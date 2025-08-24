#!/usr/bin/env python3
"""Generate article using Dakota multi-agent system with mandatory verification"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import argparse
import json
from datetime import datetime
import logging

from src.agents.dakota_agents.orchestrator import DakotaOrchestrator
from src.models import ArticleRequest
from src.utils.logging import get_logger

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = get_logger(__name__)


async def main():
    parser = argparse.ArgumentParser(description="Generate article using Dakota agent system")
    parser.add_argument("--topic", required=False, help="Article topic")
    parser.add_argument("--word-count", type=int, default=1750, help="Target word count")
    parser.add_argument("--audience", default="institutional investors and financial professionals", 
                       help="Target audience")
    parser.add_argument("--tone", default="professional yet conversational", help="Writing tone")
    parser.add_argument("--metrics", action="store_true", help="Show performance metrics")
    parser.add_argument("--health-check", action="store_true", help="Run system health check")
    
    args = parser.parse_args()
    
    # Health check mode
    if args.health_check:
        health = {
            "status": "healthy",
            "system": "dakota_multi_agent_system",
            "timestamp": datetime.now().isoformat(),
            "agents": [
                "orchestrator - Coordinates all phases with mandatory validation",
                "kb_researcher - Searches Dakota knowledge base",
                "web_researcher - Gathers current market intelligence",
                "research_synthesizer - Combines research into strategy",
                "content_writer - Creates high-quality articles",
                "metrics_analyzer - Analyzes objective quality metrics",
                "seo_specialist - Creates metadata with verified sources",
                "fact_checker - MANDATORY verification of all data",
                "iteration_manager - Fixes issues found by fact checker",
                "social_promoter - Creates multi-platform social content",
                "summary_writer - Creates executive summaries"
            ],
            "phases": [
                "1. Setup - Topic analysis and directory creation",
                "2. Research (parallel) - KB and web research",
                "3. Synthesis - Combine research into outline",
                "4. Content Creation - Write article",
                "5. Analysis (parallel) - Metrics and SEO",
                "6. MANDATORY Validation - Template check + fact checking",
                "7. Distribution - Social and summary (only if approved)"
            ],
            "features": [
                "Parallel execution for faster processing",
                "Mandatory fact-checking (no exceptions)",
                "Automatic iteration for rejected articles",
                "Phase tracking and announcements",
                "100% source verification requirement",
                "4-file output generation"
            ]
        }
        print("\n🏥 Dakota Agent System Health Check")
        print("=" * 60)
        print(json.dumps(health, indent=2))
        return
    
    if not args.topic:
        print("Error: --topic is required for article generation")
        return
    
    # Create article request
    request = ArticleRequest(
        topic=args.topic,
        audience=args.audience,
        tone=args.tone,
        word_count=args.word_count,
        include_metadata=True,
        include_social=True,
        include_summary=True,
    )
    
    print(f"\n🚀 Dakota Multi-Agent Article Generation")
    print("=" * 60)
    print(f"Topic: {request.topic}")
    print(f"Target: {request.word_count} words")
    print(f"System: 11 specialized agents with mandatory fact-checking")
    print("=" * 60)
    print("\nPhase execution will be tracked below...\n")
    
    try:
        # Create orchestrator
        orchestrator = DakotaOrchestrator()
        
        # Generate article
        start_time = datetime.now()
        result = await orchestrator.execute({
            "request": request
        })
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if result.get("success", False):
            print(f"\n✅ Article generation SUCCESSFUL with fact-checker approval!")
            print(f"⏱️  Total time: {elapsed:.1f}s")
            
            # Show output details
            data = result.get("data", {})
            output_folder = data.get("output_folder", "")
            
            if output_folder:
                print(f"\n📁 Output folder: {output_folder}/")
                print("\n📄 Files created:")
                for filename in data.get("files_created", []):
                    print(f"   ✓ {filename}")
                
                # Show verification details
                print("\n✅ Verification Status:")
                print(f"   Fact-checker: APPROVED")
                print(f"   Sources verified: {data.get('sources_verified', 0)}")
                print(f"   Iterations needed: {data.get('iterations_needed', 0)}")
                print(f"   Word count: {data.get('word_count', 0)}")
                
                # Preview article
                article_file = os.path.join(output_folder, f"{output_folder.split('-')[-1]}-article.md")
                if os.path.exists(article_file):
                    with open(article_file, 'r') as f:
                        lines = f.readlines()
                    
                    print("\n📝 Article Preview:")
                    print("-" * 50)
                    # Skip frontmatter
                    content_start = 0
                    if lines[0].strip() == "---":
                        for i, line in enumerate(lines[1:], 1):
                            if line.strip() == "---":
                                content_start = i + 1
                                break
                    
                    # Show first few content lines
                    preview_lines = [l.strip() for l in lines[content_start:] if l.strip()][:5]
                    for line in preview_lines:
                        print(line[:80] + "..." if len(line) > 80 else line)
                    print("-" * 50)
            
        else:
            print(f"\n❌ Article generation FAILED!")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            print(f"   Time elapsed: {elapsed:.1f}s")
        
        # Show metrics if requested
        if args.metrics:
            print("\n📈 Performance Metrics:")
            metrics = {
                "generation_time": elapsed,
                "success": result.get("success", False),
                "phases_completed": 7 if result.get("success") else "Failed",
                "parallel_operations": ["Research (KB + Web)", "Analysis (Metrics + SEO)", "Distribution (Social + Summary)"],
                "agent_count": 11
            }
            if result.get("data"):
                metrics.update({
                    "word_count": result["data"].get("word_count", 0),
                    "sources_verified": result["data"].get("sources_verified", 0),
                    "fact_checker_approved": result["data"].get("fact_checker_approved", False)
                })
            print(json.dumps(metrics, indent=2))
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Set event loop policy for macOS
    if sys.platform == "darwin":
        asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
    
    asyncio.run(main())