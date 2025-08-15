import os
import sys

import pytest
from unittest.mock import patch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
aiohttp = pytest.importorskip("aiohttp")
from src.link_checker import check_urls, get_url_verification_summary


class FakeResponse:
    def __init__(self, status: int):
        self.status = status

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass


class FakeClientSession:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    def head(self, url, **kwargs):
        if "good" in url:
            return FakeResponse(200)
        return FakeResponse(404)

    def get(self, url, **kwargs):
        # only called for non-200 head responses
        return FakeResponse(404)


@pytest.mark.asyncio
async def test_check_urls_and_summary():
    urls = ["https://good.com", "https://bad.com"]
    with patch("src.link_checker.aiohttp.ClientSession", FakeClientSession):
        results = await check_urls(urls)
    assert results[0]["status"] == 200
    assert results[1]["status"] == 404

    summary = get_url_verification_summary(results)
    assert summary["total_checked"] == 2
    assert summary["successful"] == 1
    assert summary["failed"] == 1
    assert summary["failed_urls"][0]["url"] == "https://bad.com"
