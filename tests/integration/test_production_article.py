#!/usr/bin/env python3
"""
Test article generation with REAL KB search (no mocks!)
This is the production-ready test
"""
import os
import sys
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from src.pipeline.multi_agent_orchestrator import MultiAgentPipelineOrchestrator
from src.utils.logging import get_logger
from src.config import OUTPUT_DIR

logger = get_logger(__name__)

def main():
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
    
    # Initialize orchestrator
    orchestrator = MultiAgentPipelineOrchestrator()
    
    print("\nStarting article generation...")
    start_time = datetime.now()
    
    try:
        # Generate article with custom parameters
        result = orchestrator.generate_article(
            topic=topic,
            audience="High-net-worth individuals and family office managers",
            tone="professional",
            word_count=1500,
            custom_instructions="Focus on practical AI applications, risk management, and real-world case studies. Include insights from Dakota's knowledge base about family office strategies."
        )
        
        generation_time = (datetime.now() - start_time).total_seconds()
        
        if result.get("success"):
            print(f"\n✅ Article generated successfully in {generation_time:.1f}s!")
            print(f"\nWord count: {result.get('word_count', 'N/A')}")
            
            # Extract metadata
            metadata = result.get('metadata', {})
            print(f"KB citations: {metadata.get('kb_citations_count', 'N/A')}")
            print(f"Web citations: {metadata.get('web_citations_count', 'N/A')}")
            
            # Show preview of article
            article = result.get('article', '')
            if article:
                lines = article.split('\n')
                title = lines[0].replace('#', '').strip() if lines else "Untitled"
                print(f"\nTitle: {title}")
                print(f"\nPreview:\n{article[:500]}...")
            
            print(f"\n📄 Article saved to: {result.get('output_path', 'N/A')}")
            
            # Show quality metrics if available
            quality = result.get('quality_metrics', {})
            if quality:
                print("\n📊 Quality Metrics:")
                for metric, value in quality.items():
                    print(f"  - {metric}: {value}")
            
        else:
            error = result.get('error', 'Unknown error')
            print(f"\n❌ Article generation failed: {error}")
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        logger.error(f"Article generation error: {e}", exc_info=True)
    
    print("\n" + "="*60)
    print("✅ Production test complete!")
    print("="*60)

if __name__ == "__main__":
    main()