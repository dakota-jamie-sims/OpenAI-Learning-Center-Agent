#!/usr/bin/env python3
"""Test the fixed response extraction"""

import asyncio
import sys
import os

sys.path.append(os.path.abspath('.'))

from src.agents.dakota_agents.base_agent import DakotaBaseAgent

async def test_extraction():
    """Test if response extraction works properly"""
    
    # Create a test agent
    agent = DakotaBaseAgent("test_agent", model_override="gpt-5-mini")
    
    print("Testing GPT-5 response extraction...")
    print(f"Model: {agent.model}")
    
    # Test a simple query
    try:
        result = await agent.query_llm(
            "What is 2+2? Answer with just the number.",
            max_tokens=10,
            reasoning_effort="minimal"
        )
        
        print(f"\n✅ Response extraction successful!")
        print(f"Result: {result}")
        print(f"Result type: {type(result)}")
        
    except Exception as e:
        print(f"\n❌ Response extraction failed!")
        print(f"Error: {e}")
        print(f"Error type: {type(e).__name__}")
        
    # Test a more complex query
    print("\n\nTesting complex query...")
    try:
        result2 = await agent.query_llm(
            "List 3 benefits of private credit for institutional investors.",
            max_tokens=200,
            reasoning_effort="low"
        )
        
        print(f"\n✅ Complex response successful!")
        print(f"Result preview: {result2[:100]}...")
        
    except Exception as e:
        print(f"\n❌ Complex response failed!")
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_extraction())