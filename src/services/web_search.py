"""Web search service using external provider.

This module integrates with a configurable web search API (e.g. Serper or
Bing) to retrieve search results. Results are normalized into a common
structure so the rest of the application can consume them easily.
"""

from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import urlparse

import requests

from src.config import WEB_SEARCH_API_KEY, WEB_SEARCH_API_ENDPOINT, CACHE_SIZE, CACHE_TTL
from src.utils.cache import Cache

# Global cache instance for web search results
_search_cache = Cache(maxsize=CACHE_SIZE, ttl=CACHE_TTL)


def _no_api_key_response(query: str) -> List[Dict[str, Any]]:
    """Return a structured response when no API key is configured."""

    return [
        {
            "title": "Web search API key not configured",
            "snippet": (
                "The WEB_SEARCH_API_KEY environment variable is missing. "
                "Set it to enable real web searches."
            ),
            "url": "",
            "source": "error",
        }
    ]


def _rate_limited_response() -> List[Dict[str, Any]]:
    """Return a structured response when the API rate limit is hit."""

    return [
        {
            "title": "Web search rate limit exceeded",
            "snippet": "The web search API rate limit has been reached. Try again later.",
            "url": "",
            "source": "error",
        }
    ]


def _error_response(error: Exception) -> List[Dict[str, Any]]:
    """Return a structured response for unexpected errors."""

    return [
        {
            "title": "Web search error",
            "snippet": str(error),
            "url": "",
            "source": "error",
        }
    ]


def search_web(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """Perform a web search using the configured provider.

    Args:
        query: The search query.
        max_results: Maximum number of results to return.

    Returns:
        List of dictionaries with keys: title, snippet, url, source.
    """

    if not WEB_SEARCH_API_KEY:
        return _no_api_key_response(query)

    # Create cache key from query and max_results
    cache_key = (query, max_results)
    
    # Check cache first
    cached_result = _search_cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    headers = {"X-API-KEY": WEB_SEARCH_API_KEY, "Content-Type": "application/json"}
    payload = {"q": query, "num": max_results}

    try:
        response = requests.post(
            WEB_SEARCH_API_ENDPOINT, headers=headers, json=payload, timeout=10
        )

        if response.status_code == 429:
            return _rate_limited_response()

        response.raise_for_status()
        data = response.json()

        results: List[Dict[str, Any]] = []
        for item in data.get("organic", [])[:max_results]:
            url = item.get("link", "")
            results.append(
                {
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "url": url,
                    "source": urlparse(url).netloc if url else "",
                }
            )

        if results:
            # Cache successful results
            _search_cache.set(cache_key, results)
            return results

        # No results returned from provider
        no_results = [
            {
                "title": "No results found",
                "snippet": f"No web search results for '{query}'.",
                "url": "",
                "source": "serper",
            }
        ]
        # Cache the no results response too
        _search_cache.set(cache_key, no_results)
        return no_results

    except requests.RequestException as exc:  # Covers HTTP and network errors
        return _error_response(exc)


def clear_search_cache() -> None:
    """Clear the web search cache."""
    _search_cache.clear()


def search_news(query: str, days_back: int = 30) -> List[Dict[str, Any]]:
    """Search for recent news articles."""

    return search_web(f"{query} news last {days_back} days")


def search_market_data(query: str) -> List[Dict[str, Any]]:
    """Search for market data and statistics."""

    return search_web(f"{query} market data statistics")