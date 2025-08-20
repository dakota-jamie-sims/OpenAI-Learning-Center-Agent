#!/usr/bin/env python3
"""
Test script for the Multi-Agent System
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.pipeline.multi_agent_orchestrator import MultiAgentPipelineOrchestrator


def test_multi_agent_system():
    """Test the multi-agent system with a sample article"""
    print("\n" + "="*70)
    print("🤖 MULTI-AGENT SYSTEM TEST")
    print("="*70)
    
    orchestrator = MultiAgentPipelineOrchestrator()
    
    # Test topic
    topic = "The Future of Alternative Investments in a Digital Economy"
    
    print(f"\n📝 Test Topic: {topic}")
    print("\n🚀 Starting multi-agent article generation...")
    
    # Generate article
    result = orchestrator.generate_article(
        topic=topic,
        custom_instructions="""
        Focus on:
        1. Digital transformation in alternative investments
        2. Emerging technologies (blockchain, AI, etc.)
        3. Dakota's perspective on innovation
        4. Practical insights for institutional investors
        5. Include recent data and statistics
        """
    )
    
    if result["success"]:
        print("\n✨ SUCCESS! Article generated using multi-agent system")
        print(f"\n📊 Generation Metrics:")
        print(f"   - Word count: {result['word_count']}")
        print(f"   - Output path: {result['output_path']}")
        
        # Show quality metrics if available
        if result.get('quality_metrics'):
            print(f"\n📈 Quality Metrics:")
            for metric, value in result['quality_metrics'].items():
                print(f"   - {metric}: {value}")
        
        # Show metadata
        if result.get('metadata'):
            print(f"\n📋 Article Metadata:")
            metadata = result['metadata']
            print(f"   - Title: {metadata.get('title', 'N/A')}")
            print(f"   - Description: {metadata.get('meta_description', 'N/A')}")
            if metadata.get('key_takeaways'):
                print(f"   - Key Takeaways: {len(metadata['key_takeaways'])} items")
        
        # Show system status
        print(f"\n🔍 System Status Check:")
        status = orchestrator.get_system_status()
        print(f"   - Orchestrator Status: {status.get('orchestrator_status', 'Unknown')}")
        print(f"   - Active Agents: {len(status.get('agent_statuses', {}))}")
        print(f"   - Pipelines Completed: {status.get('pipelines_completed', 0)}")
        
        # Show article preview
        print(f"\n📄 Article Preview (first 500 chars):")
        print("-"*70)
        print(result["article"][:500] + "...")
        print("-"*70)
        
    else:
        print(f"\n❌ FAILED: {result.get('error', 'Unknown error')}")
    
    print("\n✅ Multi-agent system test complete!")


def test_agent_coordination():
    """Test agent coordination and communication"""
    print("\n" + "="*70)
    print("🔄 AGENT COORDINATION TEST")
    print("="*70)
    
    from src.agents.multi_agent_base import AgentMessage, MessageType
    from src.agents.research_agents import WebResearchAgent
    from src.agents.writing_agents import ContentWriterAgent
    from src.agents.quality_agents import FactCheckerAgent
    from datetime import datetime
    
    # Create agents
    researcher = WebResearchAgent()
    writer = ContentWriterAgent()
    fact_checker = FactCheckerAgent()
    
    print("\n📌 Testing direct agent communication...")
    
    # Test 1: Research request
    research_msg = AgentMessage(
        from_agent="test_coordinator",
        to_agent=researcher.agent_id,
        message_type=MessageType.REQUEST,
        task="research_topic",
        payload={"query": "institutional investor trends 2025"},
        context={},
        timestamp=datetime.now().isoformat()
    )
    
    print(f"\n1️⃣ Sending research request to {researcher.agent_id}...")
    research_response = researcher.receive_message(research_msg)
    print(f"   Response: {research_response.payload.get('success', False)}")
    
    # Test 2: Writing request
    writing_msg = AgentMessage(
        from_agent="test_coordinator",
        to_agent=writer.agent_id,
        message_type=MessageType.REQUEST,
        task="write_section",
        payload={
            "section_type": "introduction",
            "content": "Test introduction about institutional investing",
            "tone": "professional"
        },
        context={},
        timestamp=datetime.now().isoformat()
    )
    
    print(f"\n2️⃣ Sending writing request to {writer.agent_id}...")
    writing_response = writer.receive_message(writing_msg)
    print(f"   Response: {writing_response.payload.get('success', False)}")
    
    # Test 3: Fact checking
    fact_msg = AgentMessage(
        from_agent="test_coordinator",
        to_agent=fact_checker.agent_id,
        message_type=MessageType.REQUEST,
        task="verify_facts",
        payload={
            "content": "The S&P 500 returned 26% in 2023.",
            "claims": [{"claim": "S&P 500 returned 26% in 2023", "source": "test"}]
        },
        context={},
        timestamp=datetime.now().isoformat()
    )
    
    print(f"\n3️⃣ Sending fact-check request to {fact_checker.agent_id}...")
    fact_response = fact_checker.receive_message(fact_msg)
    print(f"   Response: {fact_response.payload.get('success', False)}")
    
    print("\n✅ Agent coordination test complete!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Multi-Agent System")
    parser.add_argument("--coordination", action="store_true", 
                       help="Test agent coordination only")
    parser.add_argument("--full", action="store_true",
                       help="Run full article generation test")
    
    args = parser.parse_args()
    
    if args.coordination:
        test_agent_coordination()
    elif args.full or (not args.coordination):
        test_multi_agent_system()
        
    print("\n🎉 All tests completed!")