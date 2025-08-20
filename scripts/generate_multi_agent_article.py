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
from src.utils.logging import get_logger


logger = get_logger(__name__)


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
    
    logger.info("\n%s", '='*60)
    logger.info("🤖 MULTI-AGENT ARTICLE GENERATION")
    logger.info("%s", '='*60)
    logger.info("Topic: %s", args.topic)
    logger.info("Target: %s words", args.word_count)
    logger.info("Time: %s", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    logger.info("%s", '='*60)
    
    try:
        # Generate article
        result = generate_article_multi_agent(args.topic, args.word_count)
        
        if result.get("success"):
            logger.info("\n✅ Article generated successfully!")

            # Display results
            logger.info("\n📊 Results:")
            logger.info("   Word Count: %s", result['metrics']['word_count'])
            logger.info(
                "   Quality Score: %.1f/10", result['metrics']['quality_score']
            )
            logger.info(
                "   Generation Time: %.1f minutes",
                result['metrics']['generation_time'],
            )

            # Display files
            logger.info("\n📁 Output Files:")
            for file_type, file_path in result['files'].items():
                logger.info("   %s: %s", file_type, file_path)

            # Display agent involvement
            logger.info("\n🤖 Agent Involvement:")
            for agent_type, count in result['metrics']['agents_involved'].items():
                logger.info("   %s: %s agents", agent_type, count)

            # Quality summary
            if 'quality_report' in result:
                quality = result['quality_report']
                logger.info("\n✅ Quality Assessment:")
                logger.info(
                    "   Overall Score: %.1f/10",
                    quality.get('overall_quality_score', 0),
                )
                logger.info("   Grade: %s", quality.get('quality_grade', 'N/A'))
                logger.info(
                    "   Ready for Publication: %s",
                    quality.get('ready_for_publication', False),
                )

                if quality.get('recommendations'):
                    logger.info("\n💡 Top Recommendations:")
                    for i, rec in enumerate(quality['recommendations'][:3], 1):
                        logger.info("   %s. %s", i, rec)

            # Preview
            logger.info("\n📄 Article Preview:")
            logger.info("%s", '-'*60)
            logger.info("%s...", result['article'][:500])
            logger.info("%s", '-'*60)

            logger.info("\n✨ Article saved to: %s", result['output_directory'])
            logger.info("\n🎉 Success! View your article at:")
            logger.info("   %s", result['files']['article'])

        else:
            logger.error("\n❌ Article generation failed!")
            logger.error("   Error: %s", result.get('error', 'Unknown error'))
            logger.error("   Phase: %s", result.get('phase_failed', 'Unknown'))

            if 'details' in result:
                logger.error("\n🔍 Error Details:")
                logger.error(json.dumps(result['details'], indent=2))

            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("\n\n⚠️ Generation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.exception("\n❌ Error: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
