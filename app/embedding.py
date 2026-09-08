import json
from functools import lru_cache
from pathlib import Path

from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-small"


@lru_cache(maxsize=1)
def get_client() -> OpenAI:
    # Created on first use, so importing the app does not require an API key.
    return OpenAI()


def generate_embedding(text: str) -> list[float]:
    response = get_client().embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def dot_product(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b, strict=True))


def build_chunk_embeddings(chunks: list[str]) -> list[dict]:
    return [{"text": chunk, "embedding": generate_embedding(chunk)} for chunk in chunks]


def rank_chunks_by_similarity(
    query_embedding: list[float], chunk_embeddings: list[dict]
) -> list[dict]:
    scores = [
        {"text": item["text"], "score": dot_product(query_embedding, item["embedding"])}
        for item in chunk_embeddings
    ]
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores


def load_or_create_chunk_embeddings(
    knowledge_path: str, cache_path: str, chunking_function
) -> list[dict]:
    knowledge_file = Path(knowledge_path)
    cache_file = Path(cache_path)

    current_mtime = knowledge_file.stat().st_mtime

    if cache_file.exists():
        cache_data = json.loads(cache_file.read_text(encoding="utf-8"))
        if cache_data["last_modified"] == current_mtime:
            return cache_data["chunk_embeddings"]

    text = knowledge_file.read_text(encoding="utf-8")
    chunks = chunking_function(text)
    chunk_embeddings = build_chunk_embeddings(chunks)
    print("Generated new embeddings for chunks.")

    cache_data = {
        "last_modified": current_mtime,
        "chunks": chunks,
        "chunk_embeddings": chunk_embeddings,
    }
    cache_file.write_text(json.dumps(cache_data, ensure_ascii=False, indent=2), encoding="utf-8")

    return chunk_embeddings
