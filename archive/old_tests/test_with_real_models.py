#!/usr/bin/env python3
"""
Test article generation with real OpenAI models
"""
import asyncio
import sys
import os
import time

# Override models before any imports
os.environ['DEFAULT_MODEL'] = 'gpt-4o'
os.environ['ORCHESTRATOR_MODEL'] = 'gpt-4o-mini'
os.environ['WEB_RESEARCHER_MODEL'] = 'gpt-4o-mini'
os.environ['KB_RESEARCHER_MODEL'] = 'gpt-4o-mini'
os.environ['SYNTHESIZER_MODEL'] = 'gpt-4o'
os.environ['WRITER_MODEL'] = 'gpt-4o'
os.environ['SEO_MODEL'] = 'gpt-4o-mini'
os.environ['FACT_CHECKER_MODEL'] = 'gpt-4o'
os.environ['SUMMARY_MODEL'] = 'gpt-4o-mini'
os.environ['SOCIAL_MODEL'] = 'gpt-4o-mini'
os.environ['ITERATION_MODEL'] = 'gpt-4o'
os.environ['METRICS_MODEL'] = 'gpt-4o-mini'

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.models import ArticleRequest
from src.agents.dakota_agents.orchestrator import DakotaOrchestrator
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def test_with_real_models():
    """Test with real OpenAI models"""
    
    topic = "Private Equity Trends for 2025"
    logger.info(f"\n{'='*60}")
    logger.info(f"🧪 Testing with Real OpenAI Models")
    logger.info(f"📝 Topic: {topic}")
    logger.info(f"🤖 Using: gpt-4o and gpt-4o-mini")
    logger.info(f"{'='*60}\n")
    
    try:
        # Create request
        request = ArticleRequest(
            topic=topic,
            audience="institutional investors",
            tone="professional yet conversational",
            word_count=500  # Shorter for faster testing
        )
        
        # Create orchestrator
        orchestrator = DakotaOrchestrator()
        
        # Execute
        start_time = time.time()
        result = await orchestrator.execute({"request": request})
        total_time = time.time() - start_time
        
        if result["success"]:
            logger.info(f"\n✅ SUCCESS!")
            logger.info(f"⏱️ Time: {total_time:.2f} seconds")
            logger.info(f"📁 Output: {result['data']['output_folder']}")
            logger.info(f"📄 Files: {', '.join(result['data']['files_created'])}")
            logger.info(f"📝 Word count: {result['data']['word_count']}")
            logger.info(f"✅ Approved: {result['data']['fact_checker_approved']}")
            
            # Check article content
            output_dir = result['data']['output_folder']
            article_file = f"{output_dir}/{result['data']['files_created'][0]}"
            
            with open(article_file, 'r') as f:
                content = f.read()
                
            if len(content) > 500:  # Check if real content was generated
                logger.info(f"\n📄 Article preview:")
                logger.info(content[:300] + "...")
            else:
                logger.warning(f"\n⚠️ Article seems too short or incomplete")
                
        else:
            logger.error(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"\n❌ Error: {e}", exc_info=True)


if __name__ == "__main__":
    asyncio.run(test_with_real_models())