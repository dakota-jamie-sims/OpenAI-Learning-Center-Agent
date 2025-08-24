#!/usr/bin/env python3
"""Test the working multi-agent orchestrator"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import time
from datetime import datetime

from src.pipeline.working_multi_agent_orchestrator import WorkingMultiAgentOrchestrator
from src.models import ArticleRequest
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def test_orchestrator():
    """Test the working orchestrator"""
    
    # Create request
    request = ArticleRequest(
        topic="AI in portfolio management for institutional investors",
        audience="institutional investors and financial professionals",
        tone="professional yet conversational",
        word_count=1500
    )
    
    print("\n🧪 Testing Working Multi-Agent Orchestrator")
    print("=" * 60)
    print(f"Topic: {request.topic}")
    print(f"Target: {request.word_count} words")
    print("=" * 60)
    
    # Create orchestrator
    orchestrator = WorkingMultiAgentOrchestrator()
    
    # Test phases individually first
    print("\n📋 Testing individual phases...")
    
    try:
        # Test research phase
        print("\n1️⃣ Testing Research Phase...")
        start_time = time.time()
        research_data = await orchestrator._conduct_research(request.topic)
        elapsed = time.time() - start_time
        
        if research_data.get("success"):
            print(f"✅ Research completed in {elapsed:.1f}s")
            print(f"   Sources found: {len(research_data.get('sources', []))}")
        else:
            print(f"❌ Research failed: {research_data.get('error')}")
            return
        
        # Test synthesis phase
        print("\n2️⃣ Testing Synthesis Phase...")
        start_time = time.time()
        synthesis = await orchestrator._synthesize_research(research_data, request)
        elapsed = time.time() - start_time
        print(f"✅ Synthesis completed in {elapsed:.1f}s")
        
        # Test writing phase
        print("\n3️⃣ Testing Writing Phase...")
        start_time = time.time()
        article = await orchestrator._write_article(synthesis, request)
        elapsed = time.time() - start_time
        print(f"✅ Writing completed in {elapsed:.1f}s")
        print(f"   Words written: {len(article.split())}")
        
        # Test enhancement phase
        print("\n4️⃣ Testing Enhancement Phase...")
        start_time = time.time()
        enhanced = await orchestrator._enhance_article(article, request)
        elapsed = time.time() - start_time
        print(f"✅ Enhancement completed in {elapsed:.1f}s")
        
    except Exception as e:
        print(f"\n❌ Phase testing failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Now test full generation
    print("\n\n🚀 Testing Full Article Generation...")
    print("=" * 60)
    
    try:
        start_time = time.time()
        result = await orchestrator.generate_article(request)
        elapsed = time.time() - start_time
        
        if result.get("success"):
            print(f"\n✅ Article generated successfully in {elapsed:.1f}s!")
            
            # Save article
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/test_working_{timestamp}.md"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, "w") as f:
                f.write(result["article"])
            
            print(f"📄 Saved to: {output_path}")
            
            # Show metadata
            metadata = result.get("metadata", {})
            print("\n📊 Generation Metadata:")
            print(f"   Word count: {metadata.get('word_count', 'N/A')}")
            print(f"   Generation time: {metadata.get('generation_time', elapsed):.2f}s")
            print(f"   Sources used: {metadata.get('sources_used', 'N/A')}")
            print(f"   Model: {metadata.get('model', 'N/A')}")
            
            # Show first few lines of article
            lines = result["article"].split("\n")
            print("\n📝 Article Preview:")
            print("-" * 40)
            for line in lines[:10]:
                if line.strip():
                    print(line[:80] + "..." if len(line) > 80 else line)
            print("-" * 40)
            
        else:
            print(f"\n❌ Article generation failed!")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


async def test_llm_query():
    """Test LLM query directly"""
    print("\n🧪 Testing Direct LLM Query")
    print("=" * 60)
    
    orchestrator = WorkingMultiAgentOrchestrator()
    
    try:
        prompt = "Write a one-sentence summary about AI in finance."
        print(f"Prompt: {prompt}")
        
        result = await orchestrator._query_llm(
            prompt=prompt,
            model="gpt-5-nano",
            max_tokens=100
        )
        
        print(f"Response: {result}")
        
    except Exception as e:
        print(f"❌ LLM query failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🔧 Working Multi-Agent Orchestrator Test")
    print("This tests the simplified, working implementation")
    
    # Test LLM first
    asyncio.run(test_llm_query())
    
    # Then test full orchestrator
    asyncio.run(test_orchestrator())