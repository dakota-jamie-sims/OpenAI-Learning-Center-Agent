#!/usr/bin/env python3
"""
Test script for the multi-agent article generation system
"""
import argparse
import json
import sys
from datetime import datetime

from learning_center_agent.config import MIN_WORD_COUNT
from learning_center_agent.pipeline.multi_agent_orchestrator import (
    get_multi_agent_orchestrator,
)


def test_article_generation(topic: str, word_count: int):
    """Test article generation with multi-agent system"""
    print(f"\n{'='*60}")
    print("🧪 MULTI-AGENT SYSTEM TEST")
    print(f"{'='*60}")
    
    # Get orchestrator
    orchestrator = get_multi_agent_orchestrator()
    
    # Show agent status
    print("\n📊 Agent Network Status:")
    status = orchestrator.get_agent_status()
    print(json.dumps(status, indent=2))
    
    # Generate article
    print(f"\n🚀 Generating article on: {topic}")
    print(f"   Target word count: {word_count}")
    
    start_time = datetime.now()
    result = orchestrator.generate_article(topic, word_count)
    end_time = datetime.now()
    
    generation_time = (end_time - start_time).total_seconds()
    
    if result.get("success"):
        print(f"\n✅ SUCCESS!")
        print(f"\n📈 Metrics:")
        print(f"   - Word Count: {result['metrics']['word_count']}")
        print(f"   - Quality Score: {result['metrics']['quality_score']:.1f}/10")
        print(f"   - Generation Time: {generation_time:.1f} seconds")
        print(f"   - Output Directory: {result['output_directory']}")
        
        # Show involved agents
        print(f"\n🤖 Agents Involved:")
        for agent_type, count in result['metrics']['agents_involved'].items():
            print(f"   - {agent_type}: {count}")
        
        # Show communication stats
        print(f"\n📡 Communication Stats:")
        comm_stats = orchestrator.message_broker.get_stats()
        print(f"   - Messages Sent: {comm_stats['messages_sent']}")
        print(f"   - Messages Delivered: {comm_stats['messages_delivered']}")
        print(f"   - Delivery Rate: {comm_stats['delivery_rate']:.1f}%")
        
        # Preview article
        print(f"\n📄 Article Preview:")
        print(f"{'='*60}")
        print(result['article'][:500] + "...")
        print(f"{'='*60}")
        
        # Show quality report summary
        if 'quality_report' in result:
            quality = result['quality_report']
            print(f"\n✅ Quality Report:")
            print(f"   - Overall Score: {quality.get('overall_quality_score', 0):.1f}/10")
            print(f"   - Grade: {quality.get('quality_grade', 'N/A')}")
            print(f"   - Ready for Publication: {quality.get('ready_for_publication', False)}")
            
            if 'recommendations' in quality:
                print(f"\n💡 Recommendations:")
                for rec in quality['recommendations'][:3]:
                    print(f"   - {rec}")
        
        # Files created
        print(f"\n📁 Files Created:")
        for file_type, file_path in result['files'].items():
            print(f"   - {file_type}: {Path(file_path).name}")
        
        return True
        
    else:
        print(f"\n❌ FAILED!")
        print(f"   Error: {result.get('error', 'Unknown error')}")
        print(f"   Phase Failed: {result.get('phase_failed', 'Unknown')}")
        
        if 'details' in result:
            print(f"\n🔍 Error Details:")
            print(json.dumps(result['details'], indent=2))
        
        return False


def test_article_review(article_path: str):
    """Test article review functionality"""
    print(f"\n{'='*60}")
    print("🔍 ARTICLE REVIEW TEST")
    print(f"{'='*60}")
    
    # Read article
    with open(article_path, 'r', encoding='utf-8') as f:
        article = f.read()
    
    # Get orchestrator
    orchestrator = get_multi_agent_orchestrator()
    
    # Review article
    print(f"\n🔍 Reviewing article...")
    result = orchestrator.review_article(article, "comprehensive")
    
    if result.get("success"):
        print(f"\n✅ Review Complete!")
        
        assessment = result['overall_assessment']
        print(f"\n📊 Overall Assessment:")
        print(f"   - Status: {assessment['overall_status']}")
        print(f"   - Confidence: {assessment['confidence']}")
        print(f"   - Key Issues: {len(assessment['key_issues'])}")
        print(f"   - Requires Revision: {result['requires_revision']}")
        
        if assessment['key_issues']:
            print(f"\n⚠️ Key Issues:")
            for issue in assessment['key_issues'][:5]:
                print(f"   - {issue}")
        
        if assessment['strengths']:
            print(f"\n💪 Strengths:")
            for strength in assessment['strengths'][:5]:
                print(f"   - {strength}")
        
        if result['priority_recommendations']:
            print(f"\n💡 Priority Recommendations:")
            for rec in result['priority_recommendations']:
                print(f"   - {rec}")
        
        return True
    else:
        print(f"\n❌ Review Failed!")
        print(f"   Error: {result.get('error', 'Unknown error')}")
        return False


