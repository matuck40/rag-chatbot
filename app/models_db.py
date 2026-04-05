"""
SQLAlchemy models for the application.

This file defines a simple ChatHistory model to store questions and answers.
It uses the `Base` from app.db so metadata and table creation are centralized.

Why added/fixed:
- The project had no SQLAlchemy models. Adding a basic model shows how to persist
  conversation history and provides a testable schema for PostgreSQL.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Text, DateTime
from app.db import Base


class ChatHistory(Base):
    """Stores a simple Q/A pair with a timestamp.

    Fields:
    - id: integer primary key
    - question: the user's question text
    - answer: the LLM's answer text
    - created_at: timestamp when the row was created
    """

    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
