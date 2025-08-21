#!/usr/bin/env python3
"""
Test simple article generation without hanging
"""
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from pipeline.multi_agent_orchestrator import MultiAgentPipelineOrchestrator
from utils.logging import get_logger
import logging

# Set logging to INFO to see what's happening
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)

def test_simple_article():
    """Test with a simple topic"""
    
    # Create orchestrator
    orchestrator = MultiAgentPipelineOrchestrator()
    
    # Simple topic
    topic = "Best Practices for Portfolio Diversification in 2024"
    
    logger.info("="*60)
    logger.info("Testing Simple Article Generation")
    logger.info("="*60)
    logger.info(f"Topic: {topic}")
    logger.info("")
    
    start_time = datetime.now()
    
    # Generate article with shorter word count for faster testing
    result = orchestrator.generate_article(
        topic=topic,
        word_count=1000,  # Shorter for testing
        custom_instructions="Keep it concise and focused. This is a test run."
    )
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    if result["success"]:
        logger.info(f"✅ Article generated successfully in {duration:.1f} seconds!")
        logger.info(f"📄 Output: {result.get('output_path', 'N/A')}")
        logger.info(f"📊 Word count: {result.get('word_count', 'N/A')}")
        
        # Show first 300 chars
        if result.get("article"):
            logger.info("\n" + "="*60)
            logger.info("Article Preview:")
            logger.info("="*60)
            logger.info(result["article"][:300] + "...")
            
    else:
        logger.error(f"❌ Article generation failed: {result.get('error', 'Unknown error')}")
        if 'details' in result:
            logger.error(f"Details: {result['details']}")

if __name__ == "__main__":
    test_simple_article()