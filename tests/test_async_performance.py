"""Test async performance improvements in multi-agent system"""
import time
import time
import asyncio
from unittest.mock import MagicMock
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.agents.team_leads import ResearchTeamLead
from src.agents.multi_agent_base import AgentMessage, MessageType


def test_parallel_research_execution(monkeypatch):
    """Test that research agents execute in parallel, not sequentially"""
    
    # Track execution times
    execution_log = []
    
    def mock_receive_message(agent_name, delay, async_mode=True):
        """Mock agent that records when it starts/ends and simulates work"""

        if async_mode:
            async def _receive(message):
                start_time = time.time()
                execution_log.append((agent_name, "start", start_time))

                await asyncio.sleep(delay)

                end_time = time.time()
                execution_log.append((agent_name, "end", end_time))

                response = MagicMock()
                response.payload = {"success": True, "data": f"Results from {agent_name}"}
                return response

            return _receive
        else:
            def _receive(message):
                start_time = time.time()
                execution_log.append((agent_name, "start", start_time))

                time.sleep(delay)

                end_time = time.time()
                execution_log.append((agent_name, "end", end_time))

                response = MagicMock()
                response.payload = {"success": True, "data": f"Results from {agent_name}"}
                return response

            return _receive
    
    # Set dummy API key to avoid initialization errors
    monkeypatch.setenv("OPENAI_API_KEY", "test")

    # Create research team lead
    research_lead = ResearchTeamLead()
    
    # Mock the sub-agents with different delays
    research_lead.web_researcher.receive_message = mock_receive_message("web", 2.0, True)
    research_lead.kb_researcher.receive_message = mock_receive_message("kb", 1.5, True)
    research_lead.data_validator.receive_message = lambda msg: MagicMock(payload={"success": True})
    research_lead.query_llm = MagicMock(return_value="synthesis")
    
    # Create test message
    test_message = AgentMessage(
        from_agent="test",
        to_agent="research_lead",
        message_type=MessageType.REQUEST,
        task="comprehensive_research",
        payload={"topic": "test topic", "requirements": {"min_sources": 0}},
        context={},
        timestamp=""
    )
    
    # Execute research
    start_time = time.time()
    response = asyncio.run(research_lead.process_message(test_message))
    total_time = time.time() - start_time
    
    # Verify successful response
    assert response.payload["success"] == True
    
    # Analyze execution pattern
    web_events = [(name, event, t) for name, event, t in execution_log if name == "web"]
    kb_events = [(name, event, t) for name, event, t in execution_log if name == "kb"]
    
    # Check if web and KB started close to each other (within 0.1 seconds)
    web_start = web_events[0][2]
    kb_start = kb_events[0][2]
    start_difference = abs(web_start - kb_start)
    
    print(f"\nExecution Analysis:")
    print(f"Total execution time: {total_time:.2f}s")
    print(f"Web and KB start difference: {start_difference:.3f}s")
    print("\nExecution log:")
    for name, event, t in execution_log:
        print(f"  {name:10} {event:5} at {t - start_time:.3f}s")
    
    # If running in parallel, start times should be very close
    # If sequential, KB would start ~2 seconds after web
    if start_difference < 0.5:
        print("\n✅ PARALLEL EXECUTION CONFIRMED!")
    else:
        print("\n❌ SEQUENTIAL EXECUTION DETECTED!")
    
    # Total time should be close to the longest operation (2s), not sum (4s)
    assert total_time < 3.0, f"Execution took {total_time:.2f}s - should be under 3s for parallel execution"


if __name__ == "__main__":
    test_parallel_research_execution()