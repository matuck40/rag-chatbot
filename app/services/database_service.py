import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Conversation, MessageDB
from app.schemas import Message

DEFAULT_DATABASE_URL = "postgresql://user:password@localhost/rag_chatbot"


class DatabaseService:
    def __init__(self):
        database_url = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_conversation_history(self, session_id: str) -> list[Message]:
        with self.SessionLocal() as db:
            conversation = (
                db.query(Conversation).filter(Conversation.session_id == session_id).first()
            )
            if not conversation:
                return []

            rows = (
                db.query(MessageDB)
                .filter(MessageDB.conversation_id == conversation.id)
                .order_by(MessageDB.created_at)
                .all()
            )
            return [Message(role=row.role, content=row.content) for row in rows]

    def save_message_to_conversation(self, session_id: str, role: str, content: str) -> None:
        with self.SessionLocal() as db:
            conversation = (
                db.query(Conversation).filter(Conversation.session_id == session_id).first()
            )
            if not conversation:
                conversation = Conversation(session_id=session_id)
                db.add(conversation)
                db.commit()
                db.refresh(conversation)

            db.add(MessageDB(conversation_id=conversation.id, role=role, content=content))
            db.commit()


# Global instance; the engine only connects on first use.
db_service = DatabaseService()
