# time-logger

To keep track of your working hours


**Goals:**

1. Make it work: fastapi + jinja2
2. Containerize it to allow anyone to test it easily


*I will initially not care about sanitizing data. The primary goal is to make things work. Second step is to find a decent way to make sure we protect ourselves against SQL injection.*


## Development

Using python-dotenv for setting env variables while developing: https://pypi.org/project/python-dotenv/

1. Create `.env` and populate it with:
    ~~~shell
    DB_FILE="time_logger.db"
    TABLE_EVENTS="events"
    TABLE_DAILY="daily"
    TABLE_MONTHLY="monthly"
    ~~~
2. Run fastapi app: `fastapi dev time_logger.py`

## Dependencies

* python-dotenv = variables (database table names in our case) set for development
* python-multipart = fastapi requires this to handle form data



## Study notes and lessons learned

### Lesson learned

This little exercise taught me that the data management quickly escalated in an unorganized way. It quickly became hard to keep the data structured in terms of *'view'* and database. It was not my intention to focus on this part but at the same time I understand this is probably a challenge every time building an app and that an ORM or at the very least some implementation of structured data models could be beneficial. While it would be interesting to make some implementation of my own the next time I would instead like to see what tools exist to mitigate this somewhat.


### forms

From https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Forms/Sending_and_retrieving_form_data

Observe there is both GET and POST methods for forms.

Both absolut and relative urls can be used. Relative:
~~~html
<form action="/somewhere_else">…</form>`
~~~ 


From FastAPI docs:

    "The way HTML forms (<form></form>) sends the data to the server normally uses a "special" encoding for that data, it's different from JSON."

    "Data from forms is normally encoded using the "media type" application/x-www-form-urlencoded.
    But when the form includes files, it is encoded as multipart/form-data. You'll read about handling files in the next chapter."


From https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Methods/POST

    "A form using application/x-www-form-urlencoded content encoding (the default) sends a request where the body contains the form data in key=value pairs, with each pair separated by an & symbol, as shown below:"

~~~
POST /test HTTP/1.1
Host: example.com
Content-Type: application/x-www-form-urlencoded
Content-Length: 27

field1=value1&field2=value2
~~~

### fastapi

redirects: https://fastapi.tiangolo.com/it/advanced/custom-response/#ujsonresponse

We must use status code 303 instead of 307 after a POST when redirecting. Otherwise the browser will try to redirect using POST. With 303 it will redirect with GET instead.

https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status/303

    "This response code is often sent back as a result of PUT or POST methods so the client may retrieve a confirmation, or view a representation of a real-world object"
