#!/usr/bin/env python3
"""Simple article generator that just works"""
import sys

from learning_center_agent.pipeline.simple_orchestrator import SimpleOrchestrator

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n📝 Dakota Learning Center Article Generator")
        print("\nUsage:")
        print("  python generate_article.py \"Your Article Topic\" [word_count]")
        print("\nExamples:")
        print("  python generate_article.py \"Top Private Equity Strategies for 2025\"")
        print("  python generate_article.py \"Understanding Alternative Investments\" 2000")
        sys.exit(1)
    
    topic = sys.argv[1]
    word_count = int(sys.argv[2]) if len(sys.argv) > 2 else 1500
    
    orchestrator = SimpleOrchestrator()
    orchestrator.generate_article(topic, word_count)