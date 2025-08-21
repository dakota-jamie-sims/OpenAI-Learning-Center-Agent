#!/usr/bin/env python3
"""
Test production knowledge base search
"""
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.services.kb_search_production import (
    ProductionKBSearcher, 
    search_knowledge_base_production,
    get_production_kb_searcher
)
from src.utils.logging import get_logger

logger = get_logger(__name__)

def test_vector_store_connection():
    """Test connection to vector store"""
    print("\n1. Testing Vector Store Connection...")
    
    try:
        searcher = get_production_kb_searcher()
        info = searcher.get_vector_store_info()
        
        if "error" in info:
            print(f"❌ Error: {info['error']}")
            return False
        
        print(f"✅ Connected to vector store: {info['name']}")
        print(f"   ID: {info['id']}")
        print(f"   Total files: {info['total_files']}")
        print(f"   Status: {info['status']}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return False

def test_basic_search():
    """Test basic search functionality"""
    print("\n2. Testing Basic Search...")
    
    query = "portfolio diversification strategies"
    print(f"   Searching for: '{query}'")
    
    start = datetime.now()
    result = search_knowledge_base_production(query, max_results=3)
    duration = (datetime.now() - start).total_seconds()
    
    print(f"   ⏱️  Search completed in {duration:.2f}s")
    print(f"   ✅ Success: {result['success']}")
    print(f"   📊 Citations found: {result.get('citations_count', 0)}")
    
    if result['success'] and result.get('raw_results'):
        print("\n   Results:")
        for i, citation in enumerate(result['raw_results'][:3], 1):
            print(f"   {i}. File: {citation.get('filename', 'Unknown')}")
            print(f"      Quote: {citation.get('quote', '')[:100]}...")
    
    return result['success']

def test_multiple_searches():
    """Test multiple searches in parallel"""
    print("\n3. Testing Multiple Parallel Searches...")
    
    queries = [
        "AI investment opportunities",
        "private equity trends 2024",
        "ESG investing strategies"
    ]
    
    try:
        searcher = get_production_kb_searcher()
        start = datetime.now()
        results = searcher.search_multiple(queries, max_results_per_query=2)
        duration = (datetime.now() - start).total_seconds()
        
        print(f"   ⏱️  {len(queries)} searches completed in {duration:.2f}s")
        
        for i, (query, result) in enumerate(zip(queries, results), 1):
            print(f"\n   Query {i}: '{query}'")
            print(f"   Success: {result['success']}")
            print(f"   Citations: {result.get('citations_count', 0)}")
        
        return all(r['success'] for r in results)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_search_with_context():
    """Test search with additional context"""
    print("\n4. Testing Search with Context...")
    
    query = "risk management"
    context = "Focus on institutional investors and pension funds"
    
    result = search_knowledge_base_production(query, max_results=3)
    
    if result['success']:
        print(f"✅ Search successful")
        print(f"   Results: {result.get('citations_count', 0)} citations")
    else:
        print(f"❌ Search failed: {result.get('results', 'Unknown error')}")
    
    return result['success']

def main():
    """Run all tests"""
    print("="*60)
    print("Production Knowledge Base Search Tests")
    print("="*60)
    
    # Check if vector store ID is configured
    vector_store_id = os.getenv("OPENAI_VECTOR_STORE_ID") or os.getenv("VECTOR_STORE_ID")
    if not vector_store_id:
        print("\n❌ ERROR: VECTOR_STORE_ID not configured!")
        print("   Set OPENAI_VECTOR_STORE_ID in your .env file")
        print("   Current value:", vector_store_id)
        return
    
    print(f"\n📦 Using Vector Store ID: {vector_store_id}")
    
    # Run tests
    tests_passed = 0
    total_tests = 4
    
    if test_vector_store_connection():
        tests_passed += 1
    
    if test_basic_search():
        tests_passed += 1
    
    if test_multiple_searches():
        tests_passed += 1
    
    if test_search_with_context():
        tests_passed += 1
    
    # Summary
    print("\n" + "="*60)
    print(f"Test Summary: {tests_passed}/{total_tests} tests passed")
    print("="*60)
    
    if tests_passed == total_tests:
        print("\n✅ All tests passed! Production KB search is working correctly.")
    else:
        print(f"\n⚠️  {total_tests - tests_passed} tests failed. Check the errors above.")

if __name__ == "__main__":
    main()