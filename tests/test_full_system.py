#!/usr/bin/env python3
"""
Test the full production system with all agents
"""
import asyncio
import os

from dotenv import load_dotenv
from learning_center_agent.pipeline.simple_orchestrator import (
    SimpleOrchestrator,
)

load_dotenv()

async def test_full_system():
    """Run the complete article generation pipeline"""
    
    # Configuration
    topic = "Top Private Equity Firms in Dallas 2025"
    
    print("🚀 TESTING FULL PRODUCTION SYSTEM")
    print("="*60)
    print(f"Topic: {topic}")
    print("\nThis will run ALL agents with real templates:")
    print("- Web Researcher")
    print("- KB Researcher") 
    print("- Research Synthesizer")
    print("- Content Writer")
    print("- Fact Checker")
    print("- SEO Specialist")
    print("- Social Promoter")
    print("- Metadata Generator")
    print("- And more...")
    print("="*60)
    
    # Initialize orchestrator with relaxed validation for testing
    orchestrator = SimpleOrchestrator(
        min_words=500,  # Lower for testing
        min_sources=3,   # Lower for testing
        max_iterations=2  # Fewer iterations
    )
    
    try:
        # Initialize all agents
        print("\n📝 Initializing agents...")
        await orchestrator.initialize_agents()
        
        # Run the full pipeline
        print("\n🔄 Running full pipeline with all agents...")
        results = await orchestrator.generate_article(topic)
        
        if results["status"] == "success":
            print("\n✅ SUCCESS! Article generated with full pipeline")
            print(f"\nOutput directory: {results.get('output_dir', 'output/')}")
            
            # Show what was created
            print("\nGenerated files:")
            output_dir = results.get('output_dir', '')
            if output_dir and os.path.exists(output_dir):
                for file in os.listdir(output_dir):
                    print(f"  - {file}")
            
            # Show article preview
            article_path = os.path.join(output_dir, "article.md") if output_dir else None
            if article_path and os.path.exists(article_path):
                with open(article_path, 'r') as f:
                    content = f.read()
                    print(f"\n📄 Article Preview ({len(content.split())} words):")
                    print("-"*40)
                    print(content[:500] + "...")
        else:
            print(f"\n❌ Generation failed: {results.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the async function
    asyncio.run(test_full_system())