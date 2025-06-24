import sqlite3
from datetime import datetime
from datetime import timedelta

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles


load_dotenv()  # take environment variables
app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None) # disable auto docs
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "message": "Hello from FastAPI & Jinja2!"})

