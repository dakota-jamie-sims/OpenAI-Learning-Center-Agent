"""Web Search Service with simple caching."""
from typing import List, Dict, Any

from src.config import CACHE_SIZE, CACHE_TTL
from src.utils.cache import Cache

# Global cache for web search results
web_cache = Cache(maxsize=CACHE_SIZE, ttl=CACHE_TTL)

def _search_web_impl(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Actual web search implementation placeholder."""
    return [{
        "title": "Web Search Not Implemented",
        "snippet": f"Web search for '{query}' would be performed here. Please rely on knowledge base content for now.",
        "url": "#",
        "source": "placeholder",
    }]

def search_web(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Cached wrapper around web search implementation."""
    key = (query, max_results)
    cached = web_cache.get(key)
    if cached is not None:
        return cached
    result = _search_web_impl(query, max_results)
    web_cache.set(key, result)
    return result

def search_news(query: str, days_back: int = 30) -> List[Dict[str, Any]]:
    """Search for recent news articles."""
    return search_web(f"{query} news last {days_back} days")

def search_market_data(query: str) -> List[Dict[str, Any]]:
    """Search for market data and statistics."""
    return search_web(f"{query} market data statistics")
