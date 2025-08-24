#!/usr/bin/env python3
"""Test article generation with improved source system"""

import asyncio
import sys
import os

# Add project root to Python path  
sys.path.append(os.path.abspath('.'))

from src.models import ArticleRequest
from src.agents.dakota_agents.orchestrator_production import DakotaProductionOrchestrator

async def generate_test_article():
    """Generate a test article to demonstrate improved source system"""
    
    topic = "Private Credit Opportunities 2025"
    word_count = 2000  # Should get ~20 sources
    
    print(f"🚀 Generating article: {topic}")
    print(f"📝 Target word count: {word_count}")
    print("=" * 60)
    
    # Create request
    request = ArticleRequest(
        topic=topic,
        audience="Institutional Investors",
        tone="Professional/Educational",
        word_count=word_count
    )
    
    # Initialize orchestrator
    orchestrator = DakotaProductionOrchestrator()
    
    # Execute pipeline
    try:
        result = await orchestrator.execute({"request": request})
        
        if result.get("success"):
            data = result.get("data", {})
            output_folder = data.get("output_folder", "Unknown")
            word_count_actual = data.get("word_count", 0)
            sources_verified = data.get("sources_verified", 0)
            generation_time = data.get("generation_time", 0)
            
            print(f"\n✅ Article generated successfully!")
            print(f"📁 Output folder: {output_folder}")
            print(f"📝 Word count: {word_count_actual}")
            print(f"🔍 Sources verified: {sources_verified}")
            print(f"⏱️  Generation time: {generation_time:.2f}s")
            
            # Check the metadata file for source count
            metadata_file = f"{output_folder}/private-credit-metadata.md"
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    metadata_content = f.read()
                    
                # Count sources (excluding KB source if present)
                source_count = metadata_content.count("**URL:**") or metadata_content.count("- URL:")
                kb_sources = metadata_content.count("dakota.com/learning-center/dakota-knowledge-base")
                web_sources = source_count - kb_sources
                
                print(f"\n📊 Source Analysis:")
                print(f"   Total sources: {source_count}")
                print(f"   Web sources: {web_sources}")
                print(f"   KB sources: {kb_sources} (should be 0)")
                
                # Show first few sources
                print(f"\n📰 Sample Sources:")
                lines = metadata_content.split('\n')
                source_lines = [l for l in lines if '**URL:**' in l or '- URL:' in l]
                for i, line in enumerate(source_lines[:5], 1):
                    url = line.split('URL:')[-1].strip()
                    print(f"   {i}. {url}")
                    
        else:
            print(f"\n❌ Article generation failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(generate_test_article())