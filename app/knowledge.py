from pathlib import Path


def load_knowledge_base() -> str:
    base_path = Path(__file__).resolve().parent.parent
    file_path = base_path / "data" / "knowledge_base.txt"
    return file_path.read_text(encoding="utf-8")