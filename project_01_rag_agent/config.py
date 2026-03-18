# config.py — project_01_rag_agent
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# ── Ollama ──────────────────────────────────────────────
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "qwen3.5:latest")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.1"))

# ── Vector Store ─────────────────────────────────────────
CHROMA_DIR: Path = Path(__file__).parent / "chroma_db"
COLLECTION_NAME: str = "rag_docs"
CHUNK_SIZE: int = 512
CHUNK_OVERLAP: int = 64
TOP_K: int = 5

# ── Retrieval ────────────────────────────────────────────
# hybrid = BM25 + vector; vector = dense only
RETRIEVAL_MODE: str = os.getenv("RETRIEVAL_MODE", "hybrid")
RERANK_ENABLED: bool = os.getenv("RERANK_ENABLED", "true").lower() == "true"

# ── LangSmith (optional) ─────────────────────────────────
LANGSMITH_ENABLED: bool = os.getenv("LANGSMITH_API_KEY", "") != ""
if LANGSMITH_ENABLED:
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_PROJECT", "project_01_rag_agent")
