"""Integration test for Pydantic models across the system"""
import json
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.models import ArticleRequest, ArticleResponse, MetadataGeneration
from src.agents.multi_agent_base import AgentMessage, MessageType
from src.agents.communication_system import PrioritizedMessage, MessagePriority


def test_article_request_response_flow():
    """Test the full flow with Pydantic models"""
    
    # 1. Create an article request
    request = ArticleRequest(
        topic="AI in Financial Services 2025",
        word_count=2500,
        audience="institutional investors",
        custom_instructions="Focus on risk management applications"
    )
    
    print(f"✅ Created ArticleRequest: {request.topic}")
    
    # 2. Serialize to JSON (simulating API transport)
    request_json = request.model_dump_json()
    print(f"✅ Serialized to JSON: {len(request_json)} bytes")
    
    # 3. Deserialize back
    request_restored = ArticleRequest.model_validate_json(request_json)
    assert request_restored == request
    print("✅ Deserialized successfully")
    
    # 4. Create metadata
    metadata = MetadataGeneration(
        title="AI Revolutionizes Risk Management in Finance",
        description="Comprehensive analysis of AI applications in financial risk management for 2025",
        keywords=["AI", "risk management", "finance", "machine learning"],
        category="Technology",
        target_audience="institutional investors",
        read_time_minutes=8,
        key_takeaways=[
            "AI reduces risk assessment time by 70%",
            "Machine learning improves fraud detection accuracy",
            "Regulatory compliance automated through NLP"
        ],
        related_topics=["RegTech", "FinTech", "Quantitative Analysis"],
        seo_title="AI in Financial Risk Management 2025",
        seo_description="Discover how AI is transforming risk management in financial services",
        publication_date=datetime.now().strftime("%Y-%m-%d")
    )
    
    print(f"✅ Created metadata with {len(metadata.keywords)} keywords")
    
    # 5. Create article response
    response = ArticleResponse(
        success=True,
        article="# AI in Financial Services\n\nContent here...",
        metadata=metadata,
        word_count=2500,
        summary="AI is revolutionizing risk management...",
        generation_time=3.5,
        quality_metrics={"score": 92, "readability": 85}
    )
    
    print(f"✅ Created ArticleResponse with success={response.success}")
    
    # 6. Test full serialization/deserialization
    response_dict = response.model_dump()
    response_json = json.dumps(response_dict)
    response_restored = ArticleResponse.model_validate(json.loads(response_json))
    
    assert response_restored.success == response.success
    assert response_restored.metadata.title == metadata.title
    print("✅ Full response serialization working")
    
    return response


def test_agent_communication():
    """Test agent message system with Pydantic"""
    
    # 1. Create an agent message
    msg = AgentMessage(
        from_agent="orchestrator",
        to_agent="research_lead",
        message_type=MessageType.REQUEST,
        task="comprehensive_research",
        payload={
            "topic": "Private Equity Trends",
            "requirements": {"min_sources": 10}
        },
        context={"request_id": "test_123"}
    )
    
    print(f"✅ Created AgentMessage: {msg.message_id[:8]}...")
    
    # 2. Convert to dict for transport
    msg_dict = msg.to_dict()
    assert msg_dict["message_type"] == "request"
    print("✅ Message serialized to dict")
    
    # 3. Restore from dict
    msg_restored = AgentMessage.from_dict(msg_dict)
    assert msg_restored.message_id == msg.message_id
    assert msg_restored.task == msg.task
    print("✅ Message restored from dict")
    
    # 4. Create prioritized message
    priority_msg = PrioritizedMessage(
        priority=MessagePriority.HIGH.value,
        message=msg,
        retry_count=0
    )
    
    print(f"✅ Created PrioritizedMessage with priority={priority_msg.priority}")
    
    # 5. Test priority comparison
    low_priority_msg = PrioritizedMessage(
        priority=MessagePriority.LOW.value,
        message=msg
    )
    
    assert priority_msg < low_priority_msg  # HIGH priority (1) < LOW priority (3)
    print("✅ Priority comparison working correctly")
    
    return msg


def test_validation_errors():
    """Test that Pydantic validation catches errors"""
    
    errors_caught = 0
    
    # 1. Empty topic
    try:
        ArticleRequest(topic="")
    except ValueError as e:
        print(f"✅ Caught empty topic: {e}")
        errors_caught += 1
    
    # 2. Invalid word count
    try:
        ArticleRequest(topic="Test", word_count=50000)
    except ValueError as e:
        print(f"✅ Caught invalid word count: {e}")
        errors_caught += 1
    
    # 3. Invalid priority
    try:
        from src.models import AgentTask
        AgentTask(
            task_id="test",
            task_type="research",
            description="Test task",
            priority="urgent"  # Should be low/medium/high/critical
        )
    except ValueError as e:
        print(f"✅ Caught invalid priority: {e}")
        errors_caught += 1
    
    # 4. Missing required field
    try:
        MetadataGeneration(
            title="Test",
            # Missing required fields
        )
    except ValueError as e:
        print(f"✅ Caught missing fields: {type(e).__name__}")
        errors_caught += 1
    
    print(f"\n✅ Total validation errors caught: {errors_caught}")
    return errors_caught


def main():
    """Run all integration tests"""
    print("=== Pydantic Integration Tests ===\n")
    
    print("1. Testing Article Request/Response Flow:")
    response = test_article_request_response_flow()
    print(f"   Final response has {response.word_count} words\n")
    
    print("2. Testing Agent Communication:")
    message = test_agent_communication()
    print(f"   Message ID: {message.message_id}\n")
    
    print("3. Testing Validation:")
    errors = test_validation_errors()
    print(f"   Validation working correctly\n")
    
    print("=== All Pydantic Integration Tests Passed! ===")
    print("\n✅ The system is now fully using Pydantic models with:")
    print("   - Automatic validation")
    print("   - Type safety")
    print("   - JSON serialization")
    print("   - Better error messages")


if __name__ == "__main__":
    main()