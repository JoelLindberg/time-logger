import os
import sqlite3
from datetime import datetime
from datetime import timedelta
from typing import Annotated
import re

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse


load_dotenv()  # take environment variables
app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None) # disable auto docs
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
con = sqlite3.connect(f"{os.environ.get('DB_FILE')}")



def validate_log_time(log_time: str) -> list:
    '''Validates input and returns a date in the format 14:00 2025-06-14.
    
    :param log_time: Accepts formats "14:00" or "14:00 2025-06-14".
    If only 14:00 is provided it will automatically append todays date in\
    the format 2025-06-14.
    '''

    time_date = []
    p1 = "^[0-9]{2}:[0-9]{2}?"
    p2 = "^[0-9]{2}:[0-9]{2} [0-9]{4}-[0-9]{2}-[0-9]{2}?"

    if re.fullmatch(p1, log_time) != None:
        time_date.append(log_time)
        time_date.append(datetime.now().strftime("%Y-%m-%d"))
    elif re.fullmatch(p2, log_time) != None:
        time_date = log_time.split()

    if len(time_date) == 0:
        raise "Something went wrong. Possibly incorrect time and date format entered."

    return time_date


def calc_in_out(events: list) -> int | None:
    # calculate/create diffs (timedeltas) between in and out log events
    dates = []
    d_timedelta = []
    previous_event = ""
    idx = 0
    incorrect_order = False
    for i in events:
        dates.append(datetime.fromisoformat(f'{str(i["date"])}T{i["log_time"]}'))

        if i["event"] == "out" and previous_event == "in":
            d_timedelta.append(dates[idx] - dates[idx - 1])
            previous_event = "out"
        elif i["event"] == "in" and previous_event == "in":
            print("Incorrect time log event order logged. 'in' is followed by 'in'.")
            incorrect_order = True
            #raise ValueError("Incorrect time log event order logged. 'in' is followed by 'in'.")
        elif i["event"] == "out" and previous_event == "out":
            print("Incorrect time log event order logged. 'out' is followed by 'out'.")
            incorrect_order = True
            #raise ValueError("Incorrect time log event order logged. 'out' is followed by 'out'.")
        elif i["event"] == "in":
            previous_event = "in"
        idx += 1

    # sum the diffs
    d_sum = sum_timedeltas(d_timedelta)

    # calculate net minutes
    # update daily with minutes for the current day
    net_minutes = d_sum.seconds / 60 # add this value to the DB DAILY

    if incorrect_order == True:
        return None
    else:
        return net_minutes

def calc_otin_otout(events: list) -> int | None:
    # calculate/create diffs (timedeltas) between in and out log events
    dates = []
    d_timedelta = []
    previous_event = ""
    idx = 0
    incorrect_order = False
    for i in events:
        dates.append(datetime.fromisoformat(f'{str(i["date"])}T{i["log_time"]}'))

        if i["event"] == "ot-out" and previous_event == "ot-in":
            d_timedelta.append(dates[idx] - dates[idx - 1])
            previous_event = "ot-out"
        elif i["event"] == "ot-in" and previous_event == "ot-in":
            print("Incorrect time log event order logged. 'ot-in' is followed by 'ot-in'.")
            incorrect_order = True
            #raise ValueError("Incorrect time log event order logged. 'ot-in' is followed by 'ot-in'.")
        elif i["event"] == "ot-out" and previous_event == "ot-out":
            print("Incorrect time log event order logged. 'ot-out' is followed by 'ot-out'.")
            incorrect_order = True
            #raise ValueError("Incorrect time log event order logged. 'ot-out' is followed by 'ot-out'.")
        elif i["event"] == "ot-in":
            previous_event = "ot-in"
        idx += 1

    # sum the diffs
    d_sum = sum_timedeltas(d_timedelta)

    # calculate net minutes
    # update daily with minutes for the current day
    net_ot_minutes = d_sum.seconds / 60 # add this value to the DB DAILY

    if incorrect_order == True:
        return None
    else:
        return net_ot_minutes


def sum_timedeltas(d_timedelta: timedelta) -> timedelta:
    """Addition of timedelta results. Return a single object with the time diffs combined."""
    d_sum = timedelta(seconds=0)
    for d in d_timedelta:
        d_sum = d + d_sum

    return d_sum

