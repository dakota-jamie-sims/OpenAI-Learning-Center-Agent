import os
import sys
from unittest.mock import AsyncMock, patch
import asyncio
import types

sys.path.insert(0, os.getcwd())

# Create minimal stubs for the external 'agents' package
stub_agents = types.ModuleType("agents")

class _Runner:
    async def run(self, agent, prompt):
        return None

stub_agents.Runner = _Runner()

class _Agent:
    def __init__(self, *args, **kwargs):
        pass

class _WebSearchTool:
    pass

class _FileSearchTool:
    pass

stub_agents.Agent = _Agent
stub_agents.WebSearchTool = _WebSearchTool
stub_agents.FileSearchTool = _FileSearchTool
stub_agents.function_tool = lambda f: f

sys.modules['agents'] = stub_agents

# Stub aiohttp for tools.link_checker dependency
stub_aiohttp = types.ModuleType("aiohttp")

class _Session:
    def __init__(self, *args, **kwargs):
        pass
    async def __aenter__(self):
        return self
    async def __aexit__(self, exc_type, exc, tb):
        return False

stub_aiohttp.ClientSession = _Session
stub_aiohttp.ClientTimeout = lambda total=None: None
stub_aiohttp.TCPConnector = lambda limit=None: None
stub_aiohttp.ClientError = Exception

sys.modules['aiohttp'] = stub_aiohttp

from src.pipeline.orchestrator import Pipeline


class DummyRes:
    def __init__(self, output):
        self.final_output = output


def test_phase2_parallel_research(tmp_path, monkeypatch):
    async def run_test():
        monkeypatch.setattr('src.pipeline.orchestrator.RUNS_DIR', str(tmp_path))
        mock_run = AsyncMock(side_effect=[DummyRes("web"), DummyRes("kb")])
        with patch('src.pipeline.orchestrator.Runner.run', mock_run), \
             patch('src.pipeline.orchestrator.web_researcher.create', return_value=object()), \
             patch('src.pipeline.orchestrator.kb_researcher.create', return_value=object()):
            pipeline = Pipeline("topic")
            briefs = await pipeline.phase2_parallel_research()
        assert briefs == {"web": "web", "kb": "kb"}
        assert mock_run.await_count == 2
    asyncio.run(run_test())


def test_phase4_content_writes_file(tmp_path, monkeypatch):
    async def run_test():
        monkeypatch.setattr('src.pipeline.orchestrator.RUNS_DIR', str(tmp_path))
        mock_run = AsyncMock(return_value=DummyRes("article text"))
        with patch('src.pipeline.orchestrator.content_writer.create', return_value=types.SimpleNamespace(tools=[])), \
             patch('src.pipeline.orchestrator.Runner.run', mock_run):
            pipeline = Pipeline("topic")
            path = await pipeline.phase4_content("synth")
        assert os.path.exists(path)
        with open(path, "r", encoding="utf-8") as f:
            assert f.read() == "article text"
    asyncio.run(run_test())


def test_phase6_validation_approved(tmp_path, monkeypatch):
    async def run_test():
        monkeypatch.setattr('src.pipeline.orchestrator.RUNS_DIR', str(tmp_path))
        monkeypatch.setattr('src.pipeline.orchestrator.ENABLE_CLAIM_CHECK', True)
        mock_run = AsyncMock(side_effect=[DummyRes("✅ APPROVED"), DummyRes("APPROVE")])
        with patch('src.pipeline.orchestrator.fact_checker.create', return_value=types.SimpleNamespace(tools=[])), \
             patch('src.pipeline.orchestrator.claim_checker.create', return_value=types.SimpleNamespace()), \
             patch('src.pipeline.orchestrator.Runner.run', mock_run):
            pipeline = Pipeline("topic")
            os.makedirs(os.path.dirname(pipeline.article_path), exist_ok=True)
            with open(pipeline.article_path, "w", encoding="utf-8") as f:
                f.write("See https://example.com")
            with open(pipeline.metadata_path, "w", encoding="utf-8") as f:
                f.write("Meta https://meta.com")
            result = await pipeline.phase6_validation()
        assert result["decision"] == "APPROVED"
        assert result["fc_approved"] is True
        assert result["cc_approved"] is True
        assert result["issues"] == []
        assert mock_run.await_count == 2
    asyncio.run(run_test())
