#!/usr/bin/env python3
"""
Generate real estate investment trusts article with 100% verification
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime
from typing import Dict, Any

from src.agents.dakota_agents.orchestrator import DakotaOrchestrator
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


async def generate_article(topic: str):
    """Generate a single article with 100% verification"""
    orchestrator = DakotaOrchestrator()
    
    logger.info(f"Generating article for topic: {topic}")
    
    try:
        result = await orchestrator.generate_article(topic)
        
        if result["status"] == "completed":
            logger.info(f"Successfully generated article for: {topic}")
            logger.info(f"Output directory: {result['output_dir']}")
            return True
        else:
            logger.error(f"Failed to generate article for: {topic}")
            logger.error(f"Reason: {result.get('reason', 'Unknown')}")
            return False
    except Exception as e:
        logger.error(f"Error generating article for {topic}: {str(e)}")
        return False


async def main():
    """Main execution function"""
    topic = "real estate investment trusts analysis"
    
    logger.info("Starting REIT article generation with 100% verification requirement")
    
    success = await generate_article(topic)
    
    if success:
        logger.info("Article generation completed successfully!")
    else:
        logger.error("Article generation failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())