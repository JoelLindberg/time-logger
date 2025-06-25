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



@app.get("/")
async def read_root(request: Request):

    show_data = ("SELECT log_id,"
        "logged_date,"
        "event_type,"
        "log_time,"
        f"comment FROM {os.environ.get("TABLE_EVENTS")};")
    cur = con.cursor()
    cur.execute(show_data)
    r = cur.fetchall()

    print(r)
    # {{ item.date }} {{ item.event }} {{ item.time }} {{ item.comment }}
    logged_time = []
    for l in r:
        print(l)
        #table.add_row(str(l[0]), str(l[2]), str(l[3]), str(l[1]), str(l[4]))
        logged_time.append(
            {
                "id": l[0],
                "date": l[1],
                "event": l[2],
                "time": l[3],
                "comment": l[4]
            }
        )
    print(logged_time)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "message": "Hello from FastAPI & Jinja2!",
            "logged_time": logged_time
        })

@app.post("/add/")
async def login(event: Annotated[str, Form()], time: Annotated[str, Form()], comment: Annotated[str, Form()]):
    print(event)
    print(time)

    time_date = validate_log_time(time)

    cur = con.cursor()
    insert_query = (f"INSERT INTO {os.environ.get("TABLE_EVENTS")} ("
        "logged_date,"
        "event_type,"
        "log_time,"
        "comment) VALUES ("
        f"'{time_date[1]}',"
        "'in',"
        f"'{time_date[0]}',"
        f"\"{comment}\");")
    cur.execute(insert_query)
    con.commit()

    return RedirectResponse("/", status_code=303)

