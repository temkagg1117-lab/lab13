from fastapi import FastAPI

from app.database import init_db
from app.routers import tasks

app = FastAPI(
    title="Personal Task Tracker",
    description="A lightweight single-user task management API.",
    version="1.0.0",
)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


app.include_router(tasks.router)


@app.get("/", tags=["Health"])
def root() -> dict:
    return {"status": "ok", "docs": "/docs"}