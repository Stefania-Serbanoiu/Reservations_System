from fastapi import FastAPI
from db import init_db
from api.routes_users import router as users_router
from api.routes_resources import router as resources_router
from api.routes_reservations import router as reservations_router


app = FastAPI(title="Room Reservations")


@app.on_event("startup")
def _startup():
    init_db()


app.include_router(users_router, prefix="/users", tags=["users"])
app.include_router(resources_router, prefix="/resources", tags=["resources"])
app.include_router(reservations_router, prefix="", tags=["reservations"])
