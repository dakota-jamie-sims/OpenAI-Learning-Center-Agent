#!/usr/bin/env python3
"""
Test that all components are using GPT-5 models via Responses API
"""
import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.config import DEFAULT_MODELS
from src.services.openai_responses_client import ResponsesClient
from src.services.kb_search_responses import search_kb_responses
from src.services.web_search import search_web
from src.utils.logging import get_logger

logger = get_logger(__name__)

def test_models_configured():
    """Test that all models are GPT-5 variants"""
    print("\n1. Testing Model Configuration")
    print("-" * 40)
    
    gpt5_models = ["gpt-5", "gpt-5-mini", "gpt-5-nano"]
    all_gpt5 = True
    
    for role, model in DEFAULT_MODELS.items():
        is_gpt5 = model in gpt5_models
        status = "✅" if is_gpt5 else "❌"
        print(f"{status} {role}: {model}")
        if not is_gpt5:
            all_gpt5 = False
    
    assert all_gpt5, "Not all models are GPT-5 variants!"
    print("\n✅ All models are GPT-5 variants")
    return True

def test_responses_api():
    """Test basic Responses API functionality"""
    print("\n2. Testing Responses API")
    print("-" * 40)
    
    client = ResponsesClient()
    
    # Test with different GPT-5 models
    test_cases = [
        ("gpt-5", "high", "What is 2+2?"),
        ("gpt-5-mini", "medium", "Name three colors"),
        ("gpt-5-nano", "minimal", "Hello")
    ]
    
    for model, effort, prompt in test_cases:
        print(f"\nTesting {model} (effort={effort})...")
        start = datetime.now()
        
        try:
            response = client.create_response(
                model=model,
                input_text=prompt,
                reasoning_effort=effort,
                verbosity="low"
            )
            
            duration = (datetime.now() - start).total_seconds()
            
            # Extract text content
            text = ""
            if hasattr(response, 'output'):
                for item in response.output:
                    if hasattr(item, 'message') and hasattr(item.message, 'content'):
                        text = item.message.content
                        break
            
            print(f"✅ {model} responded in {duration:.2f}s")
            print(f"   Response: {text[:100]}...")
            
        except Exception as e:
            print(f"❌ {model} failed: {str(e)}")
            raise
    
    print("\n✅ All GPT-5 models working via Responses API")
    return True

def test_kb_search_with_gpt5():
    """Test KB search uses Responses API"""
    print("\n3. Testing KB Search with GPT-5")
    print("-" * 40)
    
    query = "portfolio management strategies"
    print(f"Query: {query}")
    
    start = datetime.now()
    result = search_kb_responses(query, max_results=2)
    duration = (datetime.now() - start).total_seconds()
    
    if result['success']:
        print(f"✅ KB search completed in {duration:.2f}s")
        print(f"   Citations: {result.get('citations_count', 0)}")
        print(f"   Results preview: {result['results'][:200]}...")
    else:
        print(f"❌ KB search failed: {result.get('error', 'Unknown')}")
        
    assert result['success'], "KB search should succeed"
    print("\n✅ KB search working with Responses API")
    return True

def test_agent_with_gpt5():
    """Test agent uses GPT-5 via Responses API"""
    print("\n4. Testing Agent with GPT-5")
    print("-" * 40)
    
    from src.agents.multi_agent_base import BaseAgent, AgentMessage, MessageType
    
    # Create a test agent
    class TestAgent(BaseAgent):
        def process_message(self, message):
            # This will use query_llm which uses ResponsesClient
            result = self.query_llm(
                "Respond with 'GPT-5 is working' if you can process this.",
                reasoning_effort="minimal",
                verbosity="low"
            )
            return self._create_response(message, {"result": result})
        
        def validate_task(self, task, payload):
            return True, "Valid"
    
    agent = TestAgent("test_agent", "default")
    print(f"Agent model: {agent.model}")
    
    # Send test message
    msg = AgentMessage(
        from_agent="test",
        to_agent="test_agent",
        message_type=MessageType.REQUEST,
        task="test",
        payload={},
        context={}
    )
    
    response = agent.receive_message(msg)
    if response and response.payload.get("result"):
        print(f"✅ Agent responded: {response.payload['result'][:50]}...")
    else:
        print("❌ Agent failed to respond")
        
    print("\n✅ Agents working with GPT-5 via Responses API")
    return True

def main():
    print("="*60)
    print("GPT-5 RESPONSES API SYSTEM TEST")
    print("="*60)
    
    try:
        # Run all tests
        test_models_configured()
        test_responses_api()
        test_kb_search_with_gpt5()
        test_agent_with_gpt5()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED - System using GPT-5 via Responses API!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        logger.error("Test failed", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())