import os
import sys

import asyncio
import types

sys.path.insert(0, os.path.abspath("src"))

# Provide a minimal stub for aiohttp used by link_checker
stub_aiohttp = types.ModuleType("aiohttp")

class _ClientSession:
    def __init__(self, *args, **kwargs):
        pass
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return False

stub_aiohttp.ClientSession = _ClientSession
stub_aiohttp.ClientTimeout = lambda total=None: None
stub_aiohttp.TCPConnector = lambda limit=None: None
stub_aiohttp.ClientError = Exception

sys.modules['aiohttp'] = stub_aiohttp

import link_checker


def test_check_urls(monkeypatch):
    async def fake_check(session, url):
        return {'url': url, 'status': 200, 'error': None}
    async def run_test():
        monkeypatch.setattr(link_checker, '_check_one', fake_check)
        urls = ['http://a.com', 'http://b.com']
        results = await link_checker.check_urls(urls)
        assert len(results) == 2
        assert all(r['status'] == 200 for r in results)
    asyncio.run(run_test())


def test_get_url_verification_summary():
    results = [
        {'url': 'http://a.com', 'status': 200},
        {'url': 'http://b.com', 'status': 404}
    ]
    summary = link_checker.get_url_verification_summary(results)
    assert summary['total_checked'] == 2
    assert summary['successful'] == 1
    assert summary['failed'] == 1
    assert summary['all_valid'] is False
    assert summary['failed_urls'][0]['url'] == 'http://b.com'
