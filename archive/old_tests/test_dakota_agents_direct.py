#!/usr/bin/env python3
"""Test Dakota agents directly to verify enhanced matching"""

import asyncio
import json
from src.agents.dakota_agents.kb_researcher import DakotaKBResearcher
from src.agents.dakota_agents.content_writer import DakotaContentWriter
from src.agents.dakota_agents.fact_checker_v2 import DakotaFactCheckerV2
from src.agents.dakota_agents.seo_specialist import DakotaSEOSpecialist
from src.agents.dakota_agents.summary_writer import DakotaSummaryWriter

async def test_dakota_pipeline():
    """Test the Dakota agents pipeline with enhanced matching"""
    
    topic = "venture capital trends 2025"
    print(f"🚀 Testing Dakota agents for: {topic}")
    print("=" * 60)
    
    # 1. KB Research with enhanced matching
    print("\n1️⃣ KB Research Phase...")
    kb_researcher = DakotaKBResearcher()
    kb_result = await kb_researcher.execute({"topic": topic})
    
    if kb_result["success"]:
        print(f"   ✅ Found {len(kb_result['data']['sources'])} sources")
        print(f"   ✅ Found {len(kb_result['data']['related_articles'])} related articles")
        
        print("\n   📰 Related Articles (Enhanced):")
        for article in kb_result['data']['related_articles']:
            print(f"      - {article['title']}")
            print(f"        {article['relevance']}")
    
    # 2. Content Writing
    print("\n2️⃣ Content Writing Phase...")
    writer = DakotaContentWriter()
    
    # Prepare writing context
    writing_context = {
        "topic": topic,
        "audience": "institutional investors",
        "tone": "professional yet conversational",
        "word_count": 500,  # Shorter for testing
        "kb_insights": kb_result['data']['insights'],
        "sources": kb_result['data']['sources'],
        "related_articles": kb_result['data']['related_articles']
    }
    
    write_result = await writer.execute(writing_context)
    
    if write_result["success"]:
        article = write_result['data']['article']
        print(f"   ✅ Article written: {len(article.split())} words")
        
        # 3. Fact Checking
        print("\n3️⃣ Fact Checking Phase...")
        fact_checker = DakotaFactCheckerV2()
        fact_result = await fact_checker.execute({
            "content": article,
            "sources": write_result['data'].get('sources', kb_result['data']['sources'])
        })
        
        if fact_result["success"] and fact_result['data']['approved']:
            print(f"   ✅ Article approved!")
            print(f"   ✅ Verification rate: {fact_result['data']['verification_rate']}%")
            
            # 4. SEO Metadata Generation
            print("\n4️⃣ SEO Metadata Generation Phase...")
            seo_specialist = DakotaSEOSpecialist()
            seo_result = await seo_specialist.execute({
                "article": article,
                "topic": topic
            })
            
            if seo_result["success"]:
                print("   ✅ SEO metadata generated!")
                
                # Save outputs
                print("\n5️⃣ Saving outputs...")
                import os
                output_dir = "output/dakota_test"
                os.makedirs(output_dir, exist_ok=True)
                
                # Save article
                with open(f"{output_dir}/article.md", 'w', encoding='utf-8') as f:
                    f.write(article)
                print(f"   📄 Article saved to {output_dir}/article.md")
                
                # Save metadata with related articles
                metadata = {
                    "seo": seo_result['data'],
                    "related_articles": kb_result['data']['related_articles'],
                    "sources": write_result['data'].get('sources', kb_result['data']['sources'])
                }
                with open(f"{output_dir}/metadata.json", 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, indent=2, ensure_ascii=False)
                print(f"   📄 Metadata saved to {output_dir}/metadata.json")
                
                # Print related articles
                print("\n📰 Related Articles (with enhanced matching):")
                for article in kb_result['data']['related_articles']:
                    print(f"   - {article['title']}")
                    print(f"     URL: {article['url']}")
                
        else:
            print(f"   ❌ Fact check failed: {fact_result['data'].get('rejection_reason', 'Unknown')}")
    else:
        print(f"   ❌ Writing failed: {write_result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    asyncio.run(test_dakota_pipeline())