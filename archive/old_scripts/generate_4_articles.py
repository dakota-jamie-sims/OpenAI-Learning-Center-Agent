#!/usr/bin/env python3
"""Generate 4 articles using Dakota multi-agent system"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from datetime import datetime
import logging

from src.agents.dakota_agents.orchestrator import DakotaOrchestrator
from src.models import ArticleRequest
from src.utils.logging import get_logger

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = get_logger(__name__)


async def generate_article(topic: str):
    """Generate a single article"""
    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting article generation for: {topic}")
        logger.info(f"{'='*60}\n")
        
        # Create request
        request = ArticleRequest(
            topic=topic,
            audience="institutional investors and financial professionals",
            tone="professional",
            word_count=1750
        )
        
        # Create orchestrator
        orchestrator = DakotaOrchestrator()
        
        # Execute generation
        result = await orchestrator.execute({
            "request": request
        })
        
        if result["success"]:
            logger.info(f"\n✅ Article generated successfully for: {topic}")
            logger.info(f"   Output folder: {result['data']['output_folder']}")
            logger.info(f"   Word count: {result['data']['word_count']}")
            logger.info(f"   Fact-checker approved: {result['data']['fact_checker_approved']}")
            logger.info(f"   Sources verified: {result['data']['sources_verified']}")
            return True
        else:
            logger.error(f"\n❌ Failed to generate article for: {topic}")
            logger.error(f"   Error: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        logger.error(f"\n❌ Exception generating article for {topic}: {e}")
        return False


async def main():
    """Generate all 4 articles"""
    topics = [
        "venture capital trends 2025",
        "private credit emerging managers",
        "hedge fund strategies 2025",
        "real estate investment trusts analysis"
    ]
    
    logger.info("Starting Dakota article generation for 4 topics...")
    logger.info(f"Topics: {topics}")
    
    results = []
    for topic in topics:
        success = await generate_article(topic)
        results.append({
            "topic": topic,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })
        
        # Small delay between articles
        if topic != topics[-1]:
            logger.info("\nWaiting 5 seconds before next article...")
            await asyncio.sleep(5)
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("GENERATION SUMMARY")
    logger.info(f"{'='*60}")
    
    successful = sum(1 for r in results if r["success"])
    logger.info(f"Successfully generated: {successful}/{len(topics)} articles")
    
    for result in results:
        status = "✅" if result["success"] else "❌"
        logger.info(f"{status} {result['topic']}")
    
    # Save results
    with open("output/generation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    logger.info("\nResults saved to output/generation_results.json")


if __name__ == "__main__":
    asyncio.run(main())