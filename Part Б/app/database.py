# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.task import Base

DATABASE_URL = "sqlite:///./tasks.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Create all tables. Call once on app startup."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI dependency — yields a DB session, always closes after use."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()