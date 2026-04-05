#!/usr/bin/env python3
"""
Database initialization script for the RAG chatbot.
This script creates the database tables using Alembic migrations.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from app.models import Base
from sqlalchemy import create_engine

def init_database():
    """Initialize the database by creating all tables."""
    database_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/rag_chatbot")

    print(f"Initializing database with URL: {database_url}")

    # Create engine
    engine = create_engine(database_url)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    print("Database tables created successfully!")

if __name__ == "__main__":
    init_database()