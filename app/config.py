import os
import sqlite3

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

from app import create_db


load_dotenv()  # take dev environment variables


def create_templates():
    templates = Jinja2Templates(directory="templates")
    return templates


templates = create_templates()


def create_database():
    con = sqlite3.connect(os.environ.get('DB_FILE'))
    create_db.create_db()

    return con


db_con = create_database()


def create_app():
    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)  # disable auto docs
    app.mount("/static", StaticFiles(directory="static"), name="static")

    app.add_middleware(
        SessionMiddleware,
        secret_key=os.environ.get('SESSION_SECRET')
    )

    return app


app = create_app()


@app.exception_handler(404)
async def custom_404_handler(request: Request, _):
    """Display a custom 404 page instead of JSON response"""
    return templates.TemplateResponse(
        "404.html",
        {
            "request": request,
            "message": "Not Found"
        }
    )
