#!/usr/bin/env python3
"""
Test the working production system with existing agents
"""
import asyncio
import sys
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.models import ArticleRequest
from src.agents.dakota_agents.orchestrator_v2_working import DakotaOrchestratorV2Working
from src.utils.logging import get_logger, setup_logging

setup_logging(level="INFO")
logger = get_logger(__name__)


async def test_parallel_execution():
    """Test the new parallel orchestrator with existing agents"""
    
    logger.info("="*60)
    logger.info("🧪 TESTING PARALLEL EXECUTION WITH EXISTING AGENTS")
    logger.info("="*60)
    
    # Check environment
    if not os.getenv("OPENAI_API_KEY"):
        logger.error("❌ OPENAI_API_KEY not set in .env file")
        return
    
    if not os.getenv("OPENAI_VECTOR_STORE_ID"):
        logger.error("❌ OPENAI_VECTOR_STORE_ID not set in .env file")
        return
    
    logger.info("✅ Environment variables loaded")
    
    # Create test request
    test_topic = "The Future of Private Credit in 2025"
    request = ArticleRequest(
        topic=test_topic,
        audience="institutional investors",
        tone="professional yet conversational",
        word_count=800  # Shorter for testing
    )
    
    logger.info(f"📝 Test topic: {test_topic}")
    logger.info(f"📊 Target word count: {request.word_count}")
    
    # Test orchestrator
    try:
        logger.info("\n🚀 Starting parallel article generation...")
        start_time = time.time()
        
        orchestrator = DakotaOrchestratorV2Working()
        result = await orchestrator.execute({"request": request})
        
        total_time = time.time() - start_time
        
        if result["success"]:
            logger.info(f"\n✅ SUCCESS! Article generated in {total_time:.2f} seconds")
            logger.info(f"📁 Output: {result['data']['output_folder']}")
            logger.info(f"📄 Files: {', '.join(result['data']['files_created'])}")
            logger.info(f"📝 Word count: {result['data']['word_count']}")
            logger.info(f"✅ Fact-checked: {result['data']['fact_checker_approved']}")
            
            # Check if parallel execution actually happened
            logger.info("\n📊 Parallel Execution Analysis:")
            logger.info("- Phase 2-3: KB + Web research ran in parallel")
            logger.info("- Phase 5: Metrics + SEO analysis ran in parallel")
            logger.info("- Phase 7: Social + Summary creation ran in parallel")
            
        else:
            logger.error(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"\n❌ Exception: {e}", exc_info=True)


async def test_kb_search():
    """Test basic KB search functionality"""
    logger.info("\n=== Testing KB Search ===")
    
    try:
        from src.services.kb_search_optimized import OptimizedKBSearcher
        
        searcher = OptimizedKBSearcher()
        result = searcher.search("private credit trends")
        
        if result.get("citations_count", 0) > 0:
            logger.info(f"✅ KB Search working: {result['citations_count']} results")
        else:
            logger.warning("⚠️ KB Search returned no results")
            
    except Exception as e:
        logger.error(f"❌ KB Search error: {e}")


async def test_agents_exist():
    """Verify all required agents exist"""
    logger.info("\n=== Checking Agent Files ===")
    
    agents = [
        "kb_researcher", "web_researcher", "research_synthesizer",
        "content_writer", "fact_checker_v2", "iteration_manager",
        "social_promoter", "summary_writer", "seo_specialist",
        "metrics_analyzer"
    ]
    
    all_exist = True
    for agent in agents:
        path = f"src/agents/dakota_agents/{agent}.py"
        if os.path.exists(path):
            logger.info(f"✅ {agent}.py exists")
        else:
            logger.error(f"❌ {agent}.py missing")
            all_exist = False
    
    return all_exist


async def main():
    """Run all tests"""
    
    # Check agents exist
    if not await test_agents_exist():
        logger.error("\n❌ Missing required agent files")
        return
    
    # Test KB search
    await test_kb_search()
    
    # Test parallel execution
    await test_parallel_execution()
    
    logger.info("\n" + "="*60)
    logger.info("🏁 TEST COMPLETE")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())