"""Split text into overlapping fixed-size word windows."""
import re


def normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def chunk_text(text: str, size: int = 256, overlap: int = 50) -> list[str]:
    """Return word-window chunks. `overlap` words are shared between neighbours."""
    if size <= 0:
        raise ValueError("size must be positive")
    if not 0 <= overlap < size:
        raise ValueError("overlap must be >= 0 and smaller than size")
    words = normalise(text).split()
    if not words:
        return []
    step = size - overlap
    chunks = []
    for start in range(0, len(words), step):
        chunks.append(" ".join(words[start:start + size]))
        if start + size >= len(words):
            break
    return chunks
