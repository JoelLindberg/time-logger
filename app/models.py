import os
import sqlite3
from datetime import datetime, timedelta
import re


con = sqlite3.connect(f"{os.environ.get('DB_FILE')}")


def calc_worked_hours(worked_minutes: int) -> str:
    """Present daily values on the page"""
    minutes = int(worked_minutes % 60)
    hours = int((worked_minutes - minutes) / 60)

    return f"{hours}h {minutes}m"


class Event:
    def __init__(self, 
                 event_id: int | None,
                 date: str, 
                 event: str, 
                 time: str, 
                 comment: str):
        self.event_id = event_id
        self.date = date
        self.event = event
        self.time = self.validate_log_time(time)
        self.comment = comment

    def validate_log_time(self, log_time: str) -> str:
        '''Validates input and returns a date in the format 14:00.
        
        :param log_time: Accepts format "14:00".
        '''
        p = "^([0-1][0-9]|2[0-4]):[0-5][0-9]?"

        if len(log_time) == 0:
            raise AttributeError("Invalid or no time input received.")

        if re.fullmatch(p, log_time) != None:
            return log_time
        else:
            return ""

    def to_dict(self) -> dict:
        """
        Converts the Event object's attributes into a dictionary.

        Returns:
            dict: A dict representation of the Events object.
        """
        return {
            "event_id": self.event_id,
            "date": self.date,
            "event": self.event,
            "time": self.time,
            "comment": self.comment,
        }

    @classmethod
    def from_db_row(self, row: tuple):
        """
        Creates an Event object from a database row (e.g., a tuple returned by a DB API).
        Assumes the order of columns in the row matches the order of attributes
        in the constructor.

        Args:
            row (tuple): A tuple representing a row fetched from the database.

        Returns:
            Event: An Event object populated with data from the database row.
        """
        # Basic validation: ensure the row has enough elements
        if len(row) != 5:
            raise ValueError("Database row does not have the expected number of columns for User.")
        return self(event_id=row[0], 
                   date=row[1], 
                   event=row[2], 
                   time=row[3], 
                   comment=row[4])


