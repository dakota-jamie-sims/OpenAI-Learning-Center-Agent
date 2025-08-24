#!/usr/bin/env python3
"""Test the enhanced web source system"""

import asyncio
import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath('.'))

from src.agents.dakota_agents.web_researcher import DakotaWebResearcher

async def test_web_sources():
    """Test the enhanced web researcher for source count"""
    
    print("🔍 Testing Enhanced Web Source System")
    print("=" * 50)
    
    # Test topics with different word counts
    test_cases = [
        {"topic": "Real Estate Investment Trusts 2025", "word_count": 1750},  # Should get 15 sources
        {"topic": "Private Equity Trends 2025", "word_count": 2500},         # Should get 20 sources  
        {"topic": "Hedge Fund Strategies 2025", "word_count": 3000},         # Should get 25 sources
    ]
    
    researcher = DakotaWebResearcher()
    
    for i, test_case in enumerate(test_cases, 1):
        topic = test_case["topic"]
        word_count = test_case["word_count"]
        
        print(f"\n{i}️⃣ Testing: {topic} ({word_count} words)")
        print("-" * 40)
        
        try:
            # Test web research
            result = await researcher.execute({
                "topic": topic,
                "word_count": word_count
            })
            
            if result.get("success"):
                data = result.get("data", {})
                sources = data.get("sources", [])
                queries = data.get("search_queries", [])
                
                print(f"   ✅ Search queries: {len(queries)}")
                print(f"   ✅ Sources found: {len(sources)}")
                print(f"   📊 Expected sources: {15 if word_count < 2500 else 20 if word_count < 3000 else 25}")
                
                # Show source breakdown by authority
                tier1_count = sum(1 for s in sources if s.get("authority", 0) == 3)
                tier2_count = sum(1 for s in sources if s.get("authority", 0) == 2) 
                tier3_count = sum(1 for s in sources if s.get("authority", 0) == 1)
                
                print(f"   📈 Authority Tier 1 (Gov/IMF): {tier1_count}")
                print(f"   📈 Authority Tier 2 (Bloomberg/WSJ): {tier2_count}")
                print(f"   📈 Authority Tier 3 (Other): {tier3_count}")
                
                # Show sample sources
                print(f"\n   📰 Sample Sources:")
                for j, source in enumerate(sources[:5], 1):
                    title = source.get("title", "No title")[:60]
                    url_domain = source.get("url", "").split("//")[-1].split("/")[0]
                    authority = source.get("authority", 0)
                    print(f"      {j}. {title}... ({url_domain}) [Tier {authority}]")
                    
                # Check if we hit our target
                expected = 15 if word_count < 2500 else 20 if word_count < 3000 else 25
                if len(sources) >= expected * 0.6:  # At least 60% of target
                    print(f"   ✅ SUCCESS: Got {len(sources)}/{expected} sources")
                else:
                    print(f"   ⚠️  PARTIAL: Got {len(sources)}/{expected} sources")
                    
            else:
                print(f"   ❌ Web research failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            
    print("\n" + "=" * 50)
    print("✅ Web source testing complete!")

if __name__ == "__main__":
    asyncio.run(test_web_sources())