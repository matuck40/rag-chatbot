## main.py
# FastAPI app that serves as the backend for the RAG chatbot. It loads the knowledge base, creates chunks and embeddings, and provides endpoints for asking questions and checking health/status.

# The app has the following endpoints:
# - GET /health: Returns a simple health check response.
# - GET /status: Returns the status of the API and the feature being tested.
# - POST /ask: Accepts a question, generates an embedding for it, ranks the knowledge base chunks by similarity, and prints the top 3 most relevant chunks.
# - GET /chunks: Loads the knowledge base, creates chunks and embeddings, and prints their counts for debugging purposes.

# Import necessary libraries and modules
from pathlib import Path
import logging
from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI
from sqlalchemy import desc, select
from app.models import QuestionRequest
from app.knowledge import load_system_prompt, chunk_by_sections
from app.llm import ask_llm
from app.embedding import load_or_create_chunk_embeddings
from app.services.rag_service import get_context_from_question
from app.database import Base, engine, get_db
from app.db_models import ChatInteraction
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

# Initialize FastAPI app
app = FastAPI()
logger = logging.getLogger(__name__)
HISTORY_LIMIT = 5

# Load knowledge base and create/load chunks and embeddings at startup
base_path = Path(__file__).resolve().parent.parent
knowledge_path = str(base_path / "data" / "knowledge_base.txt")
cache_path = str(base_path / "data" / "chunk_embeddings.json")

chunk_embeddings = load_or_create_chunk_embeddings(
    knowledge_path=knowledge_path,
    cache_path=cache_path,
    chunking_function=chunk_by_sections,
)


@app.on_event("startup")
def startup() -> None:
    # Importing the ORM model above registers it with Base.metadata.
    # create_all then creates the chat_interactions table the first time the app starts.
    # If PostgreSQL is not running, we log the problem and keep the API alive.
    if engine is None:
        logger.warning("PostgreSQL is disabled, so chat history will not be stored.")
        app.state.db_available = False
        return

    try:
        Base.metadata.create_all(bind=engine)
        app.state.db_available = True
    except OperationalError as exc:
        logger.warning("PostgreSQL is unavailable at startup: %s", exc)
        app.state.db_available = False

# Define API endpoints
@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/status")
def status():
    return {"api": "running", "feature": "basic-rag"}


def load_recent_history(db: Session) -> list[dict[str, str]]:
    # We load a small number of previous exchanges so the prompt stays readable and cheap.
    rows = db.execute(
        select(ChatInteraction).order_by(desc(ChatInteraction.id)).limit(HISTORY_LIMIT)
    ).scalars().all()
    rows.reverse()

    history: list[dict[str, str]] = []
    for row in rows:
        history.append(
            {
                "question": row.question,
                "answer": row.answer,
            }
        )

    return history


def history_to_messages(history: list[dict[str, str]]) -> list[dict[str, str]]:
    # OpenAI chat messages need alternating user/assistant turns, so we expand each saved record.
    messages: list[dict[str, str]] = []
    for item in history:
        messages.append({"role": "user", "content": item["question"]})
        messages.append({"role": "assistant", "content": item["answer"]})
    return messages


@app.post("/ask")
def ask(req: QuestionRequest, db: Session | None = Depends(get_db)):

    # Load system prompt and get context from question
    system_prompt = load_system_prompt()

    # Get context from question using the RAG service
    context, sources = get_context_from_question(req.question, chunk_embeddings)

    # When PostgreSQL is online, we load a few recent rows and feed them back into the LLM.
    history: list[dict[str, str]] = []
    history_available = db is not None and getattr(app.state, "db_available", False)
    if history_available:
        history = load_recent_history(db)

    # Ask the LLM for an answer based on the question, context, and system prompt
    answer = ask_llm(
        req.question,
        context,
        system_prompt,
        history_messages=history_to_messages(history),
    )

    if db is not None and getattr(app.state, "db_available", False):
        # Save the interaction so PostgreSQL is part of the request flow when the database is reachable.
        chat_interaction = ChatInteraction(question=req.question, answer=answer)
        db.add(chat_interaction)
        db.commit()
    else:
        logger.warning("Skipping PostgreSQL write because the database is unavailable.")

    return {
        "answer": answer,
        "sources": sources,
        "historic": history,
        "history_used": bool(history),
        "history_available": history_available,
        "history_limit": HISTORY_LIMIT,
    }
