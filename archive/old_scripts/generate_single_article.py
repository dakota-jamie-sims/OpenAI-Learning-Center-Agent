#!/usr/bin/env python3
"""
Generate a single article using the production system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import argparse
from datetime import datetime
from typing import Dict, Any

from src.agents.dakota_agents.orchestrator import DakotaOrchestrator
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


async def generate_article(topic: str):
    """Generate a single article with 100% verification"""
    orchestrator = DakotaOrchestrator()
    
    logger.info(f"Starting article generation for topic: {topic}")
    logger.info("=" * 60)
    
    try:
        result = await orchestrator.generate_article(topic)
        
        if result["status"] == "completed":
            logger.info(f"✅ Successfully generated article for: {topic}")
            logger.info(f"Output directory: {result['output_dir']}")
            return True
        else:
            logger.error(f"❌ Failed to generate article for: {topic}")
            logger.error(f"Reason: {result.get('reason', 'Unknown')}")
            return False
    except Exception as e:
        logger.error(f"Error generating article for {topic}: {str(e)}")
        return False


async def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="Generate a single Dakota article")
    parser.add_argument("topic", help="Topic for the article")
    args = parser.parse_args()
    
    logger.info("Starting Dakota article generation with 100% verification requirement")
    logger.info(f"Topic: {args.topic}")
    
    success = await generate_article(args.topic)
    
    if success:
        logger.info("Article generation completed successfully!")
    else:
        logger.error("Article generation failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())