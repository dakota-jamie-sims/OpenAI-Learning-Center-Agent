#!/usr/bin/env python3
"""
Generate an article using the multi-agent system
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import argparse
from datetime import datetime
import json

from src.pipeline.multi_agent_orchestrator import generate_article_multi_agent
from src.config import MIN_WORD_COUNT, OUTPUT_BASE_DIR


def main():
    """Main function for multi-agent article generation"""
    parser = argparse.ArgumentParser(
        description="Generate an article using the multi-agent system"
    )
    parser.add_argument(
        "--topic", 
        type=str, 
        required=True,
        help="Topic for the article"
    )
    parser.add_argument(
        "--word-count", 
        type=int, 
        default=MIN_WORD_COUNT,
        help=f"Target word count (default: {MIN_WORD_COUNT})"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed agent communication"
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print("🤖 MULTI-AGENT ARTICLE GENERATION")
    print(f"{'='*60}")
    print(f"Topic: {args.topic}")
    print(f"Target: {args.word_count} words")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")
    
    try:
        # Generate article
        result = generate_article_multi_agent(args.topic, args.word_count)
        
        if result.get("success"):
            print(f"\n✅ Article generated successfully!")
            
            # Display results
            print(f"\n📊 Results:")
            print(f"   Word Count: {result['metrics']['word_count']}")
            print(f"   Quality Score: {result['metrics']['quality_score']:.1f}/10")
            print(f"   Generation Time: {result['metrics']['generation_time']:.1f} minutes")
            
            # Display files
            print(f"\n📁 Output Files:")
            for file_type, file_path in result['files'].items():
                print(f"   {file_type}: {file_path}")
            
            # Display agent involvement
            print(f"\n🤖 Agent Involvement:")
            for agent_type, count in result['metrics']['agents_involved'].items():
                print(f"   {agent_type}: {count} agents")
            
            # Quality summary
            if 'quality_report' in result:
                quality = result['quality_report']
                print(f"\n✅ Quality Assessment:")
                print(f"   Overall Score: {quality.get('overall_quality_score', 0):.1f}/10")
                print(f"   Grade: {quality.get('quality_grade', 'N/A')}")
                print(f"   Ready for Publication: {quality.get('ready_for_publication', False)}")
                
                if quality.get('recommendations'):
                    print(f"\n💡 Top Recommendations:")
                    for i, rec in enumerate(quality['recommendations'][:3], 1):
                        print(f"   {i}. {rec}")
            
            # Preview
            print(f"\n📄 Article Preview:")
            print(f"{'-'*60}")
            print(result['article'][:500] + "...")
            print(f"{'-'*60}")
            
            print(f"\n✨ Article saved to: {result['output_directory']}")
            print(f"\n🎉 Success! View your article at:")
            print(f"   {result['files']['article']}")
            
        else:
            print(f"\n❌ Article generation failed!")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            print(f"   Phase: {result.get('phase_failed', 'Unknown')}")
            
            if 'details' in result:
                print(f"\n🔍 Error Details:")
                print(json.dumps(result['details'], indent=2))
            
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
