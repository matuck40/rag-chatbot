from pathlib import Path


def load_knowledge_base() -> str:
    base_path = Path(__file__).resolve().parent.parent
    file_path = base_path / "data" / "knowledge_base.txt"
    return file_path.read_text(encoding="utf-8")


def load_system_prompt() -> str:
    base_path = Path(__file__).resolve().parent.parent
    file_path = base_path / "prompts" / "system_prompt.txt"
    return file_path.read_text(encoding="utf-8")


def chunk_text(text: str, chunk_size: int = 500) -> list[str]:
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start = end

    return chunks

def chunk_by_sections(text: str) -> list[str]:
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