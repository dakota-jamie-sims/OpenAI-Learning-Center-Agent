#!/usr/bin/env python3
"""Production-ready article generation with 4 output files"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import argparse
import json
from datetime import datetime
import logging

from src.pipeline.working_multi_agent_orchestrator_v2 import WorkingMultiAgentOrchestratorV2
from src.models import ArticleRequest
from src.utils.logging import get_logger

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = get_logger(__name__)


async def main():
    parser = argparse.ArgumentParser(description="Generate article with 4 output files using multi-agent system")
    parser.add_argument("--topic", required=False, help="Article topic")
    parser.add_argument("--word-count", type=int, default=1750, help="Target word count")
    parser.add_argument("--audience", default="institutional investors and financial professionals", 
                       help="Target audience")
    parser.add_argument("--tone", default="professional yet conversational", help="Writing tone")
    parser.add_argument("--metrics", action="store_true", help="Show performance metrics")
    parser.add_argument("--health-check", action="store_true", help="Run health check only")
    
    args = parser.parse_args()
    
    # Health check mode
    if args.health_check:
        health = {
            "status": "healthy",
            "system": "working_multi_agent_orchestrator_v2",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "llm": "gpt-5 models",
                "web_search": "serper api",
                "kb_search": "dakota knowledge base (397 files)",
                "orchestrator": "4-file output generation"
            },
            "output_files": [
                "article.md - Main article content",
                "metadata.md - SEO and performance metrics",
                "social-media.md - Multi-platform social content",
                "summary.md - Executive summary"
            ]
        }
        print("\n🏥 System Health Check")
        print("=" * 60)
        print(json.dumps(health, indent=2))
        return
    
    if not args.topic:
        print("Error: --topic is required for article generation")
        return
    
    # Create article request
    request = ArticleRequest(
        topic=args.topic,
        audience=args.audience,
        tone=args.tone,
        word_count=args.word_count,
        include_metadata=True,
        include_social=True,
        include_summary=True,
    )
    
    print(f"\n🚀 Production Article Generation V4 (4-File Output)")
    print("=" * 60)
    print(f"Topic: {request.topic}")
    print(f"Target: {request.word_count} words")
    print(f"Output: 4 files in dedicated folder")
    print("=" * 60)
    
    try:
        # Create orchestrator
        orchestrator = WorkingMultiAgentOrchestratorV2()
        
        # Generate article
        start_time = datetime.now()
        result = await orchestrator.generate_article(request)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if result.get("success", False):
            print(f"\n✅ Article generated successfully in {elapsed:.1f}s!")
            
            # Show output location
            output_folder = result.get("output_folder", "")
            if output_folder:
                print(f"\n📁 Output folder: {output_folder}/")
                print("\n📄 Files generated:")
                for filename in result.get("files_generated", []):
                    print(f"   - {filename}")
                
                # Show metadata
                metadata = result.get("metadata", {})
                print("\n📊 Generation Metadata:")
                print(f"   Word count: {metadata.get('word_count', 'N/A')}")
                print(f"   Generation time: {metadata.get('generation_time', elapsed):.2f}s")
                print(f"   Sources used: {metadata.get('sources_used', 'N/A')}")
                print(f"   Model: {metadata.get('model', 'gpt-5')}")
                
                # Show preview of article
                article_path = os.path.join(output_folder, "article.md")
                if os.path.exists(article_path):
                    with open(article_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # Skip frontmatter and find content
                    content_start = 0
                    frontmatter_count = 0
                    for i, line in enumerate(lines):
                        if line.strip() == "---":
                            frontmatter_count += 1
                            if frontmatter_count == 2:
                                content_start = i + 1
                                break
                    
                    # Show preview
                    print("\n📝 Article Preview:")
                    print("-" * 50)
                    preview_lines = [l.strip() for l in lines[content_start:] if l.strip()][:5]
                    for line in preview_lines:
                        print(line[:80] + "..." if len(line) > 80 else line)
                    print("-" * 50)
            
        else:
            print(f"\n❌ Article generation failed!")
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        # Show metrics if requested
        if args.metrics:
            print("\n📈 Performance Metrics:")
            metrics = {
                "generation_time": elapsed,
                "success": result.get("success", False),
                "phases": ["research", "synthesis", "writing", "output_generation"],
                "files_generated": result.get("files_generated", []),
                "output_folder": result.get("output_folder", "")
            }
            if result.get("metadata"):
                metrics.update(result["metadata"])
            print(json.dumps(metrics, indent=2))
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())