from config import app
from auth_routes import auth_router
from timelogger_routes import timelogger_router


app.include_router(auth_router)
app.include_router(timelogger_router)
