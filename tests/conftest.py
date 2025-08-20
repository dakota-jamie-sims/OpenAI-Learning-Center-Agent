import sys
import pathlib as _pathlib
sys.path.append(str(_pathlib.Path(__file__).resolve().parent.parent))
import pytest
from unittest.mock import MagicMock

@pytest.fixture
def mock_openai(monkeypatch):
    """Patch the OpenAI client to avoid real API calls."""
    mock_client = MagicMock()
    monkeypatch.setattr("src.services.openai_responses_client.OpenAI", lambda *args, **kwargs: mock_client)
    monkeypatch.setattr("src.pipeline.base_orchestrator.OpenAI", lambda *args, **kwargs: mock_client)
    monkeypatch.setattr("openai.OpenAI", lambda *args, **kwargs: mock_client)
    return mock_client

@pytest.fixture
def mock_responses_success(monkeypatch):
    """Patch ResponsesClient methods to return a deterministic response."""
    from src.services.openai_responses_client import ResponsesClient
    mock_response = MagicMock()
    mock_response.output = MagicMock(message=MagicMock(content="mocked response"))

    def _create_response(self, *args, **kwargs):  # noqa: D401
        return mock_response

    def _create_simple_response(self, *args, **kwargs):  # noqa: D401
        return "mocked response"

    monkeypatch.setattr(ResponsesClient, "create_response", _create_response)

    monkeypatch.setattr(ResponsesClient, "create_simple_response", _create_simple_response)
    return mock_response

@pytest.fixture
def mock_responses_error(monkeypatch):
    """Patch ResponsesClient to raise an error."""
    from src.services.openai_responses_client import ResponsesClient

    def _raise(self, *args, **kwargs):  # noqa: D401
        raise Exception("Mock API error")

    monkeypatch.setattr(ResponsesClient, "create_response", _raise)
    monkeypatch.setattr(ResponsesClient, "create_simple_response", _raise)
