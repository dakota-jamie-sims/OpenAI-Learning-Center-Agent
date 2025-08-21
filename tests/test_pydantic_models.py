"""Test Pydantic model validation and serialization"""
import pytest
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.models import (
    ArticleRequest, ArticleResponse, MetadataGeneration,
    ResearchResult, ValidationResult, AgentTask, AgentResponse
)
from src.agents.multi_agent_base import AgentMessage, MessageType


class TestArticleRequest:
    """Test ArticleRequest model validation"""
    
    def test_valid_article_request(self):
        request = ArticleRequest(topic="Private Equity Trends")
        assert request.topic == "Private Equity Trends"
        assert request.word_count == 2000  # default
        assert request.include_metadata == True
    
    def test_topic_validation(self):
        # Empty topic should fail
        with pytest.raises(ValueError, match="at least 1 character"):
            ArticleRequest(topic="")
        
        # Whitespace-only topic should fail
        with pytest.raises(ValueError, match="Topic cannot be empty"):
            ArticleRequest(topic="   ")
    
    def test_word_count_validation(self):
        # Too low
        with pytest.raises(ValueError, match="greater than or equal to 100"):
            ArticleRequest(topic="Test", word_count=50)
        
        # Too high
        with pytest.raises(ValueError, match="less than or equal to 10000"):
            ArticleRequest(topic="Test", word_count=20000)
    
    def test_serialization(self):
        request = ArticleRequest(topic="Test Topic", word_count=1500)
        data = request.model_dump()
        assert data["topic"] == "Test Topic"
        assert data["word_count"] == 1500
        
        # Recreate from dict
        request2 = ArticleRequest.model_validate(data)
        assert request2 == request


class TestMetadataGeneration:
    """Test MetadataGeneration model validation"""
    
    def test_valid_metadata(self):
        metadata = MetadataGeneration(
            title="Test Article",
            description="A test article description",
            keywords=["test", "article"],
            category="Testing",
            target_audience="Developers",
            read_time_minutes=5,
            key_takeaways=["Learning Pydantic"],
            seo_title="Test Article SEO",
            seo_description="SEO description for test",
            publication_date="2024-01-15"
        )
        assert metadata.title == "Test Article"
        assert len(metadata.keywords) == 2
    
    def test_keyword_validation(self):
        # Empty keywords list should fail
        with pytest.raises(ValueError, match="at least 1 item"):
            MetadataGeneration(
                title="Test",
                description="Test",
                keywords=[],
                category="Test",
                target_audience="Test",
                read_time_minutes=5,
                key_takeaways=["Test"],
                seo_title="Test",
                seo_description="Test",
                publication_date="2024-01-15"
            )
    
    def test_date_validation(self):
        # Valid ISO format
        metadata = MetadataGeneration(
            title="Test",
            description="Test",
            keywords=["test"],
            category="Test",
            target_audience="Test",
            read_time_minutes=5,
            key_takeaways=["Test"],
            seo_title="Test",
            seo_description="Test",
            publication_date=datetime.now().isoformat()
        )
        assert metadata.publication_date
        
        # Invalid date should fail
        with pytest.raises(ValueError, match="Invalid date format"):
            MetadataGeneration(
                title="Test",
                description="Test",
                keywords=["test"],
                category="Test",
                target_audience="Test",
                read_time_minutes=5,
                key_takeaways=["Test"],
                seo_title="Test",
                seo_description="Test",
                publication_date="not-a-date"
            )


class TestArticleResponse:
    """Test ArticleResponse model validation"""
    
    def test_successful_response(self):
        response = ArticleResponse(
            success=True,
            article="This is the article content",
            word_count=100
        )
        assert response.success == True
        assert response.article == "This is the article content"
    
    def test_article_validation(self):
        # Success=True with empty article should fail
        with pytest.raises(ValueError, match="Article content cannot be empty"):
            ArticleResponse(success=True, article="")
    
    def test_failed_response(self):
        # Failed response can have empty article
        response = ArticleResponse(
            success=False,
            article="",
            error="Generation failed"
        )
        assert response.success == False
        assert response.error == "Generation failed"
    
    def test_field_aliases(self):
        # Test that both 'article' and 'article_content' work
        data = {
            "success": True,
            "article_content": "Content here",  # Using alias
            "word_count": 150
        }
        response = ArticleResponse.model_validate(data)
        assert response.article == "Content here"


class TestAgentMessage:
    """Test AgentMessage Pydantic model"""
    
    def test_valid_message(self):
        msg = AgentMessage(
            from_agent="agent1",
            to_agent="agent2",
            message_type=MessageType.REQUEST,
            task="test_task",
            payload={"data": "test"},
            context={}
        )
        assert msg.from_agent == "agent1"
        assert msg.message_id is not None  # Auto-generated
        assert msg.timestamp is not None  # Auto-generated
    
    def test_message_serialization(self):
        msg = AgentMessage(
            from_agent="agent1",
            to_agent="agent2",
            message_type=MessageType.REQUEST,
            task="test_task",
            payload={"data": "test"},
            context={}
        )
        
        # Convert to dict
        data = msg.to_dict()
        assert data["from_agent"] == "agent1"
        assert data["message_type"] == "request"  # Enum value
        
        # Recreate from dict
        msg2 = AgentMessage.from_dict(data)
        assert msg2.from_agent == msg.from_agent
        assert msg2.message_id == msg.message_id


class TestValidationResult:
    """Test ValidationResult model"""
    
    def test_accuracy_score_validation(self):
        # Valid score
        result = ValidationResult(
            is_valid=True,
            word_count=1000,
            source_count=5,
            dakota_urls_found=True,
            issues=[],
            recommendations=[],
            accuracy_score=85.5
        )
        assert result.accuracy_score == 85.5
        
        # Score too high
        with pytest.raises(ValueError, match="between 0 and 100"):
            ValidationResult(
                is_valid=True,
                word_count=1000,
                source_count=5,
                dakota_urls_found=True,
                issues=[],
                recommendations=[],
                accuracy_score=101
            )


class TestAgentTask:
    """Test AgentTask model"""
    
    def test_priority_validation(self):
        # Valid priority
        task = AgentTask(
            task_id="task1",
            task_type="research",
            description="Research task",
            priority="high"
        )
        assert task.priority == "high"
        
        # Invalid priority
        with pytest.raises(ValueError, match="string does not match regex"):
            AgentTask(
                task_id="task1",
                task_type="research",
                description="Research task",
                priority="urgent"  # Not in allowed values
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])