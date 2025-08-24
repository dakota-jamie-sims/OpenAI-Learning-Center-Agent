"""Dakota KB Researcher Agent - Searches Dakota knowledge base"""

import asyncio
import json
import os
from typing import Dict, Any, List, Optional

from .base_agent import DakotaBaseAgent
from src.services.kb_search_optimized import OptimizedKBSearcher
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DakotaKBResearcher(DakotaBaseAgent):
    """Knowledge base researcher that searches Dakota's existing content"""
    
    def __init__(self):
        super().__init__("kb_researcher", model_override="gpt-5-mini")
        self.kb_searcher = OptimizedKBSearcher()
        self.article_index = self._load_article_index()
        
        # Try to import ArticleMatcher for enhanced related article selection
        self.article_matcher = None
        try:
            from src.utils.article_matcher import ArticleMatcher
            self.article_matcher = ArticleMatcher()
            self.logger.info("ArticleMatcher loaded successfully for enhanced article matching")
        except Exception as e:
            self.logger.warning(f"ArticleMatcher not available: {e}. Using basic matching.")
        
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
                max_results=5,  # Reduced for performance
                timeout=5  # Reduced timeout
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
                for i, result in enumerate(kb_results["results"][:10]):
                    # Extract article info
                    title = result.get("title", f"Dakota Article {i+1}")
                    content_snippet = result.get("content", "")[:200]
                    
                    # Try to find URL from article index first
                    url = self._get_url_from_index(title)
                    if not url:
                        # Try to extract actual URL from content
                        url = self._extract_url_from_content(result.get("content", ""))
                        if not url:
                            url = self._generate_dakota_url(title)
                    
                    # Create source entry
                    sources.append({
                        "title": title,
                        "url": url,
                        "snippet": content_snippet,
                        "type": "dakota_kb",
                        "relevance_score": result.get("score", 0.8)
                    })
                    
                    # Add to related articles if highly relevant
                    if i < 3:  # Top 3 most relevant
                        related_articles.append({
                            "title": title,
                            "url": url,
                            "description": self._extract_description(content_snippet),
                            "relevance": "High relevance to current topic"
                        })
            
            # Use ArticleMatcher for enhanced related article selection if available
            if self.article_matcher:
                try:
                    self.logger.info("Using ArticleMatcher for enhanced related article selection")
                    # Get sophisticated matches
                    matched_articles = self.article_matcher.find_related_articles(
                        topic=topic,
                        exclude_title=None,  # Don't exclude any since we're looking for related content
                        max_results=5
                    )
                    
                    # Replace basic related articles with sophisticated matches
                    if matched_articles:
                        related_articles = []
                        for match in matched_articles[:3]:  # Top 3 matches
                            related_articles.append({
                                "title": match["title"],
                                "url": match["url"],
                                "description": match["description"],
                                "relevance": f"Score: {match['score']:.2f} - Matching categories: {', '.join([cat for cat, matches in match['matching_categories'].items() if matches])}"
                            })
                        self.logger.info(f"Found {len(related_articles)} enhanced related articles")
                except Exception as e:
                    self.logger.warning(f"Error using ArticleMatcher: {e}. Using basic matches.")
            
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
    
    def _extract_url_from_content(self, content: str) -> Optional[str]:
        """Extract actual URL from article content"""
        import re
        
        # Look for patterns like "Original URL: https://..."
        url_pattern = r'Original URL:\s*(https?://[^\s\n]+)'
        match = re.search(url_pattern, content)
        if match:
            return match.group(1).strip()
        
        # Also try pattern without "Original"
        url_pattern2 = r'URL:\s*(https?://www\.dakota\.com[^\s\n]+)'
        match2 = re.search(url_pattern2, content)
        if match2:
            return match2.group(1).strip()
        
        return None
    
    def _generate_dakota_url(self, title: str) -> str:
        """Generate Dakota Learning Center URL from title"""
        # Clean title and create URL slug
        slug = title.lower()
        slug = slug.replace(' ', '-')
        slug = slug.replace(':', '')
        slug = slug.replace(',', '')
        slug = slug.replace('&', 'and')
        slug = slug.replace('?', '')
        slug = slug.replace('!', '')
        slug = slug.replace('(', '')
        slug = slug.replace(')', '')
        slug = slug.replace('"', '')
        slug = slug.replace("'", '')
        slug = slug.replace('.', '')
        slug = slug.replace('/', '-')
        slug = slug.replace('--', '-')
        
        # Common Learning Center URL patterns
        if 'rfi' in slug or 'rfp' in slug:
            return f"https://www.dakota.com/learning-center/rfp-database/{slug}"
        elif 'allocation' in slug or 'search' in slug:
            return f"https://www.dakota.com/learning-center/allocations/{slug}"
        elif 'due-diligence' in slug:
            return f"https://www.dakota.com/learning-center/due-diligence/{slug}"
        else:
            return f"https://www.dakota.com/learning-center/{slug}"
    
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
    
    def _load_article_index(self) -> Dict[str, Dict[str, str]]:
        """Load the article index with URLs"""
        try:
            # Get path to article index
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            index_path = os.path.join(project_root, "data", "knowledge_base", "article_index.json")
            
            if os.path.exists(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                self.logger.warning(f"Article index not found at {index_path}")
                return {}
        except Exception as e:
            self.logger.error(f"Error loading article index: {e}")
            return {}
    
    def _get_url_from_index(self, title: str) -> Optional[str]:
        """Get URL from article index"""
        if title in self.article_index:
            return self.article_index[title].get("url", "")
        
        # Try partial matching for titles that might not be exact
        for indexed_title, info in self.article_index.items():
            if title.lower() in indexed_title.lower() or indexed_title.lower() in title.lower():
                return info.get("url", "")
        
        return None
    
    def get_topic_recommendations(self, current_market_trends: List[str] = None) -> List[Dict[str, str]]:
        """Get topic recommendations using ArticleMatcher if available"""
        if self.article_matcher:
            try:
                return self.article_matcher.get_topic_recommendations(current_market_trends)
            except Exception as e:
                self.logger.error(f"Error getting topic recommendations: {e}")
        
        # Fallback recommendations
        return [
            {
                "topic": "Private Credit Strategies for 2025",
                "rationale": "Growing interest in private credit markets",
                "priority": "high",
                "category": "market_analysis"
            },
            {
                "topic": "Family Office Investment Trends",
                "rationale": "Evolving preferences among family offices",
                "priority": "high",
                "category": "investor_type"
            }
        ]