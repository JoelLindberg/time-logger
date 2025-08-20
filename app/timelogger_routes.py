from datetime import datetime, date
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import FileResponse, RedirectResponse

from app import models
from app.config import templates
from app.config import db_con as con
from app.auth_dependencies import protected_endpoint


timelogger_router = APIRouter()


@timelogger_router.get(path="/", name="index")
async def root(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
        })


@timelogger_router.get(path="/manage", dependencies=[Depends(protected_endpoint)], name="manage")
async def manage(request: Request, selected_date: str = ""):
    if selected_date == "":
        selected_date = datetime.today().strftime('%Y-%m-%d')

    get_events = """SELECT event_id,
        date,
        event,
        time,
        comment
        FROM events
        WHERE date = ?
        ORDER BY date DESC, time ASC;"""
    cur = con.cursor()
    cur.execute(get_events, (selected_date,))
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
        "manage.html",
        {
            "request": request,
            "date": selected_date,
            "events": events,
            "daily":  daily,
            "monthly": monthly,
            "month_full": date(1999, int(selected_date[5:-3]), 1).strftime("%B")
        })


@timelogger_router.post("/add/", dependencies=[Depends(protected_endpoint)])
async def add(selected_date: Annotated[str, Form()],
              event: Annotated[str, Form()],
              time: Annotated[str, Form()],
              comment: Annotated[str, Form()]):

    try:
        event_to_add = models.Event(event_id=None,
                                    date=selected_date,
                                    event=event,
                                    time=time,
                                    comment=comment)
    except ValueError as err:
        print(f"Error: {err}")
        return RedirectResponse(f"/manage/?selected_date={selected_date}", status_code=303)

    add_event = ("""INSERT INTO events (
        date,
        event,
        time,
        comment) VALUES (?,?,?,?);""")
    cur = con.cursor()
    cur.execute(add_event, (event_to_add.date, event_to_add.event, event_to_add.time, event_to_add.comment))
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

    return RedirectResponse(f"/manage/?selected_date={selected_date}", status_code=303)


@timelogger_router.get("/delete/", dependencies=[Depends(protected_endpoint)])
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

    return RedirectResponse(f"/manage/?selected_date={selected_date}", status_code=303)


@timelogger_router.post("/update/", dependencies=[Depends(protected_endpoint)])
async def update(selected_date: Annotated[str, Form()],
                 event: Annotated[list, Form()],
                 time: Annotated[list, Form()],
                 comment: Annotated[list, Form()]):
    # Get the current date's events from the DB
    get_events = ("""SELECT event_id,
        date,
        event,
        time,
        comment FROM events WHERE date=? ORDER BY date DESC, time ASC;""")
    cur = con.cursor()
    cur.execute(get_events, (selected_date,))
    r = cur.fetchall()
    events = []
    for row in r:
        events.append(models.Event.from_db_row(row))

    # Compare the data from the DB with the POST data to only update when needed
    i = 0
    for e in events:
        try:
            upd_e = models.Event(event_id=None,
                                 date=selected_date[i],
                                 event=event[i],
                                 time=time[i],
                                 comment=comment[i])
        except ValueError as err:
            print(f"Error: {err}")
            return RedirectResponse(f"/manage/?selected_date={selected_date}", status_code=303)

        changed = False
        if upd_e.event != e.event:
            changed = True
        elif upd_e.time != e.time:
            changed = True
        elif upd_e.comment != e.comment:
            changed = True

        if changed == True:
            update_query = ("""UPDATE events
                SET event=?,
                time=?,
                comment=?
                WHERE event_id=?;""")
            cur = con.cursor()
            cur.execute(update_query, (upd_e.event, upd_e.time, upd_e.comment, e.event_id))
            con.commit()
        i += 1

    models.Daily.update_daily(selected_date)
    models.Monthly.update_monthly(selected_date)

    return RedirectResponse(f"/manage/?selected_date={selected_date}", status_code=303)


@timelogger_router.get("/favicon.png", include_in_schema=False, dependencies=[Depends(protected_endpoint)])
async def favicon():
    return FileResponse("static/favicon.png")
