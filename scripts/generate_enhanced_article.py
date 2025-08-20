#!/usr/bin/env python3
"""
Enhanced article generator with all features and 100% reliability
"""
import asyncio
import sys

from learning_center_agent.pipeline.enhanced_orchestrator import (
    EnhancedOrchestrator,
)


async def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_enhanced_article.py 'Your Article Topic' [word_count]")
        print("\nExamples:")
        print("  python generate_enhanced_article.py 'Top Private Equity Strategies for 2025'")
        print("  python generate_enhanced_article.py 'ESG Investing in Alternative Assets' 2000")
        sys.exit(1)
    
    topic = sys.argv[1]
    word_count = int(sys.argv[2]) if len(sys.argv) > 2 else 1500
    
    print(f"🚀 Generating enhanced article: {topic}")
    print(f"📝 Target word count: {word_count}")
    
    orchestrator = EnhancedOrchestrator()
    result = await orchestrator.generate_article(topic, word_count)
    
    if result["status"] == "success":
        print("\n✅ Article generation complete!")
        print(f"📁 Files saved to: {result['output_dir']}")
        print("\n📊 Summary:")
        print(f"  - Quality Score: {result['metrics']['quality_score']}")
        print(f"  - Total Tokens: {result['metrics']['total_tokens']:,}")
        print(f"  - Estimated Cost: ${result['metrics']['estimated_cost']:.3f}")
        print(f"  - Time Elapsed: {result['metrics']['elapsed_time']:.1f}s")
    else:
        print(f"\n❌ Generation failed: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())