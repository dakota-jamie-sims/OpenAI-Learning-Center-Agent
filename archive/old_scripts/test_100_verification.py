#!/usr/bin/env python3
"""Test article generation with 100% verification requirement"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from src.agents.dakota_agents.orchestrator import DakotaOrchestrator
from src.models import ArticleRequest
from src.utils.logging import get_logger
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = get_logger(__name__)


async def main():
    """Test with 100% verification"""
    
    print("\n" + "="*60)
    print("TESTING 100% CLAIM VERIFICATION SYSTEM")
    print("="*60)
    print("\nRequirements:")
    print("- Every claim must be verifiable from sources")
    print("- All sources must be real and fetchable")
    print("- Zero tolerance for unverified claims")
    print("="*60 + "\n")
    
    # Test topic
    topic = "venture capital trends 2025"
    
    print(f"Testing with topic: {topic}")
    print("This will generate an article where EVERY claim is 100% verified.\n")
    
    # Create request
    request = ArticleRequest(
        topic=topic,
        audience="institutional investors and financial professionals",
        tone="professional",
        word_count=1750
    )
    
    # Create orchestrator
    orchestrator = DakotaOrchestrator()
    
    # Execute
    print("Starting generation...\n")
    result = await orchestrator.execute({
        "request": request
    })
    
    if result["success"]:
        print("\n✅ ARTICLE GENERATED SUCCESSFULLY!")
        print(f"Output folder: {result['data']['output_folder']}")
        print(f"Word count: {result['data']['word_count']}")
        print(f"Fact-checker approved: {result['data']['fact_checker_approved']}")
        print(f"Sources verified: {result['data']['sources_verified']}")
        print(f"Files created: {', '.join(result['data']['files_created'])}")
        
        if result['data']['fact_checker_approved']:
            print("\n🎉 SUCCESS: Article passed 100% verification!")
            print("All claims in the article are verified from real sources.")
    else:
        print(f"\n❌ Generation failed: {result.get('error', 'Unknown error')}")
        print("\nThis likely means the fact-checker rejected the article.")
        print("Check the logs above to see which claims could not be verified.")


if __name__ == "__main__":
    asyncio.run(main())