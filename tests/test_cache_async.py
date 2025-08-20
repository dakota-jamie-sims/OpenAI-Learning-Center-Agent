import asyncio
import time
from datetime import datetime

from src.services import web_search
from src.agents.multi_agent_base import BaseAgent, AgentMessage, MessageType, llm_cache
from src.agents.team_leads import ResearchTeamLead


class DummyAgent(BaseAgent):
    def __init__(self):
        super().__init__("dummy", "dummy")

    def process_message(self, message: AgentMessage) -> AgentMessage:
        return message

    def validate_task(self, task, payload):
        return True, "ok"


def test_web_search_caching(monkeypatch):
    web_search.web_cache.clear()
    calls = {"count": 0}

    def fake_impl(query: str, max_results: int = 5):
        calls["count"] += 1
        return [{"title": "res", "url": "#"}]

    monkeypatch.setattr(web_search, "_search_web_impl", fake_impl)

    first = web_search.search_web("alpha")
    second = web_search.search_web("alpha")
    assert calls["count"] == 1
    assert first == second


def test_query_llm_caching(monkeypatch):
    llm_cache.clear()
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    agent = DummyAgent()
    calls = {"count": 0}

    def fake_response(*args, **kwargs):
        calls["count"] += 1

        class Resp:
            def __init__(self):
                self.output = type("o", (), {"message": type("m", (), {"content": "hello"})()})()
                self.choices = []

        return Resp()

    monkeypatch.setattr(agent.responses_client, "create_response", fake_response)

    t1 = agent.query_llm("hi")
    t2 = agent.query_llm("hi")
    assert calls["count"] == 1
    assert t1 == t2 == "hello"


def test_research_lead_concurrency(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setenv("VECTOR_STORE_ID", "vs-test")
    lead = ResearchTeamLead()

    def slow_response(message):
        time.sleep(0.2)
        return AgentMessage(
            from_agent="x",
            to_agent=lead.agent_id,
            message_type=MessageType.RESPONSE,
            task="t",
            payload={"sources": []},
            context={},
            timestamp=datetime.now().isoformat(),
        )

    monkeypatch.setattr(lead.web_researcher, "receive_message", slow_response)
    monkeypatch.setattr(lead.kb_researcher, "receive_message", slow_response)
    monkeypatch.setattr(lead.data_validator, "receive_message", lambda msg: slow_response(msg))
    monkeypatch.setattr(ResearchTeamLead, "_extract_all_sources", lambda self, content: [])
    monkeypatch.setattr(ResearchTeamLead, "_synthesize_findings", lambda self, t, c, v, s: "s")
    monkeypatch.setattr(ResearchTeamLead, "_calculate_research_quality", lambda self, c, v: 0)

    start = time.perf_counter()
    asyncio.run(lead.coordinate_comprehensive_research({"topic": "x", "requirements": {"min_sources": 0}}))
    duration = time.perf_counter() - start
    assert duration < 0.45
