"""RAG chatbot package. Loading the package reads `.env` so every module
(and Alembic's env.py) sees OPENAI_API_KEY and DATABASE_URL."""

from dotenv import load_dotenv

load_dotenv()
