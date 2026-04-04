from pydantic import BaseModel
from typing import List, Dict


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class QuestionRequest(BaseModel):
    question: str
    history: List[Message] = []