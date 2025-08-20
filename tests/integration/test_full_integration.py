#!/usr/bin/env python3
"""
Test Full System Integration with Vector Store
"""
import os
import sys
from pathlib import Path
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()

def test_orchestrators():
    """Test all orchestrators with vector store integration"""
    print("=== Testing All Orchestrators with Vector Store ===\n")
    
    test_topic = "private equity secondaries market trends 2025"
    results = {}
    
    # Test Simple Orchestrator
    print("1. Testing Simple Orchestrator...")
    try:
        from src.pipeline.simple_orchestrator import SimpleOrchestrator
        simple = SimpleOrchestrator()
        kb_result = simple.search_knowledge_base(test_topic, max_results=3)
        if kb_result and "No Dakota knowledge base" not in kb_result:
            print("✅ Simple Orchestrator: Vector store working")
            results["simple"] = "SUCCESS"
        else:
            print("❌ Simple Orchestrator: Vector store not working")
            results["simple"] = "FAILED"
    except Exception as e:
        print(f"❌ Simple Orchestrator Error: {str(e)}")
        results["simple"] = f"ERROR: {str(e)}"
    
    # Test Enhanced Orchestrator
    print("\n2. Testing Enhanced Orchestrator...")
    try:
        from src.pipeline.enhanced_orchestrator import EnhancedOrchestrator
        enhanced = EnhancedOrchestrator()
        kb_result = enhanced.search_knowledge_base(test_topic, max_results=3)
        if kb_result and "No Dakota knowledge base" not in kb_result:
            print("✅ Enhanced Orchestrator: Vector store working")
            results["enhanced"] = "SUCCESS"
        else:
            print("❌ Enhanced Orchestrator: Vector store not working")
            results["enhanced"] = "FAILED"
    except Exception as e:
        print(f"❌ Enhanced Orchestrator Error: {str(e)}")
        results["enhanced"] = f"ERROR: {str(e)}"
    
    # Test Strict Orchestrator
    print("\n3. Testing Strict Orchestrator...")
    try:
        from src.pipeline.strict_orchestrator import StrictOrchestrator
        strict = StrictOrchestrator()
        kb_result = strict.search_knowledge_base(test_topic, max_results=3)
        if kb_result and "No Dakota knowledge base" not in kb_result:
            print("✅ Strict Orchestrator: Vector store working")
            results["strict"] = "SUCCESS"
        else:
            print("❌ Strict Orchestrator: Vector store not working")
            results["strict"] = "FAILED"
    except Exception as e:
        print(f"❌ Strict Orchestrator Error: {str(e)}")
        results["strict"] = f"ERROR: {str(e)}"
    
    # Test GPT-5 Orchestrator
    print("\n4. Testing GPT-5 Orchestrator...")
    try:
        from src.pipeline.gpt5_orchestrator import GPT5Orchestrator
        gpt5 = GPT5Orchestrator()
        kb_result = gpt5.search_knowledge_base(test_topic, max_results=3)
        if kb_result and "No Dakota knowledge base" not in kb_result:
            print("✅ GPT-5 Orchestrator: Vector store working")
            results["gpt5"] = "SUCCESS"
        else:
            print("❌ GPT-5 Orchestrator: Vector store not working")
            results["gpt5"] = "FAILED"
    except Exception as e:
        print(f"❌ GPT-5 Orchestrator Error: {str(e)}")
        results["gpt5"] = f"ERROR: {str(e)}"
    
    return results

