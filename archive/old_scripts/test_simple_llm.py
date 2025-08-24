#!/usr/bin/env python3
"""Test simple LLM query to debug timeouts"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import time
from src.services.openai_responses_client import ResponsesClient

async def test_simple_query():
    """Test a simple LLM query"""
    print("\n🧪 Testing Simple LLM Query")
    print("=" * 40)
    
    client = ResponsesClient(timeout=15)
    
    try:
        start_time = time.time()
        
        # Test with GPT-5-nano and minimal parameters
        response = await asyncio.to_thread(
            client.create_response,
            model="gpt-5-nano",
            input_text="Say 'Hello World' in one sentence.",
            reasoning_effort="minimal",
            verbosity="low",
            max_tokens=50
        )
        
        elapsed = time.time() - start_time
        print(f"✅ Response received in {elapsed:.1f}s")
        
        # Extract text
        if hasattr(response, 'content') and response.content:
            if isinstance(response.content, list) and len(response.content) > 0:
                if hasattr(response.content[0], 'text'):
                    print(f"Response: {response.content[0].text}")
                    return True
        
        print(f"Response object: {response}")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_web_search():
    """Test web search"""
    print("\n\n🧪 Testing Web Search")
    print("=" * 40)
    
    from src.services.web_search import search_web
    
    try:
        start_time = time.time()
        
        results = await asyncio.to_thread(
            search_web, 
            "AI portfolio management 2025", 
            3
        )
        
        elapsed = time.time() - start_time
        print(f"✅ Search completed in {elapsed:.1f}s")
        print(f"Results found: {len(results) if results else 0}")
        
        if results:
            for i, result in enumerate(results[:2]):
                print(f"\nResult {i+1}:")
                print(f"  Title: {result.get('title', 'N/A')[:60]}...")
                print(f"  URL: {result.get('url', 'N/A')}")
        
        return bool(results)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_kb_search():
    """Test KB search"""
    print("\n\n🧪 Testing KB Search")
    print("=" * 40)
    
    from src.services.kb_search_optimized import OptimizedKBSearcher
    
    try:
        kb_searcher = OptimizedKBSearcher()
        start_time = time.time()
        
        results = await asyncio.to_thread(
            kb_searcher.search,
            "portfolio management",
            max_results=3,
            timeout=10
        )
        
        elapsed = time.time() - start_time
        print(f"✅ KB search completed in {elapsed:.1f}s")
        
        if isinstance(results, dict):
            print(f"Success: {results.get('success', False)}")
            print(f"Results found: {len(results.get('results', []))}")
        else:
            print(f"Results type: {type(results)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("🔍 Debugging Multi-Agent System Components")
    print("Testing each component individually to find timeout source")
    
    # Test each component
    llm_ok = await test_simple_query()
    web_ok = await test_web_search()
    kb_ok = await test_kb_search()
    
    print("\n\n📊 Test Summary:")
    print(f"LLM Query: {'✅' if llm_ok else '❌'}")
    print(f"Web Search: {'✅' if web_ok else '❌'}")
    print(f"KB Search: {'✅' if kb_ok else '❌'}")
    
    if all([llm_ok, web_ok, kb_ok]):
        print("\n✅ All components working! Issue might be in orchestration complexity.")
    else:
        print("\n❌ Some components failing. Check logs above.")


if __name__ == "__main__":
    asyncio.run(main())