"""Unit tests for the web search service."""

import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# Ensure the src package is importable
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import src.services.web_search as web_search
from src.services.web_search import search_web


class MockResponse:
    """Simple mock for requests.Response used in tests."""

    def __init__(self, status_code: int, payload: Dict[str, Any]):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Dict[str, Any]:
        return self._payload

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


def test_search_web_returns_results(monkeypatch):
    """search_web should return structured results when the API succeeds."""

    def mock_post(url, headers=None, json=None, timeout=10):
        payload = {
            "organic": [
                {
                    "title": "Example Domain",
                    "snippet": "This domain is for use in illustrative examples.",
                    "link": "https://example.com",
                }
            ]
        }
        return MockResponse(200, payload)

    monkeypatch.setattr(web_search.requests, "post", mock_post)
    monkeypatch.setattr(web_search, "WEB_SEARCH_API_KEY", "test")

    results = search_web("example")
    assert len(results) == 1
    assert results[0]["title"] == "Example Domain"
    assert results[0]["url"] == "https://example.com"
    assert results[0]["source"] == "example.com"


def test_search_web_handles_rate_limit(monkeypatch):
    """search_web should handle API rate limiting gracefully."""

    def mock_post(url, headers=None, json=None, timeout=10):
        return MockResponse(429, {})

    monkeypatch.setattr(web_search.requests, "post", mock_post)
    monkeypatch.setattr(web_search, "WEB_SEARCH_API_KEY", "test")

    results = search_web("rate limit test")
    assert len(results) == 1
    assert "rate limit" in results[0]["title"].lower()
    assert results[0]["source"] == "error"


def test_search_web_without_api_key(monkeypatch):
    """search_web should warn when no API key is configured."""

    monkeypatch.setattr(web_search, "WEB_SEARCH_API_KEY", "")

    results = search_web("missing key")
    assert len(results) == 1
    assert "api key" in results[0]["title"].lower()
    assert results[0]["source"] == "error"