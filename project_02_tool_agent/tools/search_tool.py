# tools/search_tool.py — DuckDuckGo web search (no API key required)
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
from loguru import logger

from config import MAX_SEARCH_RESULTS

_search = DuckDuckGoSearchRun(max_results=MAX_SEARCH_RESULTS)


@tool
def web_search(query: str) -> str:
    """Search the web for current information using DuckDuckGo.
    Use this for: current events, facts, prices, news, documentation.
    Input: a search query string.
    """
    # Basic input sanitization
    query = query.strip()[:500]
    if not query:
        return "Error: empty search query"
    try:
        logger.info(f"[web_search] query={query!r}")
        result = _search.run(query)
        return result or "No results found."
    except Exception as e:
        logger.error(f"[web_search] failed: {e}")
        return f"Search failed: {e}"
