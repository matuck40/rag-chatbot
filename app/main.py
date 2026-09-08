# FastAPI app for the RAG chatbot. On startup it loads the knowledge base,
# splits it into chunks and embeds them (cached in data/chunk_embeddings.json).
#
# Endpoints:
# - GET /health: liveness check.
# - POST /ask: embeds the question, retrieves the 3 most similar chunks, asks the
#   LLM with the session history, stores both messages and returns the answer.
# - GET /conversations/{session_id}: stored messages of a session.

import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.embedding import load_or_create_chunk_embeddings
from app.knowledge import chunk_by_sections, load_system_prompt
from app.llm import ask_llm
from app.schemas import QuestionRequest
from app.services.database_service import db_service
from app.services.rag_service import get_context_from_question

BASE_PATH = Path(__file__).resolve().parent.parent
KNOWLEDGE_PATH = str(BASE_PATH / "data" / "knowledge_base.txt")
CACHE_PATH = str(BASE_PATH / "data" / "chunk_embeddings.json")


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.chunk_embeddings = load_or_create_chunk_embeddings(
        knowledge_path=KNOWLEDGE_PATH,
        cache_path=CACHE_PATH,
        chunking_function=chunk_by_sections,
    )
    yield


app = FastAPI(title="rag-chatbot", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/conversations/{session_id}")
def get_conversation_history(session_id: str):
    """Retrieve conversation history for a given session"""
    history = db_service.get_conversation_history(session_id)
    return {"session_id": session_id, "messages": [msg.model_dump() for msg in history]}


@app.post("/ask")
def ask(req: QuestionRequest):
    session_id = req.session_id or str(uuid.uuid4())

    system_prompt = load_system_prompt()

    # History from the request body, or from the database when absent or empty.
    history = req.history or db_service.get_conversation_history(session_id)

    context, sources = get_context_from_question(req.question, app.state.chunk_embeddings)

    answer = ask_llm(req.question, context, system_prompt, [msg.model_dump() for msg in history])

    db_service.save_message_to_conversation(session_id, "user", req.question)
    db_service.save_message_to_conversation(session_id, "assistant", answer)

    return {"answer": answer, "sources": sources, "session_id": session_id}
