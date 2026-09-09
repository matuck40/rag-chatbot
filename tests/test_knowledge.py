from pathlib import Path

from app.knowledge import chunk_by_sections

SAMPLE = """# Title

## Section A
line a1

### Subsection A.1
line a1.1

## Section B
line b1
"""


def test_chunks_start_at_h1_and_h2_only():
    chunks = chunk_by_sections(SAMPLE)
    assert [c.splitlines()[0] for c in chunks] == ["# Title", "## Section A", "## Section B"]


def test_h3_stays_inside_parent_chunk():
    chunks = chunk_by_sections(SAMPLE)
    assert "### Subsection A.1" in chunks[1]


def test_empty_text_gives_no_chunks():
    assert chunk_by_sections("") == []


def test_sample_knowledge_base_has_14_chunks():
    text = (Path(__file__).resolve().parent.parent / "data" / "knowledge_base.txt").read_text(
        encoding="utf-8"
    )
    assert len(chunk_by_sections(text)) == 14
