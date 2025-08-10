#!/usr/bin/env python3
"""
Simple test script for Chat Completions orchestrator
"""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

from src.pipeline.chat_orchestrator import ChatOrchestrator


async def test_chat_orchestrator():
    """Test the chat orchestrator with a simple topic"""
    print("🧪 Testing Chat Completions Orchestrator")
    print("=" * 50)
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY not found")
        return
    
    # Simple test topic
    topic = "Quick Guide to Private Equity Fund Selection"
    
    print(f"Topic: {topic}")
    print(f"Mode: Quick (500 words, 5 sources)")
    print()
    
    try:
        # Create orchestrator
        orchestrator = ChatOrchestrator()
        
        print("1️⃣ Initializing agents...")
        await orchestrator.initialize_agents()
        print("✅ Agents initialized")
        
        print("\n2️⃣ Running pipeline...")
        results = await orchestrator.run_pipeline(
            topic,
            min_words=500,
            min_sources=5
        )
        
        print("\n3️⃣ Results:")
        print("-" * 30)
        print(f"Status: {results['status']}")
        
        if results['status'] == 'SUCCESS':
            print(f"✅ Article Path: {results['article_path']}")
            print(f"📊 Total Tokens: {results.get('total_tokens', 0):,}")
            print(f"⏱️  Time: {results['elapsed_time']}")
            print(f"🔄 Iterations: {results['iterations']}")
            
            # Check if article exists
            if os.path.exists(results['article_path']):
                with open(results['article_path'], 'r') as f:
                    content = f.read()
                    word_count = len(content.split())
                print(f"📝 Word Count: {word_count}")
                print(f"📄 First 200 chars: {content[:200]}...")
        else:
            print(f"❌ Failed: {results.get('reason', 'Unknown')}")
            if results.get('error'):
                print(f"Error: {results['error']}")
                
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Starting test...")
    asyncio.run(test_chat_orchestrator())
    print("\nTest complete!")