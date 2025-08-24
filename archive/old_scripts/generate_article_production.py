#!/usr/bin/env python3
"""Production-ready article generation script"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import argparse
import json
from datetime import datetime

from src.pipeline.production_orchestrator import ProductionOrchestrator
from src.models import ArticleRequest
from src.utils.logging import get_logger
from src.config_production import FEATURE_FLAGS
import logging

# Set production environment
os.environ["ENVIRONMENT"] = "production"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = get_logger(__name__)


async def main():
    parser = argparse.ArgumentParser(description="Generate article using production multi-agent system")
    parser.add_argument("--topic", required=False, help="Article topic")
    parser.add_argument("--word-count", type=int, default=1750, help="Target word count")
    parser.add_argument("--audience", default="institutional investors and financial professionals", 
                       help="Target audience")
    parser.add_argument("--tone", default="professional yet conversational", help="Writing tone")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--metrics", action="store_true", help="Show performance metrics")
    parser.add_argument("--health-check", action="store_true", help="Run health check only")
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = ProductionOrchestrator()
    
    # Health check mode
    if args.health_check:
        health = orchestrator.health_check()
        print("\n🏥 System Health Check")
        print("=" * 50)
        print(json.dumps(health, indent=2))
        return
    
    # Create article request
    request = ArticleRequest(
        topic=args.topic,
        audience=args.audience,
        tone=args.tone,
        word_count=args.word_count,
        include_metadata=True,
        include_social=FEATURE_FLAGS.get("enable_social_media", True),
        include_summary=FEATURE_FLAGS.get("enable_summary", True),
    )
    
    print(f"\n🚀 Production Article Generation")
    print("=" * 50)
    print(f"Topic: {request.topic}")
    print(f"Target: {request.word_count} words")
    print(f"Environment: PRODUCTION")
    print("=" * 50)
    
    try:
        # Generate article
        start_time = datetime.now()
        result = await orchestrator.generate_article_async(request)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if result.success:
            print(f"\n✅ Article generated successfully in {elapsed:.1f}s!")
            
            # Save article
            if args.output:
                output_path = args.output
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"output/articles/prod_{args.topic.replace(' ', '_').lower()}_{timestamp}.md"
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w") as f:
                f.write(result.article)
            
            print(f"📄 Saved to: {output_path}")
            
            # Show metadata
            if result.metadata:
                print("\n📊 Generation Metadata:")
                print(f"   Word count: {result.metadata.get('word_count', 'N/A')}")
                print(f"   Sources used: {result.metadata.get('sources_used', 'N/A')}")
                
                if "phase_timings" in result.metadata:
                    print("\n⏱️  Phase Timings:")
                    for phase, timing in result.metadata["phase_timings"].items():
                        print(f"   {phase}: {timing:.2f}s")
            
        else:
            print(f"\n❌ Article generation failed!")
            print(f"   Error: {result.error}")
            if result.metadata:
                print(f"   Failed phase: {result.metadata.get('failed_phase', 'unknown')}")
        
        # Show metrics if requested
        if args.metrics:
            metrics = orchestrator.get_metrics()
            print("\n📈 Performance Metrics:")
            print(json.dumps(metrics, indent=2))
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())