class Daily:
    def __init__(self,
                 daily_id: int | None,
                 date: str,
                 minutes: int,
                 ot_minutes: int):
        self.daily_id = daily_id
        self.date = date
        self.minutes = minutes
        self.ot_minutes = ot_minutes
        self.worked_hours = calc_worked_hours(self.minutes) # not from DB, computed
        self.worked_ot_hours = calc_worked_hours(self.ot_minutes) # not from DB, computed
        self.daily_balance = self.daily_balance(self.minutes) # not from DB, computed

    def to_dict(self) -> dict:
        return {
            "daily_id": self.daily_id,
            "date": self.date,
            "minutes": self.minutes,
            "ot_minutes": self.ot_minutes,
            "worked_hours": self.worked_hours,
            "worked_ot_hours": self.worked_ot_hours,
            "daily_balance": self.daily_balance
        }

    def daily_balance(self, worked_minutes: int) -> str:
        """Present balance on the page"""
        # 8h work expected = 480 minutes
        daily_balance = (worked_minutes - 480)

        if daily_balance < 0:
            minutes = daily_balance % 60
            hours = int((daily_balance - minutes) / 60)
            -abs(minutes) # convert the number to negative
            -abs(hours) # convert the number to negative
            return f"{hours}h {minutes}m"
        else:
            minutes = daily_balance % 60
            hours = int((daily_balance - minutes) / 60)
            return f"{hours}h {minutes}m"

    def sum_timedeltas(self, d_timedelta: timedelta) -> timedelta:
        """Addition of timedelta results. Return a single object with the time diffs combined."""
        d_sum = timedelta(seconds=0)
        for d in d_timedelta:
            d_sum = d + d_sum

        return d_sum

    def calc_in_out(self, events: list) -> int | None:
        # calculate/create diffs (timedeltas) between in and out log events
        dates = []
        d_timedelta = []
        previous_event = ""
        idx = 0
        incorrect_order = False
        for i in events:
            dates.append(datetime.fromisoformat(f'{str(i.date)}T{i.time}'))

            if i.event == "out" and previous_event == "in":
                d_timedelta.append(dates[idx] - dates[idx - 1])
                previous_event = "out"
            elif i.event == "in" and previous_event == "in":
                print("Incorrect time log event order logged. 'in' is followed by 'in'.")
                incorrect_order = True
                #raise ValueError("Incorrect time log event order logged. 'in' is followed by 'in'.")
            elif i.event == "out" and previous_event == "out":
                print("Incorrect time log event order logged. 'out' is followed by 'out'.")
                incorrect_order = True
                #raise ValueError("Incorrect time log event order logged. 'out' is followed by 'out'.")
            elif i.event == "in":
                previous_event = "in"
            idx += 1

        # sum the diffs
        d_sum = self.sum_timedeltas(self, d_timedelta)

        # calculate net minutes
        # update daily with minutes for the current day
        net_minutes = d_sum.seconds / 60 # add this value to the DB DAILY

        if incorrect_order == True:
            return None
        else:
            return net_minutes

    def calc_otin_otout(self, events: list) -> int | None:
        # calculate/create diffs (timedeltas) between in and out log events
        dates = []
        d_timedelta = []
        previous_event = ""
        idx = 0
        incorrect_order = False
        for i in events:
            dates.append(datetime.fromisoformat(f'{str(i.date)}T{i.time}'))

            if i.event == "ot-out" and previous_event == "ot-in":
                d_timedelta.append(dates[idx] - dates[idx - 1])
                previous_event = "ot-out"
            elif i.event == "ot-in" and previous_event == "ot-in":
                print("Incorrect time log event order logged. 'ot-in' is followed by 'ot-in'.")
                incorrect_order = True
                #raise ValueError("Incorrect time log event order logged. 'ot-in' is followed by 'ot-in'.")
            elif i.event == "ot-out" and previous_event == "ot-out":
                print("Incorrect time log event order logged. 'ot-out' is followed by 'ot-out'.")
                incorrect_order = True
                #raise ValueError("Incorrect time log event order logged. 'ot-out' is followed by 'ot-out'.")
            elif i.event == "ot-in":
                previous_event = "ot-in"
            idx += 1

        # sum the diffs
        d_sum = self.sum_timedeltas(self, d_timedelta)

        # calculate net minutes
        # update daily with minutes for the current day
        net_ot_minutes = d_sum.seconds / 60 # add this value to the DB DAILY

        if incorrect_order == True:
            return None
        else:
            return net_ot_minutes

    @classmethod
    def from_db_row(self, row: tuple):
        if len(row) != 4:
            raise ValueError("Database row does not have the expected number of columns for Daily.")
        return self(daily_id=row[0], 
                   date=row[1], 
                   minutes=row[2], 
                   ot_minutes=row[3])

    @classmethod
    def update_daily(self, selected_date: str):
        # get the current date logged times from events
        current_events = ("""SELECT event_id,
            date,
            event,
            time,
            comment FROM events WHERE date=? ORDER BY date DESC, time ASC;""")
        cur = con.cursor()
        cur.execute(current_events, (selected_date,))
        r = cur.fetchall()
        events = []
        for row in r:
            events.append(Event.from_db_row(row))
        
        net_minutes = self.calc_in_out(self, events=events)
        net_ot_minutes = self.calc_otin_otout(self, events=events)

        # Update DAILY if the event order is correct and complete
        if net_minutes != None:
            update_query = ("UPDATE daily SET minutes=? WHERE date=?;")
            cur = con.cursor()
            cur.execute(update_query, (net_minutes, selected_date))
            con.commit()
        else:
            print("Updating nothing in DAILY")
        
        if net_ot_minutes != None:
            update_query = ("UPDATE daily SET ot_minutes=? WHERE date=?;")
            cur = con.cursor()
            cur.execute(update_query, (net_ot_minutes, selected_date))
            con.commit()
        else:
            print("Updating nothing in DAILY for OT minutes")

    @classmethod
    def delete_daily(self, selected_date: str):
        """Deletes from DAILY table based on selected_date from the main page."""
        cur = con.cursor()
        cur.execute(f"DELETE FROM {os.environ.get("TABLE_DAILY")} WHERE date='{selected_date}';")
        con.commit()


