#!/usr/bin/env python3
"""
Test Serper API directly
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from services.web_search import search_web

def test_serper():
    """Test Serper API is working"""
    
    # Get API key
    api_key = os.getenv('SERPER_API_KEY')
    if not api_key:
        print("❌ SERPER_API_KEY not found in environment variables")
        return
    
    print(f"✅ Found Serper API key: {api_key[:10]}...")
    
    # Test search
    query = "AI investment trends Q4 2024"
    print(f"\n🔍 Testing search for: '{query}'")
    
    try:
        results = search_web(query, max_results=3)
        
        if results:
            print(f"\n✅ Search successful! Found {len(results)} results:\n")
            
            for i, result in enumerate(results, 1):
                print(f"{i}. {result.get('title', 'No title')}")
                print(f"   URL: {result.get('url', result.get('link', 'No URL'))}")
                print(f"   Snippet: {result.get('snippet', 'No snippet')[:100]}...")
                print(f"   Source: {result.get('source', 'Unknown')}")
                print()
        else:
            print("❌ No results returned")
            
    except Exception as e:
        print(f"❌ Error during search: {e}")

if __name__ == "__main__":
    test_serper()