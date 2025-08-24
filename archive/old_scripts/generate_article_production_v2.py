#!/usr/bin/env python3
"""Production-ready article generation using existing multi-agent system with enhancements"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import argparse
import json
import time
from datetime import datetime
import logging

from src.agents.orchestrator import create_article_with_multi_agent_system
from src.models import ArticleRequest
from src.utils.logging import get_logger
from src.config_production import TIMEOUTS, FEATURE_FLAGS
from src.utils.rate_limiter import init_default_limiters
from src.utils.circuit_breaker import circuit_manager

# Set production environment
os.environ["ENVIRONMENT"] = "production"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = get_logger(__name__)


async def generate_with_production_safeguards(request: ArticleRequest) -> dict:
    """Wrap the existing multi-agent system with production safeguards"""
    start_time = time.time()
    
    try:
        # Apply overall timeout
        result = await asyncio.wait_for(
            asyncio.to_thread(
                create_article_with_multi_agent_system,
                request
            ),
            timeout=TIMEOUTS.get("total_generation", 300)
        )
        
        elapsed = time.time() - start_time
        
        # Add timing metadata
        if isinstance(result, dict):
            if "metadata" not in result:
                result["metadata"] = {}
            result["metadata"]["generation_time"] = elapsed
            result["metadata"]["circuit_breaker_states"] = circuit_manager.get_states()
        
        return result
        
    except asyncio.TimeoutError:
        logger.error(f"Article generation timeout after {TIMEOUTS.get('total_generation', 300)}s")
        return {
            "success": False,
            "error": f"Generation timeout after {TIMEOUTS.get('total_generation', 300)} seconds",
            "article": "",
            "metadata": {"elapsed": time.time() - start_time}
        }
    except Exception as e:
        logger.error(f"Article generation error: {e}")
        return {
            "success": False,
            "error": str(e),
            "article": "",
            "metadata": {"error_type": type(e).__name__}
        }


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
    
    # Initialize rate limiters
    init_default_limiters()
    
    # Health check mode
    if args.health_check:
        health = {
            "status": "healthy",
            "circuit_breakers": circuit_manager.get_states(),
            "timestamp": datetime.now().isoformat(),
            "environment": "production",
            "features": FEATURE_FLAGS
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
    
    print(f"\n🚀 Production Article Generation V2")
    print("=" * 50)
    print(f"Topic: {request.topic}")
    print(f"Target: {request.word_count} words")
    print(f"Using: Multi-agent system with production safeguards")
    print("=" * 50)
    
    try:
        # Generate article
        start_time = datetime.now()
        result = await generate_with_production_safeguards(request)
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
                    output_path = f"output/articles/prod_v2_{args.topic.replace(' ', '_').lower()}_{timestamp}.md"
                
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "w") as f:
                    f.write(article_content)
                
                print(f"📄 Saved to: {output_path}")
                
                # Show metadata
                if result.get("metadata"):
                    metadata = result["metadata"]
                    print("\n📊 Generation Metadata:")
                    print(f"   Word count: {metadata.get('word_count', len(article_content.split()))}")
                    print(f"   Generation time: {metadata.get('generation_time', elapsed):.2f}s")
                    if "quality_scores" in metadata:
                        print(f"   Quality score: {metadata['quality_scores'].get('overall', 'N/A')}")
            
        else:
            print(f"\n❌ Article generation failed!")
            print(f"   Error: {result.get('error', 'Unknown error')}")
        
        # Show metrics if requested
        if args.metrics:
            print("\n📈 Performance Metrics:")
            metrics = {
                "generation_time": elapsed,
                "success": result.get("success", False),
                "circuit_breaker_states": circuit_manager.get_states(),
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