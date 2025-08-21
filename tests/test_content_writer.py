import sys
import pathlib as _pathlib
sys.path.append(str(_pathlib.Path(__file__).resolve().parent.parent))
from src.agents.writing_agents import ContentWriterAgent


def test_content_writer_success(mock_openai, mock_responses_success):
    agent = ContentWriterAgent()
    result = agent.query_llm("Write an intro")
    assert result == "mocked response"


def test_content_writer_error(mock_openai, mock_responses_error):
    agent = ContentWriterAgent()
    result = agent.query_llm("Write an intro")
    assert result == "Error: Mock API error"