# config.py — project_03_multi_agent
import os
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "qwen3.5:latest")
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.1"))
CREATIVE_TEMPERATURE: float = float(os.getenv("CREATIVE_TEMPERATURE", "0.7"))

MAX_REVISION_LOOPS: int = int(os.getenv("MAX_REVISION_LOOPS", "2"))
CRITIC_PASS_SCORE: int = int(os.getenv("CRITIC_PASS_SCORE", "7"))  # 0-10 scale

MAX_SEARCH_RESULTS: int = int(os.getenv("MAX_SEARCH_RESULTS", "5"))

# Supported scenarios
SCENARIO_MARKET_RESEARCH = "market_research"
SCENARIO_SOCIAL_MEDIA = "social_media"

LANGSMITH_ENABLED: bool = os.getenv("LANGSMITH_API_KEY", "") != ""
if LANGSMITH_ENABLED:
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    os.environ.setdefault("LANGCHAIN_PROJECT", "project_03_multi_agent")
