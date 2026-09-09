from pathlib import Path


def load_system_prompt() -> str:
    base_path = Path(__file__).resolve().parent.parent
    file_path = base_path / "prompts" / "system_prompt.txt"
    return file_path.read_text(encoding="utf-8")


def chunk_by_sections(text: str) -> list[str]:
    """Split Markdown text into chunks, starting a new chunk at each `# ` or `## ` heading."""
    chunks = []
    current_chunk = ""

    for line in text.splitlines():
        if (line.startswith("# ") or line.startswith("## ")) and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = line
        else:
            if current_chunk:
                current_chunk += "\n" + line
            else:
                current_chunk = line

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks
