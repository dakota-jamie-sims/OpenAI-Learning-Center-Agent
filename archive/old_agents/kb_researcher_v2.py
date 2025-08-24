"""KB Researcher V2 - Optimized with batch search and caching"""

import asyncio
from typing import Dict, Any, List

from .base_agent_v2 import DakotaBaseAgentV2
from src.services.kb_search_production_v2 import search_kb_production_v2, batch_search_kb_production_v2
from src.utils.article_matcher import ArticleMatcher
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DakotaKBResearcherV2(DakotaBaseAgentV2):
    """Optimized KB researcher with batch search capabilities"""
    
    def __init__(self):
        super().__init__("kb_researcher", model_override="gpt-5-nano")
        self.article_matcher = ArticleMatcher()
    
    async def _execute_impl(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute KB research with optimizations"""
        topic = task.get("topic", "")
        use_batch = task.get("use_batch_search", True)
        
        self.update_status("active", f"Researching KB for: {topic}")
        
        try:
            # Generate search queries
            queries = await self._generate_search_queries(topic)
            
            # Execute searches
            if use_batch and len(queries) > 1:
                # Batch search for efficiency
                search_results = await batch_search_kb_production_v2(queries, max_results_per_query=3)
            else:
                # Single search
                search_results = [await search_kb_production_v2(queries[0], max_results=5)]
            
            # Process results
            sources = []
            insights = []
            
            for i, result in enumerate(search_results):
                if result.get("success") and result.get("results"):
                    # Extract sources
                    for source in result.get("sources", []):
                        if source not in sources:
                            sources.append(source)
                    
                    # Extract insights
                    insight = await self._extract_insight(result["results"], queries[i] if i < len(queries) else topic)
                    if insight:
                        insights.append(insight)
            
            # Get related articles using matcher
            related_articles = []
            if sources:
                try:
                    matches = self.article_matcher.find_related_articles(
                        query=topic,
                        search_results="\n".join([s.get("title", "") for s in sources]),
                        top_k=5
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
            
            # Compile results
            self.update_status("completed", f"Found {len(sources)} KB sources")
            
            return self.format_response(True, data={
                "sources": sources[:10],  # Top 10 sources
                "insights": insights,
                "related_articles": related_articles,
                "queries_used": queries
            })
            
        except Exception as e:
            self.logger.error(f"KB research error: {e}")
            return self.format_response(False, error=str(e))
    
    async def _generate_search_queries(self, topic: str) -> List[str]:
        """Generate multiple search queries for better coverage"""
        prompt = f"""Generate 3-4 search queries for finding Dakota Knowledge Base articles about: {topic}

Focus on:
1. Main topic keywords
2. Related investor types (family offices, RIAs, etc.)
3. Geographic variations
4. Investment strategies

Return ONLY the queries, one per line."""
        
        try:
            response = await self.query_llm(prompt, max_tokens=200)
            queries = [q.strip() for q in response.strip().split('\n') if q.strip()]
            
            # Always include the original topic
            if topic not in queries:
                queries.insert(0, topic)
            
            return queries[:4]  # Max 4 queries
            
        except:
            # Fallback to simple query
            return [topic]
    
    async def _extract_insight(self, search_results: str, query: str) -> str:
        """Extract key insight from search results"""
        if not search_results:
            return ""
        
        prompt = f"""Extract ONE key insight from these Dakota KB search results for "{query}":

{search_results[:1000]}

Return a single sentence insight that would be valuable for the article."""
        
        try:
            insight = await self.query_llm(prompt, max_tokens=100, use_cache=True)
            return insight.strip()
        except:
            return ""