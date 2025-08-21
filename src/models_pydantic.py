"""
Data models for the article generation system using Pydantic
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime


class ArticleRequest(BaseModel):
    """Request model for article generation"""
    topic: str = Field(..., min_length=1, description="Topic for the article")
    word_count: int = Field(default=2000, ge=100, le=10000, description="Target word count")
    audience: str = Field(default="institutional investors and financial professionals")
    tone: str = Field(default="professional yet conversational")
    custom_instructions: Optional[str] = Field(default=None, max_length=1000)
    include_metadata: bool = Field(default=True)
    include_social: bool = Field(default=True)
    include_summary: bool = Field(default=True)
    
    @validator('topic')
    def topic_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Topic cannot be empty or just whitespace')
        return v.strip()
    

class MetadataGeneration(BaseModel):
    """Metadata for article generation"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=500)
    keywords: List[str] = Field(..., min_items=1, max_items=20)
    category: str = Field(...)
    target_audience: str = Field(...)
    read_time_minutes: int = Field(..., ge=1, le=60)
    key_takeaways: List[str] = Field(..., min_items=1, max_items=10)
    related_topics: List[str] = Field(default_factory=list, max_items=10)
    seo_title: str = Field(..., min_length=1, max_length=70)
    seo_description: str = Field(..., min_length=1, max_length=160)
    publication_date: str = Field(...)
    author: str = Field(default="Dakota Learning Center")
    content_type: str = Field(default="article")
    
    @validator('keywords', 'key_takeaways')
    def validate_list_items(cls, v):
        # Remove empty strings and strip whitespace
        return [item.strip() for item in v if item.strip()]
    
    @validator('publication_date')
    def validate_date(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except:
            # If not ISO format, try to parse as date
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except:
                raise ValueError('Invalid date format')
        return v


class ArticleResponse(BaseModel):
    """Response model for generated articles"""
    success: bool
    article: str = Field(alias="article")  # Support both 'article' and 'article_content'
    metadata: Optional[MetadataGeneration] = None
    word_count: Optional[int] = Field(default=None, ge=0)
    summary: Optional[str] = Field(default=None, max_length=1000)
    social_posts: Optional[Dict[str, str]] = None
    fact_check_results: Optional[Dict[str, Any]] = None
    sources: Optional[List[Dict[str, str]]] = None
    generation_time: Optional[float] = Field(default=None, ge=0)
    output_directory: Optional[str] = None
    error: Optional[str] = None
    quality_metrics: Optional[Dict[str, Any]] = None
    
    class Config:
        # Allow both 'article' and 'article_content' field names
        fields = {
            'article': {'alias': 'article_content'}
        }
        populate_by_name = True
    
    @validator('article')
    def validate_article_content(cls, v, values):
        if values.get('success') and not v:
            raise ValueError('Article content cannot be empty when success is True')
        return v


class ResearchResult(BaseModel):
    """Result from research operations"""
    topic: str = Field(..., min_length=1)
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    sources: List[Dict[str, str]] = Field(default_factory=list)
    key_insights: List[str] = Field(default_factory=list)
    statistics: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    @validator('sources')
    def validate_sources(cls, v):
        # Ensure each source has required fields
        for source in v:
            if not isinstance(source, dict):
                raise ValueError('Each source must be a dictionary')
            if 'url' not in source and 'title' not in source:
                raise ValueError('Each source must have at least url or title')
        return v


class ValidationResult(BaseModel):
    """Result from content validation"""
    is_valid: bool
    word_count: int = Field(..., ge=0)
    source_count: int = Field(..., ge=0)
    dakota_urls_found: bool = Field(default=False)
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    accuracy_score: float = Field(default=0.0, ge=0.0, le=100.0)
    
    @validator('accuracy_score')
    def validate_accuracy_score(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('Accuracy score must be between 0 and 100')
        return round(v, 2)


class AgentTask(BaseModel):
    """Task assignment for agents"""
    task_id: str = Field(..., min_length=1)
    task_type: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    payload: Dict[str, Any] = Field(default_factory=dict)
    priority: str = Field(default="medium", regex="^(low|medium|high|critical)$")
    deadline: Optional[str] = None
    assigned_to: Optional[str] = None
    status: str = Field(default="pending", regex="^(pending|in_progress|completed|failed)$")
    
    @validator('deadline')
    def validate_deadline(cls, v):
        if v:
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            except:
                raise ValueError('Invalid deadline format')
        return v


class AgentResponse(BaseModel):
    """Standard response from agents"""
    agent_id: str = Field(..., min_length=1)
    task_id: str = Field(..., min_length=1)
    status: str = Field(..., regex="^(success|failure|partial|timeout)$")
    result: Any
    error: Optional[str] = None
    processing_time: Optional[float] = Field(default=None, ge=0)
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('error')
    def validate_error(cls, v, values):
        if values.get('status') == 'failure' and not v:
            raise ValueError('Error message required when status is failure')
        return v