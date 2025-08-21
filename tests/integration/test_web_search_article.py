#!/usr/bin/env python3
"""
Test article generation with a topic requiring current web information
"""
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from pipeline.multi_agent_orchestrator import MultiAgentPipelineOrchestrator
from utils.logging import get_logger

logger = get_logger(__name__)

def test_current_topic():
    """Test with a topic that requires current web information"""
    
    # Create orchestrator
    orchestrator = MultiAgentPipelineOrchestrator()
    
    # Topic that requires current web data
    topic = "AI Market Trends and Investment Opportunities in Q4 2024"
    
    logger.info("="*60)
    logger.info("Testing Multi-Agent System with Current Web Data")
    logger.info("="*60)
    logger.info(f"Topic: {topic}")
    logger.info("This topic requires current market data and trends...")
    logger.info("")
    
    # Generate article
    result = orchestrator.generate_article(
        topic=topic,
        word_count=2500,
        custom_instructions="""
        Focus on:
        1. Current AI company valuations and recent funding rounds
        2. Latest AI regulatory developments 
        3. Recent AI breakthroughs and their market impact
        4. Q4 2024 specific investment opportunities
        5. Include specific data points, statistics, and recent examples
        
        This article should demonstrate the system's ability to find and incorporate
        current information from web searches.
        """
    )
    
    if result["success"]:
        logger.info("✅ Article generated successfully!")
        logger.info(f"📄 Output: {result['output_path']}")
        logger.info(f"📊 Word count: {result['word_count']}")
        
        # Check if web sources were used
        if 'metadata' in result and isinstance(result['metadata'], dict):
            sources = result['metadata'].get('sources', [])
            web_sources = [s for s in sources if 'http' in s.get('url', '')]
            logger.info(f"🌐 Web sources found: {len(web_sources)}")
            
            if web_sources:
                logger.info("\nWeb sources used:")
                for i, source in enumerate(web_sources[:5], 1):
                    logger.info(f"  {i}. {source.get('title', 'Untitled')} - {source.get('url', '')}")
        
        # Show a preview
        logger.info("\n" + "="*60)
        logger.info("Article Preview (first 500 chars):")
        logger.info("="*60)
        logger.info(result["article"][:500] + "...")
        
        # Check quality metrics
        if result.get('quality_metrics'):
            logger.info("\n" + "="*60)
            logger.info("Quality Metrics:")
            logger.info("="*60)
            for key, value in result['quality_metrics'].items():
                logger.info(f"  {key}: {value}")
                
    else:
        logger.error(f"❌ Article generation failed: {result.get('error', 'Unknown error')}")
        if 'details' in result:
            logger.error(f"Details: {result['details']}")

if __name__ == "__main__":
    test_current_topic()