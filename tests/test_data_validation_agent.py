import sys
import pathlib as _pathlib

sys.path.append(str(_pathlib.Path(__file__).resolve().parent.parent))

from src.agents.research_agents import DataValidationAgent


def test_check_source_credibility_empty_sources(mock_openai):
    agent = DataValidationAgent()
    result = agent._check_source_credibility([])
    assert result["success"] is False
    assert result["average_credibility"] == 0
    assert result["sources_checked"] == 0
    assert result["results"] == []
    assert "No sources" in result.get("error", "")
