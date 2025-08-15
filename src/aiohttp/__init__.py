"""Lightweight stub of the aiohttp interface used in tests.

This stub is **not** a real HTTP client. It merely provides the minimal
classes and context manager behaviour required by ``link_checker`` so
that the module can be imported without the external dependency.
"""
from __future__ import annotations

class ClientError(Exception):
    pass

class ClientTimeout:
    def __init__(self, total: float | None = None):
        self.total = total

class TCPConnector:
    def __init__(self, limit: int | None = None):
        self.limit = limit

class DummyResponse:
    def __init__(self, status: int = 200):
        self.status = status
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return False

class ClientSession:
    def __init__(self, *args, **kwargs):
        pass
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return False
    async def head(self, *args, **kwargs):
        return DummyResponse()
    async def get(self, *args, **kwargs):
        return DummyResponse()
