"""Web search service using external provider.

This module integrates with a configurable web search API (e.g. Serper or
Bing) to retrieve search results. Results are normalized into a common
structure so the rest of the application can consume them easily.
"""

from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import urlparse

import requests

from src.config import WEB_SEARCH_API_KEY, WEB_SEARCH_API_ENDPOINT


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
            return results

        # No results returned from provider
        return [
            {
                "title": "No results found",
                "snippet": f"No web search results for '{query}'.",
                "url": "",
                "source": "serper",
            }
        ]

    except requests.RequestException as exc:  # Covers HTTP and network errors
        return _error_response(exc)


def search_news(query: str, days_back: int = 30) -> List[Dict[str, Any]]:
    """Search for recent news articles."""

    return search_web(f"{query} news last {days_back} days")


def search_market_data(query: str) -> List[Dict[str, Any]]:
    """Search for market data and statistics."""

    return search_web(f"{query} market data statistics")

