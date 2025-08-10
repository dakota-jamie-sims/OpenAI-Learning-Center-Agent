#!/usr/bin/env python3
"""
Quick article generation script using Chat Completions API
Bypasses vector store for testing
"""
import asyncio
import os
import sys
from pathlib import Path
import click

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from src.pipeline.chat_orchestrator import ChatOrchestrator
from src.config_working import OUTPUT_DIR


@click.command()
@click.option('--topic', default="Best Practices for Private Equity Due Diligence", help='Article topic')
@click.option('--words', default=500, help='Target word count')
@click.option('--sources', default=5, help='Minimum sources')
def generate(topic: str, words: int, sources: int):
    """Generate a quick article using Chat Completions API"""
    
    print("🚀 Dakota Learning Center - Quick Article Generator")
    print("=" * 50)
    print(f"Topic: {topic}")
    print(f"Target: {words} words, {sources} sources")
    print()
    
    async def run():
        try:
            # Create orchestrator
            orchestrator = ChatOrchestrator()
            
            # Skip KB initialization if no vector store
            if not os.getenv("VECTOR_STORE_ID"):
                print("⚠️  No vector store found, skipping KB search")
                # Monkey patch to skip KB
                orchestrator._handle_kb_search = lambda *args, **kwargs: {"error": "KB disabled"}
            
            print("📝 Initializing agents...")
            await orchestrator.initialize_agents()
            
            print("🔄 Running pipeline...")
            results = await orchestrator.run_pipeline(
                topic,
                min_words=words,
                min_sources=sources
            )
            
            return results
            
        except Exception as e:
            return {"status": "ERROR", "error": str(e)}
    
    # Run async function
    results = asyncio.run(run())
    
    # Display results
    print("\n" + "=" * 50)
    if results['status'] == 'SUCCESS':
        print("✅ SUCCESS!")
        print(f"📄 Article: {results['article_path']}")
        print(f"📊 Tokens: {results.get('total_tokens', 0):,}")
        print(f"⏱️  Time: {results['elapsed_time']}")
        
        # Show first 500 chars
        if os.path.exists(results['article_path']):
            with open(results['article_path'], 'r') as f:
                content = f.read()
                print(f"\n📝 Preview ({len(content.split())} words):")
                print("-" * 40)
                print(content[:500] + "...")
    else:
        print("❌ FAILED!")
        print(f"Error: {results.get('error', 'Unknown error')}")
        if results.get('issues'):
            print("Issues:")
            for issue in results['issues']:
                print(f"  - {issue}")


if __name__ == "__main__":
    generate()