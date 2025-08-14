from app.config import app
from app.auth_routes import auth_router
from app.timelogger_routes import timelogger_router


app.include_router(auth_router)
app.include_router(timelogger_router)
