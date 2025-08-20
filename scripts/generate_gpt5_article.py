#!/usr/bin/env python3
"""
Generate article using GPT-5 with Responses API
Simple, clean implementation
"""
import sys
import argparse

from learning_center_agent.pipeline.gpt5_orchestrator import GPT5Orchestrator


def main():
    parser = argparse.ArgumentParser(description='Generate article using GPT-5')
    parser.add_argument('--topic', type=str, required=True, help='Article topic')
    parser.add_argument('--word-count', type=int, default=1500, help='Target word count')
    
    args = parser.parse_args()
    
    # Create orchestrator and generate article
    orchestrator = GPT5Orchestrator()
    result = orchestrator.generate_article(args.topic, args.word_count)
    
    if result["status"] == "success":
        print(f"\n✅ Success! Article saved to: {result['output_dir']}")
        print(f"\nGenerated files:")
        for file_type, path in result["files"].items():
            print(f"  - {file_type}: {path}")
    else:
        print(f"\n❌ Error: {result.get('error', 'Unknown error')}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())