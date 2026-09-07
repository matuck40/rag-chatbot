A retrieval-augmented generation API: a FastAPI service that splits a Markdown knowledge base into sections, embeds them with the OpenAI embeddings API, ranks them in memory by dot-product similarity, answers questions with `gpt-4o-mini` grounded on the three best-matching chunks, and stores each conversation in PostgreSQL.

## Architecture

```
client
  |  POST /ask {question, session_id?, history?}
  v
app/main.py  (FastAPI: GET /health, POST /ask, GET /conversations/{session_id})
  |
  |-- startup: data/knowledge_base.txt
  |            -> app/knowledge.py      chunk_by_sections()  (split on "# " / "## " headings)
  |            -> app/embedding.py      OpenAI text-embedding-3-small, one call per chunk
  |            -> data/chunk_embeddings.json  (cache, reused while the file's mtime is
  |                                            unchanged, git-ignored)
  |
  |-- app/services/rag_service.py     embed the question, dot product against every cached
  |                                    chunk, keep the top 3 as context + "sources"
  |-- app/llm.py                       OpenAI chat completion (gpt-4o-mini):
  |                                    system prompt + context + prior turns + question
  |-- app/services/database_service.py SQLAlchemy engine from DATABASE_URL,
  |                                    reads/writes conversations and messages
  v
PostgreSQL  (tables: conversations, messages; schema in alembic/versions/001_*.py)
```

Components, by file:

- `app/main.py`: builds the FastAPI app and, at import time, loads and embeds the knowledge base. `POST /ask` takes a `question`, an optional `session_id` (a UUID4 is generated if absent) and an optional `history` list. If `history` is not sent, prior messages for that session are loaded from the database. After the LLM answers, the user message and the assistant message are saved. `GET /conversations/{session_id}` returns the stored messages. `GET /health` returns `{"status": "ok"}`.
- `app/knowledge.py`: `load_system_prompt` reads `prompts/system_prompt.txt`; `chunk_by_sections` starts a new chunk at every line beginning with `# ` or `## ` (`### ` headings stay inside their parent chunk). The sample knowledge base yields 14 chunks. `load_knowledge_base` and `chunk_text` in the same file are not called anywhere.
- `app/embedding.py`: reads `data/knowledge_base.txt`, calls `text-embedding-3-small`, computes the dot product in plain Python, and caches chunk embeddings in `data/chunk_embeddings.json`. The cache is reused only if the knowledge file's modification time is unchanged; a change to the chunking function alone does not invalidate it.
- `app/services/rag_service.py`: retrieval. Returns the concatenated top-3 chunks as context and a `sources` list with each chunk's score and its first 200 characters.
- `app/llm.py`: sends two system messages (the prompt file, then `Contexto:\n<chunks>`), then the history turns, then the question, to `gpt-4o-mini`.
- `app/models.py`: the Pydantic request models (`QuestionRequest`, `Message`) and the SQLAlchemy ORM models (`Conversation`, `MessageDB`) live in the same file.
- `app/services/database_service.py`: `DatabaseService`, a module-level singleton created at import. It opens a session per operation. The API uses two of its methods, `save_message_to_conversation` and `get_conversation_history`; `create_conversation`, `get_conversation` and `add_message` are defined but not called.
- `alembic/`, `alembic.ini`: one migration (`001`) creating `conversations` and `messages`. `alembic/env.py` reads the connection string from `alembic.ini`, not from `.env`.
- `init_db.py`: alternative to Alembic; runs `Base.metadata.create_all` with `DATABASE_URL` from `.env` and does not record a migration version.
- `prompts/system_prompt.txt`: the assistant persona (a support agent for a fictional company "Acme"), in Brazilian Portuguese, instructing the model to answer only from the supplied context.
- `data/knowledge_base.txt`: the sample knowledge base (plans, billing, support policies of "Acme"), in Portuguese, about 300 lines.

