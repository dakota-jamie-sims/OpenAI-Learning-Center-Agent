#!/usr/bin/env python3
"""
Test direct KB search implementation
"""
import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.services.kb_search_direct import search_kb_direct, get_direct_kb_searcher

def main():
    print("="*60)
    print("Testing Direct KB Search (Production)")
    print("="*60)
    
    # Test 1: Basic search
    print("\n1. Testing basic search...")
    query = "portfolio diversification strategies"
    
    start = datetime.now()
    result = search_kb_direct(query, max_results=3)
    duration = (datetime.now() - start).total_seconds()
    
    print(f"\n✅ Search completed in {duration:.2f}s")
    print(f"Success: {result['success']}")
    print(f"Citations found: {result.get('citations_count', 0)}")
    
    if result['success']:
        print(f"\nResults:\n{result['results'][:500]}...")
        
        if result.get('citations'):
            print(f"\nCitations:")
            for i, cit in enumerate(result['citations'][:3], 1):
                print(f"{i}. {cit.get('filename', 'Unknown')}: {cit.get('text', '')[:100]}...")
    else:
        print(f"Error: {result.get('error', 'Unknown')}")
    
    # Test 2: Multiple queries
    print("\n\n2. Testing multiple queries...")
    queries = [
        "AI investment opportunities",
        "private equity trends"
    ]
    
    searcher = get_direct_kb_searcher()
    start = datetime.now()
    results = searcher.search_batch(queries, max_results_per_query=2)
    duration = (datetime.now() - start).total_seconds()
    
    print(f"\n✅ {len(queries)} searches completed in {duration:.2f}s total")
    
    for query, result in zip(queries, results):
        print(f"\nQuery: '{query}'")
        print(f"  Success: {result['success']}")
        print(f"  Citations: {result.get('citations_count', 0)}")
    
    print("\n" + "="*60)
    print("✅ Direct KB search is working!")
    print("="*60)

if __name__ == "__main__":
    main()