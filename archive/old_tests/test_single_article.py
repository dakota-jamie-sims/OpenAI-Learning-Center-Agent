#!/usr/bin/env python3
"""Test script to generate a single article with enhanced matching"""

import json
import os
from src.pipeline.multi_agent_orchestrator import MultiAgentPipelineOrchestrator

def test_single_article():
    """Test generating a single article"""
    orchestrator = MultiAgentPipelineOrchestrator()
    
    topic = "venture capital trends 2025"
    print(f"\n🚀 Generating article on: {topic}")
    print("=" * 60)
    
    try:
        result = orchestrator.generate_article(
            topic=topic,
            word_count=1750
        )
        
        if result["success"]:
            print("\n✅ Article generated successfully!")
            print(f"   Output: {result.get('output_path', 'N/A')}")
            print(f"   Word count: {result['word_count']}")
            
            # Check if we have the article content
            if 'article' in result and result['article']:
                # Extract related articles if present in the article metadata
                print("\n🔗 Checking for enhanced related articles...")
                
                # The multi-agent system should include related articles in the response
                # Let's see what's in the result
                print("\n📊 Result keys:", list(result.keys()))
                
                if 'metadata' in result:
                    print("📊 Metadata keys:", list(result['metadata'].keys()) if isinstance(result['metadata'], dict) else 'Not a dict')
            
        else:
            print(f"\n❌ Failed to generate article: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_single_article()