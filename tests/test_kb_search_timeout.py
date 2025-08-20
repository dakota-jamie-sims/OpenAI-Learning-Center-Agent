import os
import pytest
from types import SimpleNamespace
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from src.services.kb_search import KnowledgeBaseSearcher


class DummyMessages:
    def create(self, thread_id, role, content):
        return SimpleNamespace(id="msg_1")

    def list(self, thread_id):
        text = SimpleNamespace(value="dummy", annotations=[])
        content = [SimpleNamespace(text=text)]
        return SimpleNamespace(data=[SimpleNamespace(content=content)])


class DummyRuns:
    def create(self, thread_id, assistant_id):
        return SimpleNamespace(id="run_1", status="in_progress")

    def retrieve(self, thread_id, run_id):
        return SimpleNamespace(id=run_id, status="in_progress")


class DummyThreads:
    def __init__(self):
        self.messages = DummyMessages()
        self.runs = DummyRuns()

    def create(self):
        return SimpleNamespace(id="thread_1")


class DummyAssistants:
    def create(self, **kwargs):
        return SimpleNamespace(id="assistant_1")

    def delete(self, assistant_id):
        pass


class DummyBeta:
    def __init__(self):
        self.assistants = DummyAssistants()
        self.threads = DummyThreads()


class DummyClient:
    def __init__(self):
        self.beta = DummyBeta()


def test_search_times_out():
    os.environ["VECTOR_STORE_ID"] = "vs_dummy"
    client = DummyClient()
    searcher = KnowledgeBaseSearcher(client=client, max_wait_time=0.1, retry_count=1)
    result = searcher.search("topic")
    assert result["success"] is False
    assert result["status"] == "timeout"
