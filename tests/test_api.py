"""Endpoint tests with the OpenAI client and the database replaced by fakes."""

import pytest
from fastapi.testclient import TestClient

from app import main
from app.schemas import Message

FAKE_CHUNKS = [
    {"text": "## Plano Basic\naté 5 usuários", "embedding": [1.0, 0.0]},
    {"text": "## Suporte\nhorário comercial", "embedding": [0.0, 1.0]},
]


class FakeDatabase:
    def __init__(self):
        self.messages: dict[str, list[Message]] = {}

    def get_conversation_history(self, session_id):
        return list(self.messages.get(session_id, []))

    def save_message_to_conversation(self, session_id, role, content):
        self.messages.setdefault(session_id, []).append(Message(role=role, content=content))


@pytest.fixture
def client(monkeypatch):
    fake_db = FakeDatabase()
    monkeypatch.setattr(main, "load_or_create_chunk_embeddings", lambda **kwargs: FAKE_CHUNKS)
    monkeypatch.setattr(main, "db_service", fake_db)
    monkeypatch.setattr("app.services.rag_service.generate_embedding", lambda text: [1.0, 0.0])
    monkeypatch.setattr(
        main, "ask_llm", lambda question, context, system_prompt, history: f"answer to {question}"
    )
    with TestClient(main.app) as test_client:
        test_client.fake_db = fake_db
        yield test_client


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_ask_returns_answer_sources_and_session(client):
    response = client.post("/ask", json={"question": "Quantos usuários?"})
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "answer to Quantos usuários?"
    assert body["sources"][0]["text_preview"].startswith("## Plano Basic")
    assert body["sources"][0]["score"] == 1.0
    assert body["session_id"]


def test_ask_stores_both_messages_and_history_is_returned(client):
    session_id = client.post("/ask", json={"question": "Q1"}).json()["session_id"]
    history = client.get(f"/conversations/{session_id}").json()
    assert history["session_id"] == session_id
    assert [m["role"] for m in history["messages"]] == ["user", "assistant"]
    assert history["messages"][0]["content"] == "Q1"


def test_ask_rejects_missing_question(client):
    assert client.post("/ask", json={}).status_code == 422
