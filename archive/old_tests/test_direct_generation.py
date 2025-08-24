#!/usr/bin/env python3
"""Direct test of article generation system"""

import asyncio
import sys
import os

# Add project root to Python path
sys.path.append(os.path.abspath('.'))

from src.agents.dakota_agents.web_researcher import DakotaWebResearcher
from src.agents.dakota_agents.research_synthesizer import DakotaResearchSynthesizer
from src.agents.dakota_agents.content_writer import DakotaContentWriter
from src.agents.dakota_agents.seo_specialist import DakotaSEOSpecialist
from src.agents.dakota_agents.social_promoter import DakotaSocialPromoter

async def test_direct_generation():
    """Test article generation with direct agent calls"""
    
    topic = "Private Credit Opportunities 2025"
    output_dir = "output/2025-08-22-test-private-credit"
    
    print(f"🚀 Direct Article Generation Test")
    print(f"📝 Topic: {topic}")
    print("=" * 60)
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Step 1: Web Research (skip KB)
    print("\n1️⃣ Web Research...")
    web_researcher = DakotaWebResearcher()
    web_result = await web_researcher.execute({
        "topic": topic,
        "word_count": 1750
    })
    
    if web_result.get("success"):
        sources = web_result.get("data", {}).get("sources", [])
        print(f"   ✅ Found {len(sources)} web sources")
        for i, source in enumerate(sources[:5], 1):
            print(f"   {i}. {source.get('title', 'No title')[:50]}...")
    else:
        print(f"   ❌ Web research failed")
        return
    
    # Step 2: Synthesis
    print("\n2️⃣ Research Synthesis...")
    synthesizer = DakotaResearchSynthesizer()
    synthesis_result = await synthesizer.execute({
        "topic": topic,
        "audience": "Institutional Investors",
        "tone": "Professional/Educational",
        "word_count": 1750,
        "research_data": {
            "sources": sources,
            "insights": [web_result.get("data", {}).get("summary", "")]
        }
    })
    
    if synthesis_result.get("success"):
        print(f"   ✅ Synthesis complete")
    else:
        print(f"   ❌ Synthesis failed")
        return
    
    # Step 3: Content Writing
    print("\n3️⃣ Content Writing...")
    writer = DakotaContentWriter()
    article_path = f"{output_dir}/private-credit-article.md"
    
    write_result = await writer.execute({
        "topic": topic,
        "audience": "Institutional Investors",
        "tone": "Professional/Educational",
        "word_count": 1750,
        "synthesis": synthesis_result.get("data", {}),
        "output_file": article_path
    })
    
    if write_result.get("success"):
        print(f"   ✅ Article written to {article_path}")
        word_count = write_result.get("data", {}).get("word_count", 0)
        print(f"   📝 Word count: {word_count}")
    else:
        print(f"   ❌ Writing failed")
        return
    
    # Step 4: SEO Metadata
    print("\n4️⃣ SEO Metadata...")
    seo = DakotaSEOSpecialist()
    metadata_path = f"{output_dir}/private-credit-metadata.md"
    
    # Use real Dakota article URLs for related articles
    related_articles = [
        {
            "title": "Trends in Private Credit: Getting the Full Story",
            "url": "https://www.dakota.com/resources/blog/trends-in-private-credit-getting-the-full-story",
            "description": "Deep dive into private credit market dynamics"
        },
        {
            "title": "Direct Lending and Middle Market Private Credit",
            "url": "https://www.dakota.com/resources/blog/direct-lending-middle-market-private-credit",
            "description": "Analysis of direct lending opportunities"
        },
        {
            "title": "Private Credit Market Update",
            "url": "https://www.dakota.com/insights/private-credit-market-update",
            "description": "Latest trends and opportunities in private credit"
        }
    ]
    
    seo_result = await seo.execute({
        "topic": topic,
        "article_file": article_path,
        "output_file": metadata_path,
        "sources": sources,
        "related_articles": related_articles
    })
    
    if seo_result.get("success"):
        print(f"   ✅ Metadata written to {metadata_path}")
        print(f"   🔗 Sources included: {seo_result.get('data', {}).get('sources_included', 0)}")
    else:
        print(f"   ❌ SEO failed")
    
    # Step 5: Social Media (ALWAYS generate)
    print("\n5️⃣ Social Media Content...")
    social = DakotaSocialPromoter()
    social_path = f"{output_dir}/private-credit-social.md"
    
    social_result = await social.execute({
        "topic": topic,
        "article_file": article_path,
        "output_file": social_path
    })
    
    if social_result.get("success"):
        print(f"   ✅ Social media written to {social_path}")
    else:
        print(f"   ⚠️  Social media failed - creating fallback")
        # Create fallback social content
        fallback_social = f"""# Social Media Content

## LinkedIn Post
📈 New insights on Private Credit Opportunities for 2025! Our latest analysis explores key trends institutional investors need to know.

Read the full article: [Link]

#PrivateCredit #InstitutionalInvesting #AlternativeInvestments

## Twitter Thread
1/ 🚀 Private Credit in 2025: What institutional investors need to know

2/ Key opportunities emerging in the market...

3/ Read our complete analysis: [Link]

## Email Newsletter
Subject: Private Credit Opportunities in 2025

Discover the latest trends and opportunities in private credit markets...

Read more: [Link]
"""
        with open(social_path, 'w') as f:
            f.write(fallback_social)
        print(f"   ✅ Fallback social media created")
    
    print("\n" + "=" * 60)
    print(f"✅ Article generation complete!")
    print(f"📁 Files created in: {output_dir}")
    
    # List created files
    files = os.listdir(output_dir)
    print(f"\n📄 Generated files:")
    for file in files:
        size = os.path.getsize(f"{output_dir}/{file}")
        print(f"   - {file} ({size:,} bytes)")

if __name__ == "__main__":
    asyncio.run(test_direct_generation())