import sys
import pathlib as _pathlib
sys.path.append(str(_pathlib.Path(__file__).resolve().parent.parent))
from src.pipeline.base_orchestrator import BaseOrchestrator
import pytest

def test_orchestrator_create_response_success(mock_openai, mock_responses_success):
    orchestrator = BaseOrchestrator()
    response = orchestrator.create_response("hello")
    assert response.output.message.content == "mocked response"

def test_orchestrator_create_response_error(mock_openai, mock_responses_error):
    orchestrator = BaseOrchestrator()
    with pytest.raises(Exception, match="Mock API error"):
        orchestrator.create_response("hello")