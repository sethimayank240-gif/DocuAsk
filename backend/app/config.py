"""Central configuration, read from environment variables (.env supported)."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # dotenv is optional
    pass

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data"))
    RETRIEVER = os.getenv("RETRIEVER", "bm25").lower()
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "256"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
    TOP_K = int(os.getenv("TOP_K", "4"))
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
    MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024
    ALLOWED_EXTENSIONS = {"pdf", "txt"}
