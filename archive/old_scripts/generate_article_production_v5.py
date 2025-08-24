#!/usr/bin/env python3
"""
Production Article Generation Script V5
Fully optimized with all production features
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
from src.agents.dakota_agents.orchestrator_v2 import DakotaOrchestratorV2
from src.services.openai_connection_pool import initialize_agent_pools, get_connection_pool
from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


async def initialize_system():
    """Initialize all production systems"""
    logger.info("Initializing production systems...")
    
    # Initialize connection pools
    await initialize_agent_pools()
    logger.info("✅ Connection pools initialized")
    
    # Warm up KB search
    try:
        from src.services.kb_search_production_v2 import get_production_kb_searcher
        searcher = await get_production_kb_searcher()
        # Do a test search to warm cache
        await searcher.search("test warmup", max_results=1)
        logger.info("✅ KB search service warmed up")
    except Exception as e:
        logger.warning(f"KB search warmup failed: {e}")
    
    # Check Redis connection
    try:
        if searcher.redis_client:
            searcher.redis_client.ping()
            logger.info("✅ Redis cache connected")
        else:
            logger.info("ℹ️ Running without Redis (in-memory cache only)")
    except:
        logger.info("ℹ️ Redis not available, using in-memory cache")
    
    # Check vector store
    vector_store_id = os.getenv("OPENAI_VECTOR_STORE_ID")
    if vector_store_id:
        logger.info(f"✅ Vector store configured: {vector_store_id}")
    else:
        logger.error("❌ Vector store ID not configured!")
        sys.exit(1)


async def generate_article(topic: str, word_count: int = 1000):
    """Generate article with full production features"""
    start_time = time.time()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🚀 Starting Production Article Generation V5")
    logger.info(f"📝 Topic: {topic}")
    logger.info(f"📊 Target word count: {word_count}")
    logger.info(f"{'='*60}\n")
    
    try:
        # Initialize system
        await initialize_system()
        
        # Create request
        request = ArticleRequest(
            topic=topic,
            audience="institutional investors",
            tone="professional yet conversational",
            word_count=word_count
        )
        
        # Create orchestrator
        orchestrator = DakotaOrchestratorV2()
        
        # Execute with progress tracking
        logger.info("⚡ Executing optimized parallel workflow...")
        result = await orchestrator.execute({"request": request})
        
        if result["success"]:
            data = result["data"]
            total_time = time.time() - start_time
            
            logger.info(f"\n{'='*60}")
            logger.info(f"✅ ARTICLE GENERATION SUCCESSFUL!")
            logger.info(f"{'='*60}")
            logger.info(f"📁 Output folder: {data['output_folder']}")
            logger.info(f"📄 Files created: {len(data['files_created'])}")
            for file in data['files_created']:
                logger.info(f"   - {file}")
            logger.info(f"📝 Word count: {data['word_count']}")
            logger.info(f"✅ Fact-checker approved: {data['fact_checker_approved']}")
            logger.info(f"🔍 Sources verified: {data['sources_verified']}")
            logger.info(f"🔄 Iterations needed: {data['iterations_needed']}")
            logger.info(f"⏱️ Total time: {total_time:.2f} seconds")
            logger.info(f"{'='*60}\n")
            
            # Save metrics
            metrics = {
                "topic": topic,
                "word_count": data['word_count'],
                "generation_time": total_time,
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "output_folder": data['output_folder']
            }
            
            with open(f"{data['output_folder']}/generation_metrics.json", 'w') as f:
                json.dump(metrics, f, indent=2)
            
        else:
            logger.error(f"\n❌ Article generation failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)
        raise
    
    finally:
        # Show connection pool stats
        try:
            pool = await get_connection_pool()
            for pool_name in ["search", "content", "orchestrator", "analysis"]:
                stats = await pool.get_pool_stats(pool_name)
                logger.info(f"Pool '{pool_name}': {stats['busy_clients']}/{stats['total_clients']} busy")
        except:
            pass


async def health_check():
    """Run system health check"""
    logger.info("Running system health check...")
    
    try:
        # Check connection pools
        pool = await get_connection_pool()
        health = await pool.health_check()
        
        logger.info(f"Connection pools: {health['status']}")
        for pool_name, stats in health['pools'].items():
            logger.info(f"  - {pool_name}: {stats['available_clients']}/{stats['total_clients']} available")
        
        # Check KB search
        from src.services.kb_search_production_v2 import get_production_kb_searcher
        searcher = await get_production_kb_searcher()
        test_result = await searcher.search("health check", max_results=1)
        
        if test_result['success']:
            logger.info(f"KB Search: ✅ Working (response time: {test_result.get('search_time', 0):.2f}s)")
        else:
            logger.info(f"KB Search: ❌ Failed - {test_result.get('error', 'Unknown error')}")
        
        logger.info(f"Circuit breaker state: {searcher.circuit_breaker.state}")
        
        # Check cache
        cache_entries = len(searcher.memory_cache)
        logger.info(f"Cache entries: {cache_entries}")
        
        # Check Redis
        if searcher.redis_client:
            try:
                searcher.redis_client.ping()
                logger.info("Redis: ✅ Connected")
            except:
                logger.info("Redis: ❌ Not connected")
        else:
            logger.info("Redis: Not configured")
        
        return True
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Generate Dakota Learning Center articles with production optimizations")
    parser.add_argument("topic", nargs="?", help="Article topic")
    parser.add_argument("--word-count", type=int, default=1000, help="Target word count (default: 1000)")
    parser.add_argument("--health-check", action="store_true", help="Run system health check")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    # Setup logging
    if args.debug:
        setup_logging(level="DEBUG")
    else:
        setup_logging(level="INFO")
    
    # Run async
    if args.health_check:
        asyncio.run(health_check())
    elif args.topic:
        asyncio.run(generate_article(args.topic, args.word_count))
    else:
        print("Usage: python generate_article_production_v5.py <topic> [--word-count 1000]")
        print("       python generate_article_production_v5.py --health-check")
        sys.exit(1)


if __name__ == "__main__":
    main()