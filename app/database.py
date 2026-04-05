from __future__ import annotations

import logging
import os
from collections.abc import Generator
from typing import cast

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

load_dotenv()

logger = logging.getLogger(__name__)


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # The app can still boot without PostgreSQL, but database writes will be disabled.
    logger.warning("DATABASE_URL is missing; PostgreSQL persistence will be skipped.")
    engine = None
    SessionLocal = None
else:
    # Some hosting providers still emit the older postgres:// scheme.
    # SQLAlchemy expects postgresql://, so we normalize the URL before building the engine.
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    # The engine is created once and reused so PostgreSQL connections are pooled correctly.
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

    # SessionLocal gives each request its own database session and keeps commit/close handling explicit.
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class shared by all SQLAlchemy models in this project."""


def get_db() -> Generator[Session | None, None, None]:
    """Provide one session per request and always close it afterward."""
    if SessionLocal is None:
        yield None
        return

    db = cast(Session, SessionLocal())
    try:
        yield db
    finally:
        db.close()
