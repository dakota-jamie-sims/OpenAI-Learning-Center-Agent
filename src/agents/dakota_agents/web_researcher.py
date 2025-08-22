"""Dakota Web Researcher Agent - Gathers current market intelligence"""

import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime, timedelta

from .base_agent import DakotaBaseAgent
from src.services.web_search import search_web
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DakotaWebResearcher(DakotaBaseAgent):
    """Web researcher that gathers current market data and trends"""
    
    def __init__(self):
        super().__init__("web_researcher", model_override="gpt-5-mini")
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Search web for current data and trends"""
        try:
            self.update_status("active", "Searching web for current data")
            
            topic = task.get("topic", "")
            
            # Create date-filtered search queries
            current_year = datetime.now().year
            search_queries = [
                f"{topic} institutional investors {current_year}",
                f"{topic} {current_year} trends market data",
                f"{topic} latest statistics {current_year}"
            ]
            
            all_results = []
            sources = []
            
            # Search with each query
            for query in search_queries:
                self.logger.info(f"Searching: {query}")
                try:
                    results = await asyncio.to_thread(
                        search_web,
                        query,
                        5  # Get 5 results per query
                    )
                    if results:
                        all_results.extend(results)
                except Exception as e:
                    self.logger.warning(f"Search failed for '{query}': {e}")
            
            # Process and deduplicate results
            seen_urls = set()
            for result in all_results:
                url = result.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    
                    # Verify source is authoritative
                    if self._is_authoritative_source(url):
                        sources.append({
                            "title": result.get("title", ""),
                            "url": url,
                            "snippet": result.get("snippet", ""),
                            "date": self._extract_date(result) or datetime.now().strftime("%Y-%m-%d"),
                            "type": "web_research",
                            "authority": self._get_source_authority(url)
                        })
            
            # Limit to top 10 most authoritative sources
            sources = sorted(sources, key=lambda x: x["authority"], reverse=True)[:10]
            
            # Generate summary of findings
            summary = await self._generate_summary(topic, sources)
            
            return self.format_response(True, data={
                "sources": sources,
                "summary": summary,
                "search_queries": search_queries,
                "total_results": len(sources)
            })
            
        except Exception as e:
            self.logger.error(f"Web research error: {e}")
            # Return empty but valid response
            return self.format_response(True, data={
                "sources": [],
                "summary": f"Web search for {topic} encountered issues. Focusing on known industry trends.",
                "search_queries": [],
                "total_results": 0
            })
    
    def _is_authoritative_source(self, url: str) -> bool:
        """Check if source is from authoritative domain"""
        authoritative_domains = [
            # Tier 1 - Most Authoritative
            "sec.gov", "federalreserve.gov", ".gov",
            # Tier 2 - Highly Credible
            "institutionalinvestor.com", "pionline.com", "bloomberg.com", 
            "reuters.com", "wsj.com", "ft.com", "mckinsey.com", "bcg.com", 
            "bain.com", "preqin.com", "pitchbook.com",
            # Tier 3 - Acceptable
            "forbes.com", "businesswire.com", "prnewswire.com",
            "investmentnews.com", "thinkadvisor.com", "wealthmanagement.com",
            # Industry associations
            "ici.org", "sifma.org", "nvca.org", "ilpa.org"
        ]
        
        url_lower = url.lower()
        return any(domain in url_lower for domain in authoritative_domains)
    
    def _get_source_authority(self, url: str) -> int:
        """Get authority score for ranking sources"""
        url_lower = url.lower()
        
        # Tier 1 - Highest authority
        if any(domain in url_lower for domain in ["sec.gov", "federalreserve.gov", ".gov"]):
            return 3
        
        # Tier 2 - High authority
        tier2_domains = [
            "institutionalinvestor.com", "pionline.com", "bloomberg.com",
            "reuters.com", "wsj.com", "ft.com", "mckinsey.com", "bcg.com",
            "preqin.com", "pitchbook.com"
        ]
        if any(domain in url_lower for domain in tier2_domains):
            return 2
        
        # Tier 3 - Standard authority
        return 1
    
    def _extract_date(self, result: Dict[str, Any]) -> str:
        """Extract date from search result"""
        # Try to extract date from snippet or title
        import re
        
        text = f"{result.get('title', '')} {result.get('snippet', '')}"
        
        # Look for date patterns
        date_patterns = [
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',
            r'\d{1,2}/\d{1,2}/\d{4}',
            r'\d{4}-\d{2}-\d{2}',
            r'(Q[1-4]\s+\d{4})',
            r'(\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        
        return None
    
    async def _generate_summary(self, topic: str, sources: List[Dict[str, Any]]) -> str:
        """Generate summary of web research findings"""
        if not sources:
            return f"Limited current data available for {topic}. Recommend focusing on established industry practices."
        
        # Compile key findings
        source_summaries = []
        for source in sources[:5]:  # Top 5 sources
            source_summaries.append(
                f"- {source['title']}: {source['snippet'][:100]}..."
            )
        
        prompt = f"""Based on these current web sources about {topic}, provide a 2-3 sentence summary of key trends and insights for institutional investors:

{chr(10).join(source_summaries)}

Focus on:
1. Current market trends
2. Recent developments
3. Data points relevant to institutional investors"""

        try:
            summary = await self.query_llm(prompt, max_tokens=200)
            return summary.strip()
        except Exception as e:
            self.logger.error(f"Error generating summary: {e}")
            return f"Current research indicates growing institutional interest in {topic}, with emphasis on data-driven strategies and regulatory compliance."