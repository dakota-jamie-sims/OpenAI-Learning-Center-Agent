#!/usr/bin/env python3
"""
Test article generation with REAL KB search (no mocks!)
This is the production-ready test
"""
import os
import sys
import asyncio
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.pipeline.multi_agent_orchestrator import MultiAgentPipelineOrchestrator
from src.services.article_generation import ArticleGenerationRequest
from src.utils.logging import get_logger
from src.config import OUTPUT_DIR

logger = get_logger(__name__)

async def main():
    print("="*60)
    print("PRODUCTION TEST: Article Generation with REAL KB Search")
    print("="*60)
    
    # Test topic that requires both KB and web search
    topic = "How are family offices using AI to enhance portfolio management in 2024?"
    
    print(f"\nTopic: {topic}")
    print("\nThis test will:")
    print("1. Search Dakota's knowledge base for family office insights")
    print("2. Search the web for 2024 AI trends")
    print("3. Generate a comprehensive article")
    print("\n" + "-"*60)
    
    # Create request
    request = ArticleGenerationRequest(
        topic=topic,
        target_audience="High-net-worth individuals and family office managers",
        word_count=1500,
        tone="professional",
        style="analytical",
        key_points=[
            "AI applications in portfolio management",
            "Family office technology adoption",
            "Risk management with AI",
            "Performance tracking and reporting"
        ],
        sources={
            "web_search": True,
            "knowledge_base": True
        }
    )
    
    # Initialize orchestrator
    orchestrator = MultiAgentPipelineOrchestrator()
    
    print("\nStarting article generation...")
    start_time = datetime.now()
    
    try:
        # Generate article
        result = await orchestrator.generate_article(request)
        
        generation_time = (datetime.now() - start_time).total_seconds()
        
        if result.success:
            print(f"\n✅ Article generated successfully in {generation_time:.1f}s!")
            print(f"\nTitle: {result.title}")
            print(f"Word count: {result.word_count}")
            print(f"KB citations: {result.kb_citations_count}")
            print(f"Web citations: {result.web_citations_count}")
            
            # Show preview
            print(f"\nPreview:\n{result.content[:500]}...")
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"article_production_test_{timestamp}.md"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(f"# {result.title}\n\n")
                f.write(result.content)
                f.write("\n\n## Metadata\n")
                f.write(f"- Generated: {result.generation_timestamp}\n")
                f.write(f"- Word count: {result.word_count}\n")
                f.write(f"- KB citations: {result.kb_citations_count}\n")
                f.write(f"- Web citations: {result.web_citations_count}\n")
                f.write(f"- Generation time: {generation_time:.1f}s\n")
            
            print(f"\n📄 Article saved to: {filepath}")
            
            # Show some KB search results
            if hasattr(result, 'kb_search_results'):
                print("\n📚 KB Search Results Used:")
                for i, kb_result in enumerate(result.kb_search_results[:3], 1):
                    print(f"{i}. {kb_result}")
            
        else:
            print(f"\n❌ Article generation failed: {result.error}")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.error(f"Article generation error: {e}", exc_info=True)
    
    print("\n" + "="*60)
    print("✅ Production test complete!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())