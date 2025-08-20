"""
Data models for the article generation system
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class ArticleRequest:
    """Request model for article generation"""
    topic: str
    word_count: int = 2000
    audience: str = "institutional investors and financial professionals"
    tone: str = "professional yet conversational"
    custom_instructions: Optional[str] = None
    include_metadata: bool = True
    include_social: bool = True
    include_summary: bool = True
    

@dataclass
class ArticleResponse:
    """Response model for generated articles"""
    success: bool
    article: str  # Changed from article_content to match usage
    metadata: Optional['MetadataGeneration'] = None  # Forward reference
    word_count: Optional[int] = None
    summary: Optional[str] = None
    social_posts: Optional[Dict[str, str]] = None
    fact_check_results: Optional[Dict[str, Any]] = None
    sources: Optional[List[Dict[str, str]]] = None
    generation_time: Optional[float] = None
    output_directory: Optional[str] = None
    error: Optional[str] = None
    quality_metrics: Optional[Dict[str, Any]] = None
    

@dataclass
class MetadataGeneration:
    """Metadata for article generation"""
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
    

@dataclass
class ResearchResult:
    """Result from research operations"""
    topic: str
    findings: List[Dict[str, Any]]
    sources: List[Dict[str, str]]
    key_insights: List[str]
    statistics: List[Dict[str, Any]]
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ValidationResult:
    """Result from content validation"""
    is_valid: bool
    word_count: int
    source_count: int
    dakota_urls_found: bool
    issues: List[str]
    recommendations: List[str]
    accuracy_score: float = 0.0
    

@dataclass
class AgentTask:
    """Task assignment for agents"""
    task_id: str
    task_type: str
    description: str
    payload: Dict[str, Any]
    priority: str = "medium"
    deadline: Optional[str] = None
    assigned_to: Optional[str] = None
    status: str = "pending"
    

@dataclass
class AgentResponse:
    """Standard response from agents"""
    agent_id: str
    task_id: str
    status: str
    result: Any
    error: Optional[str] = None
    processing_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None