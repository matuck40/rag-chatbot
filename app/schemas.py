from pydantic import BaseModel


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class QuestionRequest(BaseModel):
    question: str
    history: list[Message] | None = None
    session_id: str | None = None
