import sys
import pathlib as _pathlib
sys.path.append(str(_pathlib.Path(__file__).resolve().parent.parent))

from src.agents.team_leads import PublishingTeamLead
from src.agents.orchestrator import OrchestratorAgent
from src.agents.multi_agent_base import AgentMessage, MessageType
from src.models import ArticleRequest


def test_metadata_generation_missing_fields(monkeypatch, mock_openai):
    lead = PublishingTeamLead()
    monkeypatch.setattr(PublishingTeamLead, "query_llm", lambda self, *args, **kwargs: "title: Sample\nDescription: Desc")
    result = lead._generate_comprehensive_metadata("content", {})
    assert not result["success"]
    assert "keywords" in result["error"]


def test_orchestrator_reports_invalid_metadata(monkeypatch, mock_openai):
    orchestrator = OrchestratorAgent()

    async def _mock_research(self, request):
        return {"success": True}

    async def _mock_writing(self, request, research):
        return {"success": True, "article": "content"}

    async def _mock_quality(self, article):
        return {"ready_for_publication": True, "approved_article": article}

    monkeypatch.setattr(OrchestratorAgent, "_phase_research", _mock_research)
    monkeypatch.setattr(OrchestratorAgent, "_phase_writing", _mock_writing)
    monkeypatch.setattr(OrchestratorAgent, "_phase_quality_check", _mock_quality)

    monkeypatch.setattr(PublishingTeamLead, "query_llm", lambda self, *args, **kwargs: "title: Sample")
    monkeypatch.setattr(PublishingTeamLead, "_optimize_for_seo", lambda self, *args, **kwargs: {"optimized_content": "content", "seo_data": {}, "seo_score": 0})
    monkeypatch.setattr(PublishingTeamLead, "_create_social_media_content", lambda self, *args, **kwargs: {"social_content": [], "platforms_covered": [], "estimated_engagement": 0})
    monkeypatch.setattr(PublishingTeamLead, "_calculate_metadata_completeness", lambda self, metadata: 0.0)

    request = ArticleRequest(topic="Test Topic")
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
    assert "publishing phase failed" in response.payload["error"].lower()
    assert "missing required metadata" in response.payload["details"].get("error", "").lower()
