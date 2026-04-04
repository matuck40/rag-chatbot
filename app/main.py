## main.py
# FastAPI app that serves as the backend for the RAG chatbot. It loads the knowledge base, creates chunks and embeddings, and provides endpoints for asking questions and checking health/status.

# The app has the following endpoints:
# - GET /health: Returns a simple health check response.
# - GET /status: Returns the status of the API and the feature being tested.
# - POST /ask: Accepts a question, generates an embedding for it, ranks the knowledge base chunks by similarity, and prints the top 3 most relevant chunks.
# - GET /chunks: Loads the knowledge base, creates chunks and embeddings, and prints their counts for debugging purposes.

# Import necessary libraries and modules
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from app.models import QuestionRequest
from app.knowledge import load_system_prompt, chunk_by_sections
from app.llm import ask_llm
from app.embedding import load_or_create_chunk_embeddings
from app.services.rag_service import get_context_from_question

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


@app.get("/status")
def status():
    return {"api": "running", "feature": "basic-rag"}


@app.post("/ask")
def ask(req: QuestionRequest):

    # Load system prompt and get context from question
    system_prompt = load_system_prompt()

    # Get context from question using the RAG service
    context, sources = get_context_from_question(req.question, chunk_embeddings)

    # Ask the LLM for an answer based on the question, context, system prompt, and history
    answer = ask_llm(req.question, context, system_prompt, [msg.dict() for msg in req.history])
    
    return {
        "answer": answer,
        "sources": sources
    }