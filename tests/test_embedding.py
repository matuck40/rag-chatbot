import json

import pytest

from app.embedding import dot_product, load_or_create_chunk_embeddings, rank_chunks_by_similarity


def test_dot_product():
    assert dot_product([1.0, 2.0, 3.0], [4.0, 5.0, 6.0]) == 32.0


def test_dot_product_rejects_length_mismatch():
    with pytest.raises(ValueError):
        dot_product([1.0], [1.0, 2.0])


def test_rank_orders_by_descending_score():
    chunks = [
        {"text": "low", "embedding": [0.0, 1.0]},
        {"text": "high", "embedding": [1.0, 0.0]},
        {"text": "mid", "embedding": [0.5, 0.5]},
    ]
    ranked = rank_chunks_by_similarity([1.0, 0.0], chunks)
    assert [r["text"] for r in ranked] == ["high", "mid", "low"]
    assert ranked[0]["score"] == 1.0


def test_cache_is_reused_when_mtime_unchanged(tmp_path, monkeypatch):
    knowledge = tmp_path / "kb.txt"
    knowledge.write_text("# A\ntext", encoding="utf-8")
    cache = tmp_path / "cache.json"
    cache.write_text(
        json.dumps(
            {
                "last_modified": knowledge.stat().st_mtime,
                "chunks": ["# A\ntext"],
                "chunk_embeddings": [{"text": "# A\ntext", "embedding": [1.0]}],
            }
        ),
        encoding="utf-8",
    )

    def fail(*args, **kwargs):
        raise AssertionError("embedding API must not be called when the cache is valid")

    monkeypatch.setattr("app.embedding.generate_embedding", fail)
    result = load_or_create_chunk_embeddings(str(knowledge), str(cache), lambda t: [t])
    assert result == [{"text": "# A\ntext", "embedding": [1.0]}]


def test_cache_is_rebuilt_when_missing(tmp_path, monkeypatch):
    knowledge = tmp_path / "kb.txt"
    knowledge.write_text("# A\ntext\n# B\nmore", encoding="utf-8")
    cache = tmp_path / "cache.json"

    monkeypatch.setattr("app.embedding.generate_embedding", lambda text: [float(len(text))])
    from app.knowledge import chunk_by_sections

    result = load_or_create_chunk_embeddings(str(knowledge), str(cache), chunk_by_sections)
    assert [r["text"] for r in result] == ["# A\ntext", "# B\nmore"]
    assert cache.exists()
    assert json.loads(cache.read_text(encoding="utf-8"))["chunks"] == ["# A\ntext", "# B\nmore"]