class Monthly:
    def __init__(self,
                 monthly_id: int | None,
                 year: str,
                 month: str,
                 minutes: int,
                 ot_minutes: int,
                 worked_days: int):
        self.monthly_id = monthly_id
        self.year = year
        self.month = month
        self.minutes = minutes
        self.ot_minutes = ot_minutes
        self.worked_days = worked_days
        self.worked_hours = calc_worked_hours(self.minutes) # not from DB, computed
        self.worked_ot_hours = calc_worked_hours(self.ot_minutes) # not from DB, computed
        self.monthly_balance = self.monthly_balance(self.minutes, self.worked_days)  # not from DB, computed

    def to_dict(self) -> dict:
        return {
            "monthly_id": self.monthly_id,
            "year": self.year,
            "month": self.month,
            "minutes": self.minutes,
            "ot_minutes": self.ot_minutes,
            "worked_days": self.worked_days,
            "worked_hours": self.worked_hours,
            "worked_ot_hours": self.worked_ot_hours,
            "monthly_balance": self.monthly_balance
        }

    def monthly_balance(self, worked_minutes: int, worked_days: int) -> str:
        # worked hours
        #worked_hours = (worked_minutes / 60)
        expected_minutes = worked_days * 8 * 60
        monthly_balance = worked_minutes - expected_minutes

        if monthly_balance < 0:
            minutes = monthly_balance % 60
            hours = int((abs(monthly_balance) - minutes) / 60)
            minutes = -abs(minutes)
            hours = -abs(hours)

            return f"{hours}h {minutes}m"
        else:
            minutes = monthly_balance % 60
            hours = int((monthly_balance - minutes) / 60)

            return f"{hours}h {minutes}m"

    @classmethod
    def from_db_row(cls, row: tuple):
        if len(row) != 6:
            raise ValueError("Database row does not have the expected number of columns for Monthly.")
        return cls(monthly_id=row[0], 
                   year=row[1], 
                   month=row[2], 
                   minutes=row[3],
                   ot_minutes=row[4],
                   worked_days=row[5])

    @classmethod
    def update_monthly(self, selected_date: str):
        year_month = selected_date[:-3]
        month = selected_date[5:-3]
        year = selected_date[:-6]

        # get the sum (minutes) for the month
        daily = ("SELECT SUM(minutes) FROM daily WHERE minutes>0 AND date like ?;")
        cur = con.cursor()
        cur.execute(daily, (f"{year_month}%",))
        minutes = cur.fetchall()[0][0]

        # get the sum (minutes) for the month
        daily = ("SELECT SUM(ot_minutes) FROM daily WHERE ot_minutes>0 AND date like ?;")
        cur = con.cursor()
        cur.execute(daily, (f"{year_month}%",))
        ot_minutes = cur.fetchall()[0][0]

        if minutes == None:
            minutes = 0

        if ot_minutes == None:
            ot_minutes = 0

        daily = ("SELECT COUNT(minutes) FROM daily WHERE minutes>0 AND date like ?;")
        cur = con.cursor()
        cur.execute(daily, (f"{year_month}%",))
        r = cur.fetchall()
        worked_days = r[0][0]

        insert_monthly = ("INSERT OR REPLACE INTO monthly ("
            "year,"
            "month,"
            "minutes,"
            "ot_minutes,"
            "worked_days) VALUES (?,?,?,?,?);")
        cur = con.cursor()
        cur.execute(insert_monthly, (year, month, minutes, ot_minutes, worked_days))
        con.commit()
