# time-logger
To keep track of working hours


Goals:

1. Make it work: fastapi + jinja2
2. Containerize it to allow anyone to test it easily



## Development

Using python-dotenv for setting env variables while developing: https://pypi.org/project/python-dotenv/

1. Create `.env` and populate it with:
    ~~~shell
    TABLE_EVENTS="events"
    TABLE_DAILY="daily"
    TABLE_MONTHLY="monthly"
    ~~~
2. Run fastapi app: `fastapi dev time_logger.py`

