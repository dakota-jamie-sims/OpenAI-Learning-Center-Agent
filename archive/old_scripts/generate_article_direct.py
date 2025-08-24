#!/usr/bin/env python3
"""
Direct article generation using Dakota agents with enhanced matching
"""

import asyncio
import json
import os
from datetime import datetime
from src.agents.dakota_agents.orchestrator import DakotaOrchestrator

async def generate_article(topic: str, output_dir: str = "output"):
    """Generate article directly using Dakota orchestrator"""
    print(f"\n🚀 Generating article: {topic}")
    print("=" * 60)
    
    orchestrator = DakotaOrchestrator()
    
    try:
        # Execute generation
        from src.models import ArticleRequest
        
        request = ArticleRequest(
            topic=topic,
            word_count=1750,
            audience="institutional investors and financial professionals",
            tone="professional yet conversational"
        )
        
        result = await orchestrator.execute({
            "request": request
        })
        
        if result["success"]:
            # Create output directory
            timestamp = datetime.now().strftime("%Y-%m-%d")
            topic_slug = topic.lower().replace(" ", "-")
            article_dir = os.path.join(output_dir, f"{timestamp}-{topic_slug}")
            os.makedirs(article_dir, exist_ok=True)
            
            # Save outputs
            outputs = result["data"]["outputs"]
            
            # Save article
            article_path = os.path.join(article_dir, f"{topic_slug}-article.md")
            with open(article_path, 'w', encoding='utf-8') as f:
                f.write(outputs["article"]["content"])
            print(f"\n✅ Article saved to: {article_path}")
            
            # Save metadata
            metadata_path = os.path.join(article_dir, f"{topic_slug}-metadata.md")
            with open(metadata_path, 'w', encoding='utf-8') as f:
                f.write(outputs["metadata"]["content"])
            print(f"✅ Metadata saved to: {metadata_path}")
            
            # Print related articles to verify enhanced matching
            print("\n📰 Related Articles (Enhanced Matching):")
            # Parse metadata to find related articles
            metadata_lines = outputs["metadata"]["content"].split('\n')
            in_related = False
            for line in metadata_lines:
                if "Related Learning Center Articles" in line:
                    in_related = True
                elif in_related and line.strip() and not line.startswith('#'):
                    if "URL:" in line:
                        print(f"   {line.strip()}")
                elif in_related and line.startswith('#'):
                    break
            
            # Save other outputs
            for output_type in ["social_media", "summary"]:
                if output_type in outputs:
                    file_path = os.path.join(article_dir, f"{topic_slug}-{output_type.replace('_', '-')}.md")
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(outputs[output_type]["content"])
                    print(f"✅ {output_type.title()} saved to: {file_path}")
            
            print(f"\n✨ Article generation complete!")
            print(f"   Word count: {outputs['article']['word_count']}")
            print(f"   Generation time: {result['data'].get('total_time', 'N/A')}")
            
        else:
            print(f"\n❌ Generation failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Generate the 4 requested articles"""
    topics = [
        "venture capital trends 2025",
        "private credit emerging managers",
        "hedge fund strategies 2025",
        "real estate investment trusts analysis"
    ]
    
    for topic in topics:
        await generate_article(topic)
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())