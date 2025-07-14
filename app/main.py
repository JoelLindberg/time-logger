import os
import sqlite3
from datetime import datetime, date
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

import create_db
import models


load_dotenv()  # take dev environment variables
app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None) # disable auto docs
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
con = sqlite3.connect(f"{os.environ.get('DB_FILE')}")

create_db.create_db()


@app.get("/")
async def root(request: Request, selected_date: str = ""):
    if selected_date == "":
       selected_date = datetime.today().strftime('%Y-%m-%d')

    get_events = """SELECT event_id,
        date,
        event,
        time,
        comment FROM events ORDER BY date DESC, time ASC;"""
    cur = con.cursor()
    cur.execute(get_events)
    r = cur.fetchall()
    events = []
    for row in r:
        events.append(models.Event.from_db_row(row))
    
    daily = ("""SELECT daily_id,
        date,
        minutes,
        ot_minutes FROM daily ORDER BY date DESC;""")
    cur = con.cursor()
    cur.execute(daily)
    r = cur.fetchall()
    daily = []
    for row in r:
        daily.append(models.Daily.from_db_row(row))

    monthly = models.Monthly.get_monthly(selected_date)

    if monthly == None:
        init_row = ("""INSERT INTO monthly (
            year,
            month,
            minutes,
            ot_minutes,
            worked_days) VALUES (?,?,0,0,0);""")
        cur = con.cursor()
        cur.execute(init_row, (selected_date[:-6], selected_date[5:-3]))
        con.commit()

        monthly = models.Monthly.get_monthly(selected_date)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "date": selected_date,
            "events": events,
            "daily":  daily,
            "monthly": monthly,
            "month_full": date(1999, int(selected_date[5:-3]), 1).strftime("%B")
        })


@app.post("/add/")
async def add(selected_date: Annotated[str, Form()], event: Annotated[str, Form()], time: Annotated[str, Form()], comment: Annotated[str, Form()]):
    event = models.Event(event_id = None,
                         date = selected_date,
                         event = event,
                         time = time,
                         comment = comment)
    add_event = ("""INSERT INTO events (
        date,
        event,
        time,
        comment) VALUES (?,?,?,?);""")
    cur = con.cursor()
    cur.execute(add_event, (event.date, event.event, event.time, event.comment))
    con.commit()

    # Also create an entry in the daily table for the daily net to be stored
    cur = con.cursor()
    select_daily = ("SELECT date FROM daily WHERE date=?;")
    cur.execute(select_daily, (selected_date,))
    r = cur.fetchall()

    if len(r) == 0:
        insert_daily = ("""INSERT INTO daily (
            date,
            minutes) VALUES (?, ?);""")
        cur = con.cursor()
        cur.execute(insert_daily, (selected_date, 0))
        con.commit()

    models.Daily.update_daily(selected_date)
    models.Monthly.update_monthly(selected_date)

    return RedirectResponse(f"/?selected_date={selected_date}", status_code=303)


@app.get("/delete/")
async def delete(event_id: int, selected_date: str, event: str):
    cur = con.cursor()
    cur.execute("DELETE FROM events WHERE event_id=?;", (event_id,))
    con.commit()

    # if all events for a day are deleted - update daily and monthly then cleanup daily
    select_events = ("SELECT * FROM events WHERE date=?;")
    cur = con.cursor()
    cur.execute(select_events, (selected_date,))
    r = cur.fetchall()
    events = []
    for row in r:
        events.append(models.Event.from_db_row(row))
    
    if event == "in" or event == "out":
        event_type = "normal"
    else:
        event_type = "ot"

    # Don't update Daily and Monthly tables unless there are no more events of the same type
    update = True
    for e in events:
        if (e.event == "in" or e.event == "out") and event_type == "normal":
            update = False
            break
        elif (e.event == "ot-in" or e.event == "ot-out") and event_type == "ot":
            update = False
            break

    if update == True:
        models.Daily.update_daily(selected_date)
        models.Monthly.update_monthly(selected_date)

    if len(events) == 0:
        models.Daily.delete_daily(selected_date)

    return RedirectResponse(f"/?selected_date={selected_date}", status_code=303)


@app.post("/update/")
async def update(selected_date: Annotated[str, Form()], event: Annotated[list, Form()], time: Annotated[list, Form()], comment: Annotated[list, Form()]):
    # Get the current date's events from the DB
    get_events = ("SELECT event_id,"
        "date,"
        "event,"
        "time,"
        "comment FROM events WHERE date=? ORDER BY date DESC, time ASC;")
    cur = con.cursor()
    cur.execute(get_events, (selected_date,))
    r = cur.fetchall()
    events = []
    for row in r:
        events.append(models.Event.from_db_row(row))
    # Compare the data from the DB with the POST data to only update when needed
    i = 0
    for e in events:
        changed = False
        if event[i] != e.event:
            changed = True
        elif time[i] != e.time:
            changed = True
        elif comment[i] != e.comment:
            changed = True

        if changed == True:
            update_query = ("""UPDATE events 
                SET event=?, 
                time=?, 
                comment=? 
                WHERE event_id=?;""")
            cur = con.cursor()
            cur.execute(update_query, (event[i], time[i], comment[i], e.event_id))
            con.commit()
        i += 1

    models.Daily.update_daily(selected_date)
    models.Monthly.update_monthly(selected_date)

    return RedirectResponse(f"/?selected_date={selected_date}", status_code=303)
