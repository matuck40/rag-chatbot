# FastAPI app for the RAG chatbot. At import time it loads the knowledge base,
# splits it into chunks and embeds them (cached in data/chunk_embeddings.json).
#
# Endpoints:
# - GET /health: liveness check.
# - POST /ask: embeds the question, retrieves the 3 most similar chunks, asks the
#   LLM with the session history, stores both messages and returns the answer.
# - GET /conversations/{session_id}: stored messages of a session.

# Import necessary libraries and modules
from pathlib import Path
from dotenv import load_dotenv
import uuid

load_dotenv()

from fastapi import FastAPI
from app.models import QuestionRequest, Message
from app.knowledge import load_system_prompt, chunk_by_sections
from app.llm import ask_llm
from app.embedding import load_or_create_chunk_embeddings
from app.services.rag_service import get_context_from_question
from app.services.database_service import db_service

# Initialize FastAPI app
app = FastAPI()

# Load knowledge base and create/load chunks and embeddings at startup
base_path = Path(__file__).resolve().parent.parent
knowledge_path = str(base_path / "data" / "knowledge_base.txt")
cache_path = str(base_path / "data" / "chunk_embeddings.json")

chunk_embeddings = load_or_create_chunk_embeddings(
    knowledge_path=knowledge_path,
    cache_path=cache_path,
    chunking_function=chunk_by_sections,
)

# Define API endpoints
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/conversations/{session_id}")
def get_conversation_history(session_id: str):
    """Retrieve conversation history for a given session"""
    history = db_service.get_conversation_history(session_id)
    return {"session_id": session_id, "messages": [msg.dict() for msg in history]}


@app.post("/ask")
def ask(req: QuestionRequest):
    # Generate session_id if not provided
    session_id = req.session_id or str(uuid.uuid4())

    # Load system prompt and get context from question
    system_prompt = load_system_prompt()

    # Get conversation history from database if session_id exists
    history = req.history or []
    if not history and session_id:
        history = db_service.get_conversation_history(session_id)

    # Get context from question using the RAG service
    context, sources = get_context_from_question(req.question, chunk_embeddings)

    # Ask the LLM for an answer based on the question, context, system prompt, and history
    answer = ask_llm(req.question, context, system_prompt, [msg.dict() for msg in history])

    # Save user message and assistant response to database
    db_service.save_message_to_conversation(session_id, "user", req.question)
    db_service.save_message_to_conversation(session_id, "assistant", answer)

    return {
        "answer": answer,
        "sources": sources,
        "session_id": session_id
    }