#!/usr/bin/env python3
"""
Optimized Article Generation Script
Uses existing agents with parallel execution optimizations
"""
import asyncio
import sys
import os
import time
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import ArticleRequest
from src.agents.dakota_agents.orchestrator_v2_working import DakotaOrchestratorV2Working
from src.utils.logging import get_logger, setup_logging

logger = get_logger(__name__)


async def generate_article(topic: str, word_count: int = 1000):
    """Generate article with parallel execution optimizations"""
    start_time = time.time()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🚀 Optimized Article Generation")
    logger.info(f"📝 Topic: {topic}")
    logger.info(f"📊 Target word count: {word_count}")
    logger.info(f"{'='*60}\n")
    
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("❌ OPENAI_API_KEY not set. Please check your .env file")
        return
    
    if not os.getenv("OPENAI_VECTOR_STORE_ID"):
        logger.error("❌ OPENAI_VECTOR_STORE_ID not set. Please check your .env file")
        return
    
    try:
        # Create request
        request = ArticleRequest(
            topic=topic,
            audience="institutional investors",
            tone="professional yet conversational",
            word_count=word_count
        )
        
        # Create orchestrator
        orchestrator = DakotaOrchestratorV2Working()
        
        # Show parallel execution plan
        logger.info("⚡ Parallel Execution Plan:")
        logger.info("  Phase 1: Setup")
        logger.info("  Phase 2-3: KB Research + Web Research (PARALLEL)")
        logger.info("  Phase 4: Content Writing")
        logger.info("  Phase 5: Metrics + SEO Analysis (PARALLEL)")
        logger.info("  Phase 6: Fact Checking")
        logger.info("  Phase 7: Social Media + Summary (PARALLEL)\n")
        
        # Execute
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
            
            # Performance analysis
            logger.info(f"\n📊 Performance Analysis:")
            if total_time < 120:
                logger.info(f"  🚀 Excellent! Under 2 minutes")
            elif total_time < 180:
                logger.info(f"  ✅ Good! Under 3 minutes")
            else:
                logger.info(f"  ⚠️ Could be optimized further")
            
            logger.info(f"{'='*60}\n")
            
        else:
            logger.error(f"\n❌ Article generation failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}", exc_info=True)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate Dakota Learning Center articles with parallel execution"
    )
    parser.add_argument("topic", help="Article topic")
    parser.add_argument(
        "--word-count", 
        type=int, 
        default=1000, 
        help="Target word count (default: 1000)"
    )
    parser.add_argument(
        "--debug", 
        action="store_true", 
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    if args.debug:
        setup_logging(level="DEBUG")
    else:
        setup_logging(level="INFO")
    
    # Run async
    asyncio.run(generate_article(args.topic, args.word_count))


if __name__ == "__main__":
    main()