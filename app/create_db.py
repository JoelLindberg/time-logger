import os
import sqlite3

from rich.console import Console
from rich.text import Text

from dotenv import load_dotenv


console = Console(tab_size=4)
load_dotenv()  # take dev environment variables


def create_db():
    TABLE_EVENTS_EXISTS = False
    TABLE_DAILY_EXISTS = False
    TABLE_MONTHLY_EXISTS = False

    # Check if database exists - otherwise create it
    # Need to create this for sqlite to check for the database file instead
    if os.path.exists(f"./{os.environ.get('DB_FILE')}"):
        if os.path.isfile(f"./{os.environ.get('DB_FILE')}") is not True:
            print("Could not create the database: There is a directory named the same as the database that is being created")
    else:
        print(f"Creating database: ./{os.environ.get('DB_FILE')}")

    con = sqlite3.connect(f"{os.environ.get('DB_FILE')}")


    # log_time exists? - otherwise create it
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master")
    r = cur.fetchall()

    for i in r:
        if i[0] == "events":
            TABLE_EVENTS_EXISTS = True
            #print(f"Table exists: {i[0]}")

    if TABLE_EVENTS_EXISTS == False:
        tables = f"""CREATE TABLE {os.environ.get('TABLE_EVENTS')} (
            log_id INTEGER PRIMARY KEY,
            logged_date date,
            event_type varchar(3),
            log_time varchar(5),
            comment varchar(30),
            UNIQUE(logged_date, log_time)
            );"""
        cur.execute(tables)
        text = Text(f"Created table {os.environ.get('TABLE_EVENTS')}")
        text.stylize("green")
        console.print(text)


    # sum_time exists? - otherwise create it
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master")
    r = cur.fetchall()

    for i in r:
        if i[0] == "daily":
            TABLE_DAILY_EXISTS = True
            #print(f"Table exists: {i[0]}")

    if TABLE_DAILY_EXISTS == False:
        tables = f"""CREATE TABLE {os.environ.get('TABLE_DAILY')} (
            daily_id INTEGER PRIMARY KEY,
            date date UNIQUE,
            minutes int,
            ot_minutes int
            );"""
        cur.execute(tables)
        text = Text(f"Created table {os.environ.get('TABLE_DAILY')}")
        text.stylize("green")
        console.print(text)


    # saldo_time exists? - otherwise create it
    cur = con.cursor()
    cur.execute("SELECT name FROM sqlite_master")
    r = cur.fetchall()

    for i in r:
        if i[0] == "monthly":
            TABLE_MONTHLY_EXISTS = True
            #print(f"Table exists: {i[0]}")

    if TABLE_MONTHLY_EXISTS == False:
        tables = f"""CREATE TABLE {os.environ.get('TABLE_MONTHLY')} (
            monthly_id INTEGER PRIMARY KEY,
            year varchar(4),
            month varchar(2),
            minutes int,
            ot_minutes int,
            worked_days int,
            UNIQUE(year, month)
            );"""
        cur.execute(tables)
        text = Text(f"Created table {os.environ.get('TABLE_MONTHLY')}")
        text.stylize("green")
        console.print(text)
