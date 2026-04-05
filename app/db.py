"""
Database setup using SQLAlchemy.

This module provides:
- engine: the SQLAlchemy Engine
- SessionLocal: a session factory to get DB sessions
- Base: declarative base for models

Behavior:
- Reads DATABASE_URL from environment. If not provided, falls back to a local sqlite file
  so the app keeps working for development without requiring PostgreSQL.

Why added/fixed:
- The project had no DB configuration. Attempts to use PostgreSQL previously failed
  because there was no centralized engine/session setup and required packages were missing.
- This file implements a minimal, correct setup and documents the fallback behavior.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Read DATABASE_URL from env. Common env var name is DATABASE_URL.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # If DATABASE_URL is not set, default to a local sqlite file inside ./data
    # This makes it easy to run the app without Postgres during development.
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    DATABASE_URL = f"sqlite:///{data_dir / 'app.db'}"

# For sqlite, we must pass connect_args to allow usage from multiple threads.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# Create the SQLAlchemy engine. `future=True` opts in to SQLAlchemy 2.0 style APIs.
# echo is False so normal logs don't get noisy; change to True for debug.
engine = create_engine(DATABASE_URL, echo=False, future=True, connect_args=connect_args)

# Create a configured "SessionLocal" class
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

# Base class for declarative models
Base = declarative_base()

# Helpful comment for beginners:
# - Use `SessionLocal()` to get a session in request handlers (and close it when done)
# - Use `Base.metadata.create_all(bind=engine)` to create tables (we call this at app startup)
