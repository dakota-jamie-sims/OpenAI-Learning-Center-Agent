import sys
from pathlib import Path

import pytest

# Ensure project root is on the Python path for namespace package imports
sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.tools.link_checker import check_urls, get_url_verification_summary

@pytest.mark.asyncio
async def test_link_checker_basic():
    urls = ["https://example.com", "https://httpbin.org/status/404"]
    results = await check_urls(urls)
    summary = get_url_verification_summary(results)
    assert summary["total_checked"] == 2
    status_map = {r["url"]: r["status"] for r in results}
    assert status_map["https://example.com"] == 200
    assert status_map["https://httpbin.org/status/404"] == 404
