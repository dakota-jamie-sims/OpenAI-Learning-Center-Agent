from __future__ import annotations

"""
Data models for the article generation system.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ArticleRequest(BaseModel):
    """Request model for article generation."""

    topic: str
    word_count: int = 2000
    audience: str = "institutional investors and financial professionals"
    tone: str = "professional yet conversational"
    custom_instructions: Optional[str] = None
    include_metadata: bool = True
    include_social: bool = True
    include_summary: bool = True


class MetadataGeneration(BaseModel):
    """Metadata for article generation."""

    title: str
    description: str
    keywords: List[str]
    category: str
    target_audience: str
    read_time_minutes: int
    key_takeaways: List[str]
    related_topics: List[str]
    seo_title: str
    seo_description: str
    publication_date: str
    author: str = "Dakota Learning Center"
    content_type: str = "article"


class ArticleResponse(BaseModel):
    """Response model for generated articles."""

    success: bool
    article: str
    metadata: Optional[MetadataGeneration] = None
    word_count: Optional[int] = None
    summary: Optional[str] = None
    social_posts: Optional[Dict[str, str]] = None
    fact_check_results: Optional[Dict[str, Any]] = None
    sources: Optional[List[Dict[str, str]]] = None
    generation_time: Optional[float] = None
    output_directory: Optional[str] = None
    error: Optional[str] = None
    quality_metrics: Optional[Dict[str, Any]] = None


class ResearchResult(BaseModel):
    """Result from research operations."""

    topic: str
    findings: List[Dict[str, Any]]
    sources: List[Dict[str, str]]
    key_insights: List[str]
    statistics: List[Dict[str, Any]]
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ValidationResult(BaseModel):
    """Result from content validation."""

    is_valid: bool
    word_count: int
    source_count: int
    dakota_urls_found: bool
    issues: List[str]
    recommendations: List[str]
    accuracy_score: float = 0.0


class AgentTask(BaseModel):
    """Task assignment for agents."""

    task_id: str
    task_type: str
    description: str
    payload: Dict[str, Any]
    priority: str = "medium"
    deadline: Optional[str] = None
    assigned_to: Optional[str] = None
    status: str = "pending"


class AgentResponse(BaseModel):
    """Standard response from agents."""

    agent_id: str
    task_id: str
    status: str
    result: Any
    error: Optional[str] = None
    processing_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
