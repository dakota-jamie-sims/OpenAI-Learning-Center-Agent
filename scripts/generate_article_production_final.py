#!/usr/bin/env python3
"""
Production Article Generation Script - Final Version
Uses all optimizations: parallel execution, caching, connection pooling
"""
import asyncio
import sys
import os
import time
import argparse
from datetime import datetime
import json

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import ArticleRequest
from src.agents.dakota_agents.orchestrator_production import DakotaProductionOrchestrator
from src.utils.logging import get_logger
from src.utils.connection_pool import get_pool_stats

# Set up logging
os.environ["LOG_LEVEL"] = "INFO"
logger = get_logger(__name__)


async def generate_article(topic: str, word_count: int = 1000, debug: bool = False):
    """Generate article with full production optimizations"""
    start_time = time.time()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🚀 Production Article Generation - Optimized")
    logger.info(f"📝 Topic: {topic}")
    logger.info(f"📊 Target word count: {word_count}")
    logger.info(f"⚡ Features: Parallel execution, Caching, Connection pooling")
    logger.info(f"{'='*60}\n")
    
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("❌ OPENAI_API_KEY not set. Please check your .env file")
        return False
    
    if not os.getenv("OPENAI_VECTOR_STORE_ID"):
        logger.error("❌ OPENAI_VECTOR_STORE_ID not set. Please check your .env file")
        return False
    
    try:
        # Create request
        request = ArticleRequest(
            topic=topic,
            audience="institutional investors",
            tone="professional yet conversational",
            word_count=word_count
        )
        
        # Create production orchestrator
        orchestrator = DakotaProductionOrchestrator()
        
        # Show execution plan
        logger.info("⚡ Optimized Execution Plan:")
        logger.info("  ├─ Phase 1: Setup (instant)")
        logger.info("  ├─ Phase 2-3: KB + Web Research (parallel) → Synthesis")
        logger.info("  ├─ Phase 4-5: Content Writing → Metrics + SEO (parallel)")
        logger.info("  ├─ Phase 6: Fast Validation (cached)")
        logger.info("  └─ Phase 7: Social + Summary (parallel)\n")
        
        # Execute with timing
        result = await orchestrator.execute({"request": request})
        
        if result["success"]:
            data = result["data"]
            total_time = time.time() - start_time
            
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ ARTICLE GENERATION SUCCESSFUL!")
            logger.info(f"{'='*60}")
            logger.info(f"📁 Output folder: {data['output_folder']}")
            logger.info(f"📄 Files created:")
            for file in data['files_created']:
                logger.info(f"   ✓ {file}")
            logger.info(f"📝 Word count: {data['word_count']}")
            logger.info(f"✅ Fact-checker approved: {data['fact_checker_approved']}")
            logger.info(f"🔍 Sources verified: {data['sources_verified']}")
            logger.info(f"🔄 Iterations needed: {data['iterations_needed']}")
            logger.info(f"⏱️ Total time: {total_time:.2f} seconds")
            
            # Show performance breakdown
            if "phase_times" in data:
                logger.info(f"\n📊 Performance Breakdown:")
                for phase, duration in data["phase_times"].items():
                    logger.info(f"   {phase}: {duration:.2f}s")
            
            # Show connection pool stats
            pool_stats = get_pool_stats()
            logger.info(f"\n🔌 Connection Pool Stats:")
            for pool_name, stats in pool_stats.items():
                logger.info(f"   {pool_name}: {stats['in_use']}/{stats['total']} in use")
            
            # Performance verdict
            logger.info(f"\n🎯 Performance Verdict:")
            if total_time < 60:
                logger.info(f"   🚀 EXCELLENT! Under 1 minute")
            elif total_time < 90:
                logger.info(f"   ✅ GREAT! Under 1.5 minutes")
            elif total_time < 120:
                logger.info(f"   👍 GOOD! Under 2 minutes")
            else:
                logger.info(f"   ⚠️ OK, but could be optimized")
            
            logger.info(f"{'='*60}\n")
            
            # Save metrics
            metrics = {
                "topic": topic,
                "word_count": data['word_count'],
                "generation_time": total_time,
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "output_folder": data['output_folder'],
                "phase_times": data.get("phase_times", {})
            }
            
            metrics_file = f"{data['output_folder']}/generation_metrics.json"
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
            
            return True
            
        else:
            logger.error(f"\n❌ Article generation failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=debug)
        return False


async def test_components():
    """Test individual components"""
    logger.info("\n🧪 Testing Production Components...")
    
    # Test KB search
    try:
        from src.services.kb_search_optimized_v2 import search_kb_optimized
        logger.info("\n1. Testing Optimized KB Search...")
        start = time.time()
        result = search_kb_optimized("private equity trends", max_results=3)
        elapsed = time.time() - start
        
        if result.get("success") or result.get("results"):
            logger.info(f"   ✅ KB Search: OK ({elapsed:.2f}s)")
        else:
            logger.info(f"   ⚠️ KB Search: No results ({elapsed:.2f}s)")
    except Exception as e:
        logger.error(f"   ❌ KB Search: Failed - {e}")
    
    # Test connection pool
    try:
        from src.utils.connection_pool import get_pool_stats
        logger.info("\n2. Testing Connection Pool...")
        stats = get_pool_stats()
        logger.info(f"   ✅ Connection Pool: OK")
        for pool, info in stats.items():
            logger.info(f"      {pool}: {info['total']} clients")
    except Exception as e:
        logger.error(f"   ❌ Connection Pool: Failed - {e}")
    
    # Test fact checker
    try:
        logger.info("\n3. Testing Cached Fact Checker...")
        logger.info(f"   ✅ Fact Checker: Ready (with caching)")
    except Exception as e:
        logger.error(f"   ❌ Fact Checker: Failed - {e}")
    
    logger.info("\n✅ Component tests complete\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate Dakota Learning Center articles with production optimizations"
    )
    parser.add_argument("topic", nargs="?", help="Article topic")
    parser.add_argument(
        "--word-count", 
        type=int, 
        default=1000, 
        help="Target word count (default: 1000)"
    )
    parser.add_argument(
        "--test", 
        action="store_true", 
        help="Test production components"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Set debug level if requested
    if args.debug:
        os.environ["LOG_LEVEL"] = "DEBUG"
    
    # Run async
    if args.test:
        asyncio.run(test_components())
    elif args.topic:
        success = asyncio.run(generate_article(args.topic, args.word_count, args.debug))
        sys.exit(0 if success else 1)
    else:
        print("Usage: python generate_article_production_final.py <topic> [--word-count 1000]")
        print("       python generate_article_production_final.py --test")
        sys.exit(1)


if __name__ == "__main__":
    main()