Retrieval happens in process, against the list of chunk embeddings held in memory since startup. PostgreSQL stores chat history only; there is no vector extension and no vector index.

## Example

The example below is illustrative, not captured from a live run (the app needs a valid OpenAI key even to start: the client is constructed at import, and without a cache the embeddings are generated at import). The request and response fields match the code; the answer text and scores are placeholders. The previews are the first characters of real chunks of `data/knowledge_base.txt`.

```bash
curl -s -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Quantos usuários o Plano Basic permite?"}'
```

```json
{
  "answer": "O Plano Basic permite até 5 usuários. ...",
  "sources": [
    {"score": 0.61, "text_preview": "## Usuários e limites\n\n### Limites por plano\n- Basic: até 5 usuários\n- Pro: até ..."},
    {"score": 0.55, "text_preview": "## Planos disponíveis\n\n### Plano Basic\nO Plano Basic é indicado para profissiona..."},
    {"score": 0.47, "text_preview": "## Comparação rápida entre planos\n\nResumo:\n- Basic: solução inicial para uso sim..."}
  ],
  "session_id": "8f3c2c0e-1b7e-4b2e-9a4e-2f1c3d4e5f60"
}
```

Sending the returned `session_id` in the next request continues the same conversation. `GET /conversations/<session_id>` returns `{"session_id": "...", "messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}`.

## Running locally

1. Python 3.9 or newer. No version is declared in the repository; 3.9 is the floor implied by the built-in generic type hints in the code (such as `list[float]`). Create a virtual environment and install the dependencies; versions are not pinned in `requirements.txt`.

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. PostgreSQL. The migration uses only standard column types and no extensions. Create the database:

   ```bash
   createdb rag_chatbot
   ```

3. Copy `.env.example` to `.env` and fill in both variables. `OPENAI_API_KEY` is read by the `openai` client. `DATABASE_URL` is a SQLAlchemy URL such as `postgresql://USER:PASSWORD@localhost:5432/rag_chatbot`. If `DATABASE_URL` is missing, `database_service.py` falls back to `postgresql://user:password@localhost/rag_chatbot`.

4. Create the tables. Alembic takes its URL from the `sqlalchemy.url` line in `alembic.ini` (a placeholder value is committed); set it to the same value as `DATABASE_URL`, then:

   ```bash
   alembic upgrade head
   ```

   `python init_db.py` creates the same tables from the ORM models using `.env` instead, without an `alembic_version` table.

5. Start the API. The first start makes one embeddings call per section of the knowledge base and writes `data/chunk_embeddings.json`; later starts reuse it until `data/knowledge_base.txt` changes.

   ```bash
   uvicorn app.main:app --reload
   ```

   `./run.sh` does the same after activating `.venv`. Interactive docs are served at `http://127.0.0.1:8000/docs`.

## What is not here

- Automated tests: there is no `tests/` directory.
- Authentication, rate limiting or CORS configuration on the endpoints.
- Deployment: no Dockerfile, container configuration or CI.
- Evaluation of answer quality or retrieval quality.
- A vector store: similarity is computed in memory over a JSON file, which is adequate for the ~300-line sample and not designed for larger corpora.
- Error handling: there is no `except` block in `app/`. If PostgreSQL or the OpenAI API is unreachable, `POST /ask` and `GET /conversations/{session_id}` return a 500. On `/ask`, the database write happens after the LLM call, so a database failure loses an answer that was already generated.
- A limit on conversation length: the full stored history of a session is replayed into every prompt.
- Access control on conversations: anyone who knows a `session_id` can read and extend that conversation.
- Configuration of model names or the number of retrieved chunks; both are hard-coded.
- Accurate in-code comments in two places: the header of `app/main.py` lists `GET /status` and `GET /chunks` endpoints that do not exist, and the docstring of `init_db.py` says it uses Alembic migrations when it calls `create_all`.

## Author

Lucca Matuck, PhD in Engineering Physics. Signal processing and instrumentation for physical measurement; also builds and operates management systems in production.
