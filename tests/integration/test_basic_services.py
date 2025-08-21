#!/usr/bin/env python3
"""
Test basic services without agent framework
"""
import os
import sys
import asyncio
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_web_search():
    """Test web search service"""
    print("\n1. Testing Web Search Service...")
    try:
        from services.web_search import search_web
        start = datetime.now()
        results = search_web("AI investment trends", max_results=2)
        duration = (datetime.now() - start).total_seconds()
        
        print(f"   ✅ Completed in {duration:.2f}s")
        print(f"   Results: {len(results)}")
        for i, r in enumerate(results[:2], 1):
            print(f"   {i}. {r.get('title', 'No title')[:50]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_kb_search():
    """Test KB search service"""
    print("\n2. Testing KB Search Service...")
    try:
        from services.kb_search_optimized import search_knowledge_base
        start = datetime.now()
        result = search_knowledge_base("portfolio management", max_results=2)
        duration = (datetime.now() - start).total_seconds()
        
        print(f"   ✅ Completed in {duration:.2f}s")
        print(f"   Success: {result.get('success')}")
        print(f"   Status: {result.get('status')}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

async def test_async_execution():
    """Test async execution pattern"""
    print("\n3. Testing Async Execution...")
    
    async def slow_task(name, duration):
        print(f"   Starting {name}...")
        await asyncio.sleep(duration)
        return f"{name} completed"
    
    try:
        start = datetime.now()
        # Run tasks in parallel
        results = await asyncio.gather(
            slow_task("Task1", 1),
            slow_task("Task2", 1),
            slow_task("Task3", 1)
        )
        duration = (datetime.now() - start).total_seconds()
        
        print(f"   ✅ All tasks completed in {duration:.2f}s (should be ~1s, not 3s)")
        for r in results:
            print(f"   - {r}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def test_responses_api():
    """Test OpenAI Responses API"""
    print("\n4. Testing OpenAI Responses API...")
    try:
        from utils.responses_client import ResponsesClient
        client = ResponsesClient()
        
        start = datetime.now()
        response = client.create_response(
            model="gpt-5",
            input_text="What is 2+2?",
            reasoning_effort="low",
            max_output_tokens=10
        )
        duration = (datetime.now() - start).total_seconds()
        
        print(f"   ✅ Completed in {duration:.2f}s")
        print(f"   Response: {response[:50]}...")
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    print("="*60)
    print("Testing Basic Services")
    print("="*60)
    
    # Test individual services
    test_web_search()
    test_kb_search()
    
    # Test async
    print("\nTesting async execution...")
    asyncio.run(test_async_execution())
    
    # Test Responses API
    test_responses_api()
    
    print("\n" + "="*60)
    print("Basic tests completed!")

if __name__ == "__main__":
    main()