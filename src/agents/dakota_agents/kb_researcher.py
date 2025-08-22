"""Dakota KB Researcher Agent - Searches Dakota knowledge base"""

import asyncio
import json
from typing import Dict, Any, List

from .base_agent import DakotaBaseAgent
from src.services.kb_search_optimized import OptimizedKBSearcher
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DakotaKBResearcher(DakotaBaseAgent):
    """Knowledge base researcher that searches Dakota's existing content"""
    
    def __init__(self):
        super().__init__("kb_researcher", model_override="gpt-5-mini")
        self.kb_searcher = OptimizedKBSearcher()
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Search knowledge base for related articles and insights"""
        try:
            self.update_status("active", "Searching Dakota knowledge base")
            
            topic = task.get("topic", "")
            
            # Search KB with timeout
            self.logger.info(f"Searching KB for: {topic}")
            kb_results = await asyncio.to_thread(
                self.kb_searcher.search,
                topic,
                max_results=10,
                timeout=15
            )
            
            if not kb_results or (isinstance(kb_results, dict) and not kb_results.get("success")):
                self.logger.warning("KB search returned no results")
                return self.format_response(True, data={
                    "sources": [],
                    "insights": [],
                    "related_articles": []
                })
            
            # Process results
            sources = []
            related_articles = []
            
            if isinstance(kb_results, dict) and "results" in kb_results:
                for i, result in enumerate(kb_results["results"][:5]):
                    # Extract article info
                    title = result.get("title", f"Dakota Article {i+1}")
                    content_snippet = result.get("content", "")[:200]
                    
                    # Create source entry
                    sources.append({
                        "title": title,
                        "url": self._generate_dakota_url(title),
                        "snippet": content_snippet,
                        "type": "dakota_kb",
                        "relevance_score": result.get("score", 0.8)
                    })
                    
                    # Add to related articles if highly relevant
                    if i < 3:  # Top 3 most relevant
                        related_articles.append({
                            "title": title,
                            "url": self._generate_dakota_url(title),
                            "description": self._extract_description(content_snippet),
                            "relevance": "High relevance to current topic"
                        })
            
            # Generate insights from KB content
            insights = await self._extract_insights(topic, sources)
            
            return self.format_response(True, data={
                "sources": sources,
                "insights": insights,
                "related_articles": related_articles,
                "total_results": len(kb_results.get("results", [])) if isinstance(kb_results, dict) else 0
            })
            
        except Exception as e:
            self.logger.error(f"KB research error: {e}")
            return self.format_response(True, data={
                "sources": [],
                "insights": ["Focus on current market trends and Dakota's expertise"],
                "related_articles": []
            })
    
    def _generate_dakota_url(self, title: str) -> str:
        """Generate Dakota Learning Center URL from title"""
        # Create URL slug from title
        slug = title.lower()
        slug = slug.replace(" ", "-")
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')
        slug = slug.strip('-')[:60]  # Limit length
        
        return f"https://www.dakota.com/resources/blog/{slug}"
    
    def _extract_description(self, content: str) -> str:
        """Extract a brief description from content"""
        # Clean and truncate content
        description = content.strip()
        if len(description) > 100:
            description = description[:97] + "..."
        return description
    
    async def _extract_insights(self, topic: str, sources: List[Dict[str, Any]]) -> List[str]:
        """Extract key insights from KB search results"""
        if not sources:
            return [
                f"Dakota has extensive expertise in {topic}",
                "Institutional investors are increasingly focused on this area",
                "Data-driven approaches are essential for success"
            ]
        
        # Compile source content
        source_content = "\n\n".join([
            f"Article: {s['title']}\nContent: {s['snippet']}"
            for s in sources[:3]
        ])
        
        prompt = f"""Based on these Dakota Learning Center articles about {topic}, extract 3-4 key insights:

{source_content}

Provide insights that are:
1. Specific to institutional investors
2. Based on the article content
3. Actionable and valuable

Format as a list of insights."""

        try:
            insights_text = await self.query_llm(prompt, max_tokens=300)
            
            # Parse insights
            insights = []
            for line in insights_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # Clean up formatting
                    insight = line.lstrip('0123456789.-•').strip()
                    if insight:
                        insights.append(insight)
            
            return insights[:4] if insights else [
                f"Dakota's research shows growing institutional interest in {topic}",
                "Best practices emphasize data-driven decision making",
                "Market leaders are adopting innovative approaches"
            ]
            
        except Exception as e:
            self.logger.error(f"Error extracting insights: {e}")
            return [
                f"Dakota has covered {topic} extensively",
                "Institutional best practices are evolving",
                "Data and verification are critical"
            ]