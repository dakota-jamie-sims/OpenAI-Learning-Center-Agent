import json

import pytest
from pydantic import ValidationError

from src.models import ArticleRequest, MetadataGeneration


def test_article_request_validation():
    # topic must be a string
    with pytest.raises(ValidationError):
        ArticleRequest(topic=123)


def test_metadata_generation_serialization():
    metadata = MetadataGeneration(
        title="Test",
        description="Desc",
        keywords=["a", "b"],
        category="Cat",
        target_audience="Investors",
        read_time_minutes=5,
        key_takeaways=["k1"],
        related_topics=["t1"],
        seo_title="SEO Title",
        seo_description="SEO Desc",
        publication_date="2024-01-01",
    )
    json_str = metadata.model_dump_json()
    data = json.loads(json_str)
    assert data["title"] == "Test"


def test_metadata_generation_validation_error():
    # keywords should be a list, not a string
    with pytest.raises(ValidationError):
        MetadataGeneration(
            title="T",
            description="D",
            keywords="not a list",
            category="Cat",
            target_audience="Investors",
            read_time_minutes="ten",
            key_takeaways=[],
            related_topics=[],
            seo_title="SEO",
            seo_description="SEO",
            publication_date="2024-01-01",
        )
