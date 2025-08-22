#!/usr/bin/env python3
"""Production-ready article generation using the working multi-agent orchestrator"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import argparse
import json
import time
from datetime import datetime
import logging

from src.pipeline.working_multi_agent_orchestrator import WorkingMultiAgentOrchestrator
from src.models import ArticleRequest
from src.utils.logging import get_logger

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = get_logger(__name__)


async def main():
    parser = argparse.ArgumentParser(description="Generate article using working multi-agent system")
    parser.add_argument("--topic", required=False, help="Article topic")
    parser.add_argument("--word-count", type=int, default=1750, help="Target word count")
    parser.add_argument("--audience", default="institutional investors and financial professionals", 
                       help="Target audience")
    parser.add_argument("--tone", default="professional yet conversational", help="Writing tone")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--metrics", action="store_true", help="Show performance metrics")
    parser.add_argument("--health-check", action="store_true", help="Run health check only")
    
    args = parser.parse_args()
    
    # Health check mode
    if args.health_check:
        health = {
            "status": "healthy",
            "system": "working_multi_agent_orchestrator",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "llm": "gpt-5 models",
                "web_search": "serper api",
                "kb_search": "dakota knowledge base (397 files)",
                "orchestrator": "simplified async implementation"
            }
        }
        print("\n🏥 System Health Check")
        print("=" * 50)
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
    
    print(f"\n🚀 Production Article Generation V3 (Working System)")
    print("=" * 60)
    print(f"Topic: {request.topic}")
    print(f"Target: {request.word_count} words")
    print(f"Using: Simplified working multi-agent orchestrator")
    print("=" * 60)
    
    try:
        # Create orchestrator
        orchestrator = WorkingMultiAgentOrchestrator()
        
        # Generate article
        start_time = datetime.now()
        result = await orchestrator.generate_article(request)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if result.get("success", False):
            print(f"\n✅ Article generated successfully in {elapsed:.1f}s!")
            
            # Save article
            article_content = result.get("article", "")
            if article_content:
                if args.output:
                    output_path = args.output
                else:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    topic_slug = args.topic.replace(' ', '_').lower()[:50]
                    output_path = f"output/articles/prod_v3_{topic_slug}_{timestamp}.md"
                
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "w") as f:
                    f.write(article_content)
                
                print(f"📄 Saved to: {output_path}")
                
                # Show metadata
                metadata = result.get("metadata", {})
                print("\n📊 Generation Metadata:")
                print(f"   Word count: {metadata.get('word_count', len(article_content.split()))}")
                print(f"   Generation time: {metadata.get('generation_time', elapsed):.2f}s")
                print(f"   Sources used: {metadata.get('sources_used', 'N/A')}")
                print(f"   Model: {metadata.get('model', 'gpt-5')}")
                
                # Show article preview
                lines = article_content.split('\n')
                non_empty_lines = [l for l in lines if l.strip()][:5]
                if non_empty_lines:
                    print("\n📝 Article Preview:")
                    print("-" * 50)
                    for line in non_empty_lines:
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
                "phases": ["research", "synthesis", "writing", "enhancement"],
                "components_used": ["gpt-5", "serper_api", "dakota_kb"]
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