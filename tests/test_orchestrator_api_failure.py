import os
import sys

import pytest

# Ensure repository root is on the path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.agents.orchestrator import OrchestratorAgent
from src.agents.multi_agent_base import AgentMessage, MessageType
from src.models import ArticleRequest


def test_orchestrator_handles_api_failure(monkeypatch):
    """The orchestrator should surface errors when the LLM API fails."""

    def mock_create_response(*args, **kwargs):
        raise Exception("API failure")

    # Patch the ResponsesClient to always fail
    monkeypatch.setattr(
        "src.services.openai_responses_client.ResponsesClient.__init__",
        lambda self: None,
    )
    monkeypatch.setattr(
        "src.services.openai_responses_client.ResponsesClient.create_response",
        mock_create_response,
    )
    monkeypatch.setattr(
        "src.services.kb_search.KnowledgeBaseSearcher.__init__",
        lambda self: None,
    )
    monkeypatch.setattr(
        "src.services.kb_search.KnowledgeBaseSearcher.search",
        lambda self, query: {"success": False, "results": []},
    )

    orchestrator = OrchestratorAgent()

    request = ArticleRequest(
        topic="Test topic",
        audience="investors",
        tone="formal",
        word_count=500,
    )

    message = AgentMessage(
        from_agent="tester",
        to_agent=orchestrator.agent_id,
        message_type=MessageType.REQUEST,
        task="generate_article",
        payload={"request": request},
        context={},
        timestamp="",
    )

    response = orchestrator.receive_message(message)
    assert not response.payload["success"]
    assert "Research phase failed" in response.payload["error"]
    assert "API failure" in response.payload["details"].get("error", "")
