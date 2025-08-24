"""KB Researcher using optimized search with caching"""

from typing import Dict, Any, List
import asyncio

from .base_agent import DakotaBaseAgent
from src.services.kb_search_optimized_v2 import search_kb_optimized
from src.utils.article_matcher import ArticleMatcher
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DakotaKBResearcherOptimized(DakotaBaseAgent):
    """KB researcher using optimized cached search"""
    
    def __init__(self):
        super().__init__("kb_researcher", model_override="gpt-4o-mini")
        try:
            self.article_matcher = ArticleMatcher()
            self.logger.info("ArticleMatcher loaded successfully")
        except Exception as e:
            self.logger.warning(f"ArticleMatcher not available: {e}")
            self.article_matcher = None
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute KB research with optimized search"""
        topic = task.get("topic", "")
        
        self.update_status("active", f"Optimized KB search for: {topic}")
        
        try:
            # Use optimized search with caching
            self.logger.info(f"Searching KB with cache for: {topic}")
            search_result = await asyncio.to_thread(
                search_kb_optimized, 
                topic, 
                max_results=5
            )
            
            # Check if we got results
            if not search_result.get("success") and not search_result.get("results"):
                self.logger.warning("KB search returned no results")
                return self.format_response(True, data={
                    "sources": [],
                    "insights": ["No specific Dakota KB articles found for this topic."],
                    "related_articles": []
                })
            
            # Extract sources
            sources = []
            if search_result.get("citations"):
                for citation in search_result["citations"][:5]:
                    sources.append({
                        "title": citation.get("filename", "Dakota KB Article"),
                        "url": f"dakota-kb://{citation.get('file_id', '')}",
                        "description": citation.get("content", "")[:200] + "..."
                    })
            
            # Extract insights
            insights = []
            if search_result.get("results"):
                insight = await self._extract_key_insight(search_result["results"], topic)
                if insight:
                    insights.append(insight)
            
            # Get related articles if matcher available
            related_articles = []
            if self.article_matcher and sources:
                try:
                    matches = self.article_matcher.find_related_articles(
                        query=topic,
                        search_results=search_result.get("results", ""),
                        top_k=3
                    )
                    related_articles = [
                        {
                            "title": match["title"],
                            "url": match["url"],
                            "relevance_score": match["score"]
                        }
                        for match in matches
                    ]
                except Exception as e:
                    self.logger.warning(f"Article matching failed: {e}")
            
            self.update_status("completed", f"Found {len(sources)} KB sources")
            
            return self.format_response(True, data={
                "sources": sources,
                "insights": insights,
                "related_articles": related_articles
            })
            
        except Exception as e:
            self.logger.error(f"KB research error: {e}")
            return self.format_response(False, error=str(e))
    
    async def _extract_key_insight(self, search_results: str, topic: str) -> str:
        """Extract one key insight from search results"""
        if not search_results or len(search_results) < 50:
            return ""
        
        prompt = f"""Based on these Dakota KB search results about "{topic}", provide ONE key insight:

{search_results[:1000]}

Return only the insight in one sentence."""
        
        try:
            insight = await self.query_llm(prompt, max_tokens=100, reasoning_effort="minimal")
            return insight.strip()
        except:
            return ""