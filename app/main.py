from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from app.models import QuestionRequest
from app.knowledge import load_knowledge_base
from app.llm import ask_llm

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/status")
def status():
    return {"api": "running", "feature": "basic-rag"}


@app.post("/ask")
def ask(req: QuestionRequest):
    context = load_knowledge_base()
    answer = ask_llm(req.question, context)
    return {"answer": answer}