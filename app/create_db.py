import os
import sqlite3

from rich.console import Console
from rich.text import Text

from dotenv import load_dotenv


console = Console(tab_size=4)
load_dotenv()  # take dev environment variables


def create_db():
    """Create the database and tables if they don't exist"""
    TABLE_EVENTS_EXISTS = False
    TABLE_DAILY_EXISTS = False
    TABLE_MONTHLY_EXISTS = False

    # Create the sqlite database it it doesn't exist
    if os.path.exists(f"./{os.environ.get('DB_FILE')}"):
        if os.path.isfile(f"./{os.environ.get('DB_FILE')}") is not True:
            print("Could not create the database: There is a directory named the same as the database that is being created")
    else:
        print(f"Creating database: ./{os.environ.get('DB_FILE')}")

    con = sqlite3.connect(f"{os.environ.get('DB_FILE')}")

    # Create table events if it doesn't exist
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master")
    r = cur.fetchall()

    for i in r:
        if i[0] == "events":
            TABLE_EVENTS_EXISTS = True

    if TABLE_EVENTS_EXISTS == False:
        tables = """CREATE TABLE events (
            event_id INTEGER PRIMARY KEY,
            date date,
            event varchar(3),
            time varchar(5),
            comment varchar(30),
            UNIQUE(date, time)
            );"""
        cur.execute(tables)
        text = Text("Created table events")
        text.stylize("green")
        console.print(text)

    # Create table daily it it doesn't exist
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master")
    r = cur.fetchall()

    for i in r:
        if i[0] == "daily":
            TABLE_DAILY_EXISTS = True

    if TABLE_DAILY_EXISTS == False:
        tables = """CREATE TABLE daily (
            daily_id INTEGER PRIMARY KEY,
            date date UNIQUE,
            minutes int,
            ot_minutes int
            );"""
        cur.execute(tables)
        text = Text("Created table daily")
        text.stylize("green")
        console.print(text)

    # Create table monthly it it doesn't exist
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master")
    r = cur.fetchall()

    for i in r:
        if i[0] == "monthly":
            TABLE_MONTHLY_EXISTS = True

    if TABLE_MONTHLY_EXISTS == False:
        tables = """CREATE TABLE monthly (
            monthly_id INTEGER PRIMARY KEY,
            year varchar(4),
            month varchar(2),
            minutes int,
            ot_minutes int,
            worked_days int,
            UNIQUE(year, month)
            );"""
        cur.execute(tables)
        text = Text("Created table monthly")
        text.stylize("green")
        console.print(text)
