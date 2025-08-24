#!/usr/bin/env python3
"""Test KB researcher with enhanced article matching"""

import asyncio
from src.agents.dakota_agents.kb_researcher import DakotaKBResearcher

async def test_kb_researcher():
    """Test the KB researcher enhanced matching"""
    kb_researcher = DakotaKBResearcher()
    
    # Check if ArticleMatcher loaded
    print(f"ArticleMatcher loaded: {kb_researcher.article_matcher is not None}")
    
    # Test research
    test_topic = "venture capital trends 2025"
    print(f"\n🔍 Testing KB research for: {test_topic}")
    
    result = await kb_researcher.execute({
        "topic": test_topic
    })
    
    if result["success"]:
        print(f"\n✅ KB research successful!")
        print(f"   Sources found: {len(result['data']['sources'])}")
        print(f"   Related articles: {len(result['data']['related_articles'])}")
        
        print("\n📰 Related Articles (with enhanced matching):")
        for article in result['data']['related_articles']:
            print(f"\n   Title: {article['title']}")
            print(f"   URL: {article['url']}")
            print(f"   Relevance: {article['relevance']}")
            
        # Test topic recommendations
        print("\n💡 Topic Recommendations:")
        recommendations = kb_researcher.get_topic_recommendations(
            current_market_trends=["AI in Investment Management", "ESG Integration"]
        )
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"\n   {i}. {rec['topic']}")
            print(f"      Rationale: {rec['rationale']}")
            print(f"      Priority: {rec['priority']}")
    else:
        print(f"\n❌ KB research failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(test_kb_researcher())