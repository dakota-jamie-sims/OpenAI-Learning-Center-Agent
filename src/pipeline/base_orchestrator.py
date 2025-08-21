"""
Base orchestrator class with common functionality
"""
import os
import json
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from src.tools.vector_store_handler import VectorStoreHandler
from src.services.openai_responses_client import ResponsesClient
from src.services.kb_search import KnowledgeBaseSearcher
from src.config import DEFAULT_MODELS, OUTPUT_BASE_DIR
from src.utils.logging import get_logger

load_dotenv()

logger = get_logger(__name__)


class BaseOrchestrator:
    """Base class for all orchestrators with common functionality"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.responses_client = ResponsesClient()
        self.output_dir = Path(OUTPUT_BASE_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Vector store for knowledge base
        self.vector_store_id = os.getenv("VECTOR_STORE_ID") or os.getenv("OPENAI_VECTOR_STORE_ID")
        
        if self.vector_store_id:
            self.kb_searcher = KnowledgeBaseSearcher(self.client)
            logger.info("✅ Using existing vector store: %s", self.vector_store_id)
        else:
            self.kb_searcher = None
            logger.warning("⚠️ No vector store configured. Knowledge base search will be limited.")
    
    def search_knowledge_base(self, query: str, max_results: int = 5) -> str:
        """Search the knowledge base"""
        if not self.kb_searcher:
            return "No Dakota knowledge base content available."
        
        result = self.kb_searcher.search(query, max_results)
        
        if result["success"]:
            return result["results"]
        else:
            return f"Knowledge base search failed: {result.get('error', 'Unknown error')}"
    
    def create_response(self, prompt: str, model: Optional[str] = None, 
                       reasoning_effort: str = "medium", verbosity: str = "medium") -> str:
        """Create a response using the Responses API"""
        return self.responses_client.create_response(
            prompt=prompt,
            model=model or DEFAULT_MODELS["default"],
            reasoning_effort=reasoning_effort,
            verbosity=verbosity
        )
    
    def create_output_directory(self, topic: str) -> Path:
        """Create output directory for article"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = "".join(c for c in topic if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_topic = safe_topic.replace(' ', '_')[:50]
        
        dir_name = f"{timestamp}_{safe_topic}"
        article_dir = self.output_dir / dir_name
        article_dir.mkdir(parents=True, exist_ok=True)
        
        return article_dir
    
    def generate_metadata(self, article_content: str, topic: str, date_str: str) -> str:
        """Generate metadata for the article"""
        prompt = f"""Generate comprehensive metadata for this article:

Topic: {topic}
Date: {date_str}

Article Content:
{article_content[:2000]}...

Create JSON metadata including:
- title
- description
- keywords (array)
- category
- target_audience
- read_time_minutes
- key_takeaways (array)
- related_topics (array)
- seo_title
- seo_description
- publication_date
- author
- content_type"""

        response = self.create_response(
            prompt,
            model=DEFAULT_MODELS.get("metadata", DEFAULT_MODELS["default"]),
            reasoning_effort="low",
            verbosity="low"
        )
        
        # Clean up response to ensure valid JSON
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.endswith("```"):
            response = response[:-3]
        
        return response
    
    def fact_check_article(self, article_content: str) -> Dict[str, Any]:
        """Fact check the article content"""
        prompt = f"""Review this article for factual accuracy and provide a detailed fact-check report:

{article_content[:3000]}...

Provide:
1. Claims that need verification
2. Potentially questionable statements
3. Missing citations
4. Overall accuracy assessment (score 1-10)
5. Specific recommendations for improvement

Return as JSON with structure:
{{
    "accuracy_score": <number>,
    "claims_to_verify": [...],
    "questionable_statements": [...],
    "missing_citations": [...],
    "recommendations": [...]
}}"""

        response = self.create_response(
            prompt,
            model=DEFAULT_MODELS.get("fact_checker", DEFAULT_MODELS["default"]),
            reasoning_effort="high",
            verbosity="medium"
        )
        
        try:
            # Clean and parse JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            return json.loads(response)
        except:
            return {
                "accuracy_score": 0,
                "error": "Failed to parse fact-check response",
                "raw_response": response
            }