def update_daily(date):
    # get the current date logged times from events
    current_events = ("SELECT log_id,"
        "logged_date,"
        "event_type,"
        "log_time,"
        f"comment FROM {os.environ.get("TABLE_EVENTS")} "
        f"WHERE logged_date='{date}' "
        "ORDER BY "
        "logged_date DESC, log_time ASC;")
    cur = con.cursor()
    cur.execute(current_events)
    r = cur.fetchall()

    events = []
    for i in r:
        row = {}
        row["log_id"] = i[0]
        row["date"] = i[1]
        row["event"] = i[2]
        row["log_time"] = i[3]
        row["comment"] = i[4]
        events.append(row)
    
    net_minutes = calc_in_out(events)
    net_ot_minutes = calc_otin_otout(events)

    # Update DAILY if the event order is correct and complete
    if net_minutes != None:
        update_query = (f"UPDATE {os.environ.get("TABLE_DAILY")} "
            f"SET minutes='{net_minutes}' "
            f"WHERE date='{date}';")
        cur = con.cursor()
        cur.execute(update_query)
        con.commit()

        # these calcs can be used by a method presenting the daily value to the page
        minutes = (net_minutes % 60)
        hours = (net_minutes - minutes) / 60
    else:
        print("updating nothing in DAILY")
    
    if net_ot_minutes != None:
        update_query = (f"UPDATE {os.environ.get("TABLE_DAILY")} "
            f"SET ot_minutes='{net_ot_minutes}' "
            f"WHERE date='{date}';")
        cur = con.cursor()
        cur.execute(update_query)
        con.commit()
    else:
        print("updating nothing in DAILY for OT minutes")

    
def worked_hours(worked_minutes: int) -> str:
    """Present daily values on the page"""
    minutes = int(worked_minutes % 60)
    hours = int((worked_minutes - minutes) / 60)

    return f"{hours}h {minutes}m"
    

def daily_saldo(worked_minutes: int) -> str:
    """Present saldo on the page"""
    # 8h work expected = 480 minutes
    daily_saldo = (worked_minutes - 480)

    if daily_saldo < 0:
        minutes = daily_saldo % 60
        hours = int((daily_saldo - minutes) / 60)
        -abs(minutes) # convert the number to negative
        -abs(hours) # convert the number to negative
        return f"{hours}h {minutes}m"
    else:
        minutes = daily_saldo % 60
        hours = int((daily_saldo - minutes) / 60)
        return f"{hours}h {minutes}m"

def monthly_saldo(worked_minutes: int, worked_days: int) -> str:
    # worked hours
    #worked_hours = (worked_minutes / 60)
    expected_minutes = worked_days * 8 * 60
    monthly_saldo = worked_minutes - expected_minutes

    if monthly_saldo < 0:
        minutes = monthly_saldo % 60
        hours = int((monthly_saldo - minutes) / 60)
        minutes = -abs(minutes)
        hours = -abs(hours)

        return f"{hours}h {minutes}m"
    else:
        minutes = monthly_saldo % 60
        hours = int((monthly_saldo - minutes) / 60)

        return f"{hours}h {minutes}m"


def update_monthly(date: str):
    year_month = date[:-3]
    month = date[5:-3]
    year = date[:-6]

    # get the sum (minutes) for the month
    daily = ("SELECT SUM(minutes) "
        f"FROM {os.environ.get("TABLE_DAILY")} "
        f"WHERE minutes>0 AND date like '{year_month}%'"
        ";")
    cur = con.cursor()
    cur.execute(daily)
    minutes = cur.fetchall()[0][0]

    # get the sum (minutes) for the month
    daily = ("SELECT SUM(ot_minutes) "
        f"FROM {os.environ.get("TABLE_DAILY")} "
        f"WHERE ot_minutes>0 AND date like '{year_month}%'"
        ";")
    cur = con.cursor()
    cur.execute(daily)
    ot_minutes = cur.fetchall()[0][0]

    if minutes == None:
        minutes = 0

    if ot_minutes == None:
        ot_minutes = 0

    daily = ("SELECT COUNT(minutes) "
        f"FROM {os.environ.get("TABLE_DAILY")} "
        f"WHERE minutes>0 AND date like '{year_month}%'"
        ";")
    cur = con.cursor()
    cur.execute(daily)
    r = cur.fetchall()
    worked_days = r[0][0]

    insert_monthly = ("INSERT OR REPLACE INTO "
        f"{os.environ.get("TABLE_MONTHLY")} ("
        "year,"
        "month,"
        "minutes,"
        "ot_minutes,"
        "worked_days) VALUES ("
        f"'{year}',"
        f"'{month}',"
        f"'{minutes}',"
        f"'{ot_minutes}',"
        f"{worked_days});")
    cur = con.cursor()
    cur.execute(insert_monthly)
    con.commit()


def monthly_worked(date):
    # get all days from DAILY where minutes > 0 and multiply this with 480 (8h) for each day
    current_month = date[:-3]
    
    daily = ("SELECT COUNT(minutes) "
        f"FROM {os.environ.get("TABLE_DAILY")} "
        f"WHERE minutes>0 AND date like '{current_month}%'"
        ";")
    cur = con.cursor()
    cur.execute(daily)
    r = cur.fetchall()
    worked_days = r[0][0]
    
    worked_minutes = (worked_days * 480)




