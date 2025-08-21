#!/usr/bin/env python3
"""
Test individual components to isolate issues
"""
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.web_search import search_web
from services.kb_search_optimized import search_knowledge_base
from agents.research_agents import WebResearchAgent, KnowledgeBaseAgent
from agents.multi_agent_base import AgentMessage, MessageType
import logging

logging.basicConfig(level=logging.INFO)

def test_web_search_direct():
    """Test web search directly"""
    print("\n1. Testing Web Search Directly...")
    start = datetime.now()
    results = search_web("portfolio diversification 2024", max_results=3)
    duration = (datetime.now() - start).total_seconds()
    
    print(f"   ✅ Web search completed in {duration:.2f}s")
    print(f"   Found {len(results)} results")
    if results:
        print(f"   First result: {results[0].get('title', 'No title')[:50]}...")

def test_kb_search_direct():
    """Test KB search directly"""
    print("\n2. Testing KB Search Directly...")
    start = datetime.now()
    results = search_knowledge_base("portfolio diversification", max_results=3)
    duration = (datetime.now() - start).total_seconds()
    
    print(f"   ✅ KB search completed in {duration:.2f}s")
    print(f"   Success: {results.get('success', False)}")
    print(f"   Status: {results.get('status', 'Unknown')}")

def test_web_agent():
    """Test web research agent"""
    print("\n3. Testing Web Research Agent...")
    agent = WebResearchAgent()
    
    msg = AgentMessage(
        from_agent="test",
        to_agent=agent.agent_id,
        message_type=MessageType.REQUEST,
        task="search_web",
        payload={"query": "portfolio diversification strategies"},
        context={},
        timestamp=datetime.now().isoformat()
    )
    
    start = datetime.now()
    response = agent.receive_message(msg)
    duration = (datetime.now() - start).total_seconds()
    
    print(f"   ✅ Agent responded in {duration:.2f}s")
    print(f"   Success: {response.payload.get('success', False)}")

def test_kb_agent():
    """Test KB agent"""
    print("\n4. Testing KB Agent...")
    agent = KnowledgeBaseAgent()
    
    msg = AgentMessage(
        from_agent="test",
        to_agent=agent.agent_id,
        message_type=MessageType.REQUEST,
        task="search_kb",
        payload={"query": "investment strategies"},
        context={},
        timestamp=datetime.now().isoformat()
    )
    
    start = datetime.now()
    response = agent.receive_message(msg)
    duration = (datetime.now() - start).total_seconds()
    
    print(f"   ✅ Agent responded in {duration:.2f}s")
    print(f"   Success: {response.payload.get('success', False)}")

def main():
    print("="*60)
    print("Testing Individual Components")
    print("="*60)
    
    test_web_search_direct()
    test_kb_search_direct()
    test_web_agent()
    test_kb_agent()
    
    print("\n" + "="*60)
    print("All component tests completed!")
    print("="*60)

if __name__ == "__main__":
    main()