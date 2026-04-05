from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import List, Optional
import os
from app.models import Conversation, MessageDB, Message

class DatabaseService:
    def __init__(self):
        database_url = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/rag_chatbot")
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def get_db(self) -> Session:
        db = self.SessionLocal()
        try:
            return db
        finally:
            db.close()

    def create_conversation(self, session_id: str) -> Conversation:
        db = self.get_db()
        try:
            conversation = Conversation(session_id=session_id)
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
            return conversation
        finally:
            db.close()

    def get_conversation(self, session_id: str) -> Optional[Conversation]:
        db = self.get_db()
        try:
            return db.query(Conversation).filter(Conversation.session_id == session_id).first()
        finally:
            db.close()

    def add_message(self, conversation_id: int, role: str, content: str) -> MessageDB:
        db = self.get_db()
        try:
            message = MessageDB(conversation_id=conversation_id, role=role, content=content)
            db.add(message)
            db.commit()
            db.refresh(message)
            return message
        finally:
            db.close()

    def get_conversation_history(self, session_id: str) -> List[Message]:
        db = self.get_db()
        try:
            conversation = db.query(Conversation).filter(Conversation.session_id == session_id).first()
            if not conversation:
                return []

            messages = db.query(MessageDB).filter(MessageDB.conversation_id == conversation.id).order_by(MessageDB.created_at).all()
            return [Message(role=msg.role, content=msg.content) for msg in messages]
        finally:
            db.close()

    def save_message_to_conversation(self, session_id: str, role: str, content: str) -> None:
        db = self.get_db()
        try:
            conversation = db.query(Conversation).filter(Conversation.session_id == session_id).first()
            if not conversation:
                conversation = Conversation(session_id=session_id)
                db.add(conversation)
                db.commit()
                db.refresh(conversation)

            message = MessageDB(conversation_id=conversation.id, role=role, content=content)
            db.add(message)
            db.commit()
        finally:
            db.close()

# Global instance
db_service = DatabaseService()