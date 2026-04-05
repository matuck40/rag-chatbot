## main.py
# FastAPI app that serves as the backend for the RAG chatbot. It loads the knowledge base, creates chunks and embeddings, and provides endpoints for asking questions and checking health/status.

# The app has the following endpoints:
# - GET /health: Returns a simple health check response.
# - GET /status: Returns the status of the API and the feature being tested.
# - POST /ask: Accepts a question, generates an embedding for it, ranks the knowledge base chunks by similarity, and prints the top 3 most relevant chunks.

# Import necessary libraries and modules
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

from fastapi import FastAPI
from app.models import QuestionRequest
from app.knowledge import load_system_prompt, chunk_by_sections
from app.llm import ask_llm
from app.embedding import load_or_create_chunk_embeddings
from app.services.rag_service import get_context_from_question

# Import the DB engine and models so we can create tables at startup
# Note: these imports are minimal and won't create tables by themselves.
from app.db import engine, SessionLocal
from app.models_db import ChatHistory
from app.db import Base as DBSBase

# Initialize FastAPI app
app = FastAPI()

# Load knowledge base and create/load chunks and embeddings at import time
# (this keeps original behavior of the project)
base_path = Path(__file__).resolve().parent.parent
knowledge_path = str(base_path / "data" / "knowledge_base.txt")
cache_path = str(base_path / "data" / "chunk_embeddings.json")

chunk_embeddings = load_or_create_chunk_embeddings(
    knowledge_path=knowledge_path,
    cache_path=cache_path,
    chunking_function=chunk_by_sections,
)

# Create DB tables at startup. This is a simple approach for development.
# If using migrations (Alembic) in production, prefer migrations instead of create_all().
@app.on_event("startup")
def on_startup():
    # The Base metadata knows about ChatHistory because we imported models_db
    # Calling create_all will create missing tables in the configured database.
    DBSBase.metadata.create_all(bind=engine)


# Define API endpoints
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/status")
def status():
    return {"api": "running", "feature": "basic-rag"}


@app.get("/db-health")
def db_health():
    """Simple endpoint to check DB connectivity.

    - Uses a short-lived session to run a trivial query.
    - Returns database URL summary and simple success/failure.
    """
    db = SessionLocal()
    try:
        # A minimal query to validate the connection. Using a raw SELECT 1 is fine.
        db.execute("SELECT 1")
        return {"db": "ok", "database_url": os.getenv("DATABASE_URL") or "sqlite (fallback)"}
    except Exception as e:
        # Return error details to help debugging - safe for development.
        return {"db": "error", "details": str(e)}
    finally:
        db.close()


@app.post("/ask")
def ask(req: QuestionRequest):

    # Load system prompt and get context from question
    system_prompt = load_system_prompt()

    # Get context from question using the RAG service
    context, sources = get_context_from_question(req.question, chunk_embeddings)

    # Ask the LLM for an answer based on the question, context, and system prompt
    answer = ask_llm(req.question, context, system_prompt)
    
    # NOTE: Optionally persist the Q/A pair. Disabled by default to avoid unexpected DB writes.
    # To enable saving, uncomment the block below. This shows how to use the SessionLocal safely.
    # db = SessionLocal()
    # try:
    #     chat = ChatHistory(question=req.question, answer=answer)
    #     db.add(chat)
    #     db.commit()
    # finally:
    #     db.close()

    return {
        "answer": answer,
        "sources": sources
    }