def test_multi_agent_system():
    """Test multi-agent system with vector store"""
    print("\n\n=== Testing Multi-Agent System ===\n")
    
    try:
        from src.agents.research_agents import KnowledgeBaseAgent
        from src.agents.multi_agent_base import AgentMessage, MessageType
        
        # Test KB Agent
        print("Testing KnowledgeBaseAgent...")
        kb_agent = KnowledgeBaseAgent()
        
        # Create test message
        test_message = AgentMessage(
            from_agent="test",
            to_agent=kb_agent.agent_id,
            message_type=MessageType.REQUEST,
            task="search_kb",
            payload={"query": "Dakota Way investment philosophy"},
            context={},
            timestamp=datetime.now().isoformat()
        )
        
        # Process message
        response = kb_agent.process_message(test_message)
        
        if response.payload.get("status") == "success" and response.payload.get("success"):
            print("✅ Multi-Agent KB Search: Working")
            print(f"   Found insights: {len(response.payload.get('kb_insights', '')) > 100}")
            return "SUCCESS"
        else:
            print("❌ Multi-Agent KB Search: Failed")
            return "FAILED"
            
    except Exception as e:
        print(f"❌ Multi-Agent System Error: {str(e)}")
        return f"ERROR: {str(e)}"

def test_kb_searcher():
    """Test KnowledgeBaseSearcher directly"""
    print("\n\n=== Testing KnowledgeBaseSearcher Service ===\n")
    
    try:
        from src.services.kb_search import KnowledgeBaseSearcher
        
        searcher = KnowledgeBaseSearcher()
        
        # Test different search methods
        tests = [
            ("Basic search", lambda: searcher.search("private equity trends", max_results=3)),
            ("Similar articles", lambda: searcher.search_similar_articles("investment strategies", limit=2)),
            ("Dakota insights", lambda: searcher.get_dakota_insights("relationship building")),
            ("Fact verification", lambda: searcher.verify_fact("Private equity allocations increased in 2024"))
        ]
        
        results = {}
        for test_name, test_func in tests:
            print(f"Testing {test_name}...")
            try:
                result = test_func()
                if result.get("success") or result.get("verification_status") == "verified":
                    print(f"✅ {test_name}: Success")
                    results[test_name] = "SUCCESS"
                else:
                    print(f"❌ {test_name}: Failed")
                    results[test_name] = "FAILED"
            except Exception as e:
                print(f"❌ {test_name}: Error - {str(e)}")
                results[test_name] = f"ERROR: {str(e)}"
        
        return results
        
    except Exception as e:
        print(f"❌ KnowledgeBaseSearcher Error: {str(e)}")
        return {"error": str(e)}

def main():
    """Run all integration tests"""
    print("🚀 Starting Full System Integration Test\n")
    
    # Check environment
    vector_store_id = os.getenv("VECTOR_STORE_ID")
    if not vector_store_id:
        print("❌ ERROR: No VECTOR_STORE_ID found in environment")
        return
    
    print(f"✅ Vector Store ID: {vector_store_id}\n")
    
    # Run tests
    orchestrator_results = test_orchestrators()
    multi_agent_result = test_multi_agent_system()
    kb_searcher_results = test_kb_searcher()
    
    # Summary
    print("\n\n=== INTEGRATION TEST SUMMARY ===\n")
    
    print("Orchestrators:")
    for name, result in orchestrator_results.items():
        status = "✅" if result == "SUCCESS" else "❌"
        print(f"  {status} {name.capitalize()}: {result}")
    
    print(f"\nMulti-Agent System: {multi_agent_result}")
    
    print("\nKB Searcher Methods:")
    for method, result in kb_searcher_results.items():
        if isinstance(result, str):
            status = "✅" if result == "SUCCESS" else "❌"
            print(f"  {status} {method}: {result}")
    
    # Overall status
    all_success = (
        all(r == "SUCCESS" for r in orchestrator_results.values()) and
        multi_agent_result == "SUCCESS" and
        all(r == "SUCCESS" for r in kb_searcher_results.values() if isinstance(r, str))
    )
    
    print(f"\n{'✅ ALL TESTS PASSED!' if all_success else '❌ Some tests failed'}")
    print("\n🎉 Full system integration with vector store is {'WORKING' if all_success else 'PARTIALLY WORKING'}!")

if __name__ == "__main__":
    main()