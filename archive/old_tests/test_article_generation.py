#!/usr/bin/env python3
"""
Simple test of article generation using existing orchestrator
"""
import asyncio
import sys
import os
import time
from datetime import datetime

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Use existing imports that we know work
from src.models import ArticleRequest
from src.agents.dakota_agents.orchestrator import DakotaOrchestrator
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def test_generation():
    """Test article generation with existing orchestrator"""
    
    topic = "The Rise of Alternative Investment Strategies in 2025"
    logger.info(f"\n{'='*60}")
    logger.info(f"📝 Testing Article Generation")
    logger.info(f"Topic: {topic}")
    logger.info(f"{'='*60}\n")
    
    try:
        # Create request
        request = ArticleRequest(
            topic=topic,
            audience="institutional investors",
            tone="professional yet conversational",
            word_count=800
        )
        
        # Use existing orchestrator
        orchestrator = DakotaOrchestrator()
        
        # Time the execution
        start_time = time.time()
        result = await orchestrator.execute({"request": request})
        total_time = time.time() - start_time
        
        if result["success"]:
            logger.info(f"\n✅ SUCCESS!")
            logger.info(f"Time: {total_time:.2f} seconds")
            logger.info(f"Output: {result['data']['output_folder']}")
            logger.info(f"Files: {result['data']['files_created']}")
            logger.info(f"Word count: {result['data']['word_count']}")
        else:
            logger.error(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)


if __name__ == "__main__":
    # Run with existing orchestrator first to establish baseline
    asyncio.run(test_generation())