@app.get("/")
async def root(request: Request, date: str = ""):

    if date == "":
       date = datetime.today().strftime('%Y-%m-%d')

    show_data = ("SELECT log_id,"
        "logged_date,"
        "event_type,"
        "log_time,"
        f"comment FROM {os.environ.get("TABLE_EVENTS")} ORDER BY "
        "logged_date DESC, log_time ASC;")
    cur = con.cursor()
    cur.execute(show_data)
    r = cur.fetchall()

    events = []
    for l in r:
        events.append(
            {
                "id": l[0],
                "date": l[1],
                "event": l[2],
                "time": l[3],
                "comment": l[4]
            }
        )


    daily = ("SELECT daily_id,"
        "date,"
        "minutes,"
        "ot_minutes "
        f"FROM {os.environ.get("TABLE_DAILY")} "
        "ORDER BY date DESC;")
    cur = con.cursor()
    cur.execute(daily)
    r = cur.fetchall()

    daily = []
    for l in r:
        daily.append(
            {
                "id": l[0],
                "date": l[1],
                "minutes": l[2],
                "ot_minutes": l[3],
                "worked_hours": worked_hours(l[2]),
                "worked_ot_hours": worked_hours(l[3]),
                "daily_saldo": daily_saldo(l[2])
            }
        )
    
    get_monthly = ("SELECT monthly_id,"
        "year,"
        "month,"
        "minutes,"
        "ot_minutes,"
        "worked_days "
        f"FROM {os.environ.get("TABLE_MONTHLY")} "
        f"WHERE month='{date[5:-3]}'"
        "ORDER BY year DESC, month ASC;")
    cur = con.cursor()
    cur.execute(get_monthly)
    r = cur.fetchall()

    monthly = {
            "id": r[0][0],
            "year": r[0][1],
            "month": r[0][2],
            "minutes": r[0][3],
            "ot_minutes": r[0][4],
            "worked_days": r[0][5],
            "worked_hours": worked_hours(r[0][3]),
            "worked_ot_hours": worked_hours(r[0][4]),
            "monthly_saldo": monthly_saldo(r[0][3], r[0][5])
        }

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "date": date,
            "events": events,
            "daily":  daily,
            "monthly": monthly
        })


@app.post("/add/")
async def add(date: Annotated[str, Form()], event: Annotated[str, Form()], time: Annotated[str, Form()], comment: Annotated[str, Form()]):

    time_date = validate_log_time(time) # this method should be changed

    cur = con.cursor()
    insert_query = (f"INSERT INTO {os.environ.get("TABLE_EVENTS")} ("
        "logged_date,"
        "event_type,"
        "log_time,"
        "comment) VALUES ("
        f"'{date}',"
        f"'{event}',"
        f"'{time_date[0]}',"
        f"\"{comment}\");")
    cur.execute(insert_query)
    con.commit()

    # Also create an entry in the daily table for the daily net to be stored
    cur = con.cursor()
    select_daily = ("SELECT date "
        f"FROM {os.environ.get("TABLE_DAILY")} WHERE date='{date}';")
    cur.execute(select_daily)
    r = cur.fetchall()
    
    if len(r) == 0:
        cur = con.cursor()
        insert_daily = (f"INSERT INTO {os.environ.get("TABLE_DAILY")} ("
            "date,"
            "minutes) VALUES ("
            f"'{date}',"
            f"0);")
        cur.execute(insert_daily)
        con.commit()

    update_daily(date)
    update_monthly(date)

    return RedirectResponse(f"/?date={date}", status_code=303)


@app.get("/delete/")
async def delete(id: int, date: str):
    cur = con.cursor()
    cur.execute(f"DELETE FROM {os.environ.get("TABLE_EVENTS")} WHERE log_id = '{id}';")
    con.commit()

    return RedirectResponse(f"/?date={date}", status_code=303)









@app.post("/update/")
async def update(date: Annotated[str, Form()], event: Annotated[list, Form()], time: Annotated[list, Form()], comment: Annotated[list, Form()]):
    # Get the current date's events from the DB
    show_data = ("SELECT log_id,"
        "logged_date,"
        "event_type,"
        "log_time,"
        f"comment FROM {os.environ.get("TABLE_EVENTS")} "
        f"WHERE logged_date='{date}' "
        "ORDER BY "
        "logged_date DESC, log_time ASC;")
    cur = con.cursor()
    cur.execute(show_data)
    r = cur.fetchall()

    # Compare the dat from the DB with the POST data to only update where needed
    i = 0
    for db_event in r:
        changed = False
        if event[i] != db_event[2]:
            changed = True
        elif time[i] != db_event[3]:
            changed = True
        elif comment[i] != db_event[4]:
            changed = True

        if changed == True:
            update_query = (f"UPDATE {os.environ.get("TABLE_EVENTS")} "
                f"SET event_type='{event[i]}', "
                f"log_time='{time[i]}', "
                f"comment='{comment[i]}' "
                f"WHERE log_id='{db_event[0]}';")
            cur = con.cursor()
            cur.execute(update_query)
            con.commit()
        i += 1

    update_daily(date)
    update_monthly(date)

    return RedirectResponse(f"/?date={date}", status_code=303)