def test_batch_generation(topics: list, word_count: int):
    """Test batch article generation"""
    print(f"\n{'='*60}")
    print("📚 BATCH GENERATION TEST")
    print(f"{'='*60}")
    
    # Get orchestrator
    orchestrator = get_multi_agent_orchestrator()
    
    # Generate batch
    print(f"\n📝 Topics to generate:")
    for i, topic in enumerate(topics, 1):
        print(f"   {i}. {topic}")
    
    results = orchestrator.generate_batch(topics, word_count)
    
    # Summary
    successful = sum(1 for r in results if r["result"].get("success"))
    
    print(f"\n📊 Batch Results:")
    print(f"   - Total: {len(results)}")
    print(f"   - Successful: {successful}")
    print(f"   - Failed: {len(results) - successful}")
    
    # Details
    for result in results:
        status = "✅" if result["result"].get("success") else "❌"
        topic = result["topic"]
        
        if result["result"].get("success"):
            score = result["result"]["metrics"]["quality_score"]
            words = result["result"]["metrics"]["word_count"]
            print(f"\n{status} {topic}")
            print(f"     Quality: {score:.1f}/10 | Words: {words}")
        else:
            error = result["result"].get("error", "Unknown error")
            print(f"\n{status} {topic}")
            print(f"     Error: {error}")
    
    return successful == len(results)


def main():
    """Main test function"""
    parser = argparse.ArgumentParser(description="Test multi-agent article generation")
    parser.add_argument("--topic", type=str, 
                       default="The Impact of AI on Alternative Investment Strategies",
                       help="Article topic")
    parser.add_argument("--word-count", type=int, default=MIN_WORD_COUNT,
                       help="Target word count")
    parser.add_argument("--test", type=str, default="generate",
                       choices=["generate", "review", "batch", "all"],
                       help="Test type to run")
    parser.add_argument("--article-path", type=str,
                       help="Path to article for review test")
    
    args = parser.parse_args()
    
    try:
        if args.test in ["generate", "all"]:
            success = test_article_generation(args.topic, args.word_count)
            if not success and args.test == "all":
                print("\n⚠️ Skipping remaining tests due to generation failure")
                return
        
        if args.test in ["review", "all"]:
            if args.article_path:
                test_article_review(args.article_path)
            else:
                print("\n⚠️ Skipping review test - no article path provided")
        
        if args.test in ["batch", "all"]:
            test_topics = [
                "Best Practices for Private Equity Due Diligence",
                "Understanding ESG Integration in Hedge Funds",
                "The Role of AI in Portfolio Construction"
            ]
            test_batch_generation(test_topics[:2], 1000)  # Short articles for testing
        
        # Final metrics
        print(f"\n{'='*60}")
        print("📊 FINAL METRICS")
        print(f"{'='*60}")
        
        orchestrator = get_multi_agent_orchestrator()
        metrics = orchestrator.get_metrics()
        
        print("\n🎯 Orchestrator Performance:")
        orch_metrics = metrics['orchestrator_metrics']['metrics']
        print(f"   - Articles Generated: {orch_metrics['articles_generated']}")
        print(f"   - Average Quality: {orch_metrics['average_quality_score']:.1f}/10")
        print(f"   - Success Rate: {orch_metrics['success_rate']:.1f}%")
        
        print("\n📡 Communication Performance:")
        comm_stats = metrics['communication_stats']
        print(f"   - Total Messages: {comm_stats['messages_sent']}")
        print(f"   - Delivery Rate: {comm_stats['delivery_rate']:.1f}%")
        print(f"   - Active Agents: {comm_stats['agents_registered']}")
        
        # Shutdown
        print(f"\n🛑 Shutting down...")
        orchestrator.shutdown()
        
        print(f"\n✅ All tests completed!")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        orchestrator = get_multi_agent_orchestrator()
        orchestrator.shutdown()
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        orchestrator = get_multi_agent_orchestrator()
        orchestrator.shutdown()


if __name__ == "__main__":
    main()