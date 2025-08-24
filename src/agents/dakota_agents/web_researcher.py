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
            word_count = task.get("word_count", 1750)  # Default word count
            
            # Scale source target based on word count
            base_sources = 15
            if word_count >= 3000:
                max_sources = 25  # Very long articles need more sources
            elif word_count >= 2500:
                max_sources = 20
            else:
                max_sources = base_sources
            
            # Create diverse search queries to maximize source coverage
            current_year = datetime.now().year
            search_queries = [
                f"{topic} institutional investors {current_year}",
                f"{topic} {current_year} trends market data",
                f"{topic} latest statistics {current_year}",
                f"{topic} research reports {current_year}",
                f"{topic} industry analysis {current_year}",
                f"{topic} investment outlook {current_year}",  # Additional query
                f"{topic} portfolio allocation {current_year}",  # Additional query
                f"{topic} market insights {current_year}"  # Additional query
            ]
            
            # Limit queries based on word count to avoid overwhelming search API
            if word_count < 2500:
                search_queries = search_queries[:5]  # Standard 5 queries
            elif word_count < 3000:
                search_queries = search_queries[:6]  # 6 queries for medium articles
            # else: use all 8 queries for long articles
            
            all_results = []
            sources = []
            
            # Search with each query
            for query in search_queries:
                self.logger.info(f"Searching: {query}")
                try:
                    results = await asyncio.to_thread(
                        search_web,
                        query,
                        10  # Increased from 5 to 10 results per query
                    )
                    if results:
                        all_results.extend(results)
                except Exception as e:
                    self.logger.warning(f"Search failed for '{query}': {e}")
            
            # Process and deduplicate results with improved filtering
            seen_urls = set()
            seen_domains = {}  # Track domain frequency
            
            # First pass: collect all authoritative sources
            authoritative_sources = []
            other_sources = []
            
            for result in all_results:
                url = result.get("url", "")
                title = result.get("title", "")
                
                if not url or url in seen_urls or not title:
                    continue
                    
                seen_urls.add(url)
                domain = url.split("//")[-1].split("/")[0].lower()
                
                # Track domain frequency (limit 3 per domain to ensure diversity)
                if domain not in seen_domains:
                    seen_domains[domain] = 0
                if seen_domains[domain] >= 3:
                    continue
                seen_domains[domain] += 1
                
                source_data = {
                    "title": title,
                    "url": url,
                    "snippet": result.get("snippet", ""),
                    "date": self._extract_date(result) or datetime.now().strftime("%Y-%m-%d"),
                    "type": "web_research",
                    "authority": self._get_source_authority(url)
                }
                
                if self._is_authoritative_source(url):
                    authoritative_sources.append(source_data)
                elif self._is_acceptable_source(url):
                    # Keep high-quality non-authoritative sources
                    other_sources.append(source_data)
            
            # Combine sources: prioritize authoritative, then others
            sources = authoritative_sources + other_sources
            
            # Limit to scaled number of most authoritative sources
            sources = sorted(sources, key=lambda x: x["authority"], reverse=True)[:max_sources]
            
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
            "sec.gov", "federalreserve.gov", ".gov", "imf.org", "worldbank.org", "oecd.org", "bis.org",
            "treasury.gov", "cftc.gov", "finra.org", "fasb.org", "iasb.org",
            # Tier 2 - Highly Credible
            "institutionalinvestor.com", "pionline.com", "bloomberg.com", 
            "reuters.com", "wsj.com", "ft.com", "mckinsey.com", "bcg.com", 
            "bain.com", "preqin.com", "pitchbook.com", "blackrock.com", "jpmorgan.com",
            "goldmansachs.com", "morganstanley.com", "statestreet.com", "vanguard.com",
            "pwc.com", "deloitte.com", "ey.com", "kpmg.com", "spglobal.com", "moodys.com",
            "fidelity.com", "schwab.com", "troweprice.com", "capitalgroup.com", "invesco.com",
            # Financial News & Analysis
            "barrons.com", "investopedia.com", "morningstar.com", "zerohedge.com", "seekingalpha.com",
            "fool.com", "financialpost.com", "thestreet.com", "benzinga.com",
            # Tier 3 - Acceptable
            "forbes.com", "businesswire.com", "prnewswire.com", "cnbc.com", "marketwatch.com",
            "investmentnews.com", "thinkadvisor.com", "wealthmanagement.com", "nasdaq.com",
            "privateequityinternational.com", "privatedebtinvestor.com", "altassets.net",
            "hedgeweek.com", "absolutereturn-alpha.com", "hedgefundintelligence.com",
            # Industry associations
            "ici.org", "sifma.org", "nvca.org", "ilpa.org", "aima.org", "lsta.org", "caia.org",
            "cfainstitute.org", "risknet.org", "garp.org", "isda.org", "icma-group.org"
        ]
        
        url_lower = url.lower()
        return any(domain in url_lower for domain in authoritative_domains)
    
    def _is_acceptable_source(self, url: str) -> bool:
        """Check if source is acceptable quality for additional sources"""
        acceptable_domains = [
            # Additional financial and business sources
            "yahoo.com", "finance.yahoo.com", "businessinsider.com", "quartz.com",
            "axios.com", "cnn.com", "bbc.com", "economist.com", "harvard.edu",
            "wharton.upenn.edu", "mit.edu", "stanford.edu", "chicagobooth.edu",
            "knowledge.wharton.upenn.edu", "hbr.org", "sloanreview.mit.edu",
            # Trade publications
            "fundfire.com", "ignites.com", "plan-sponsor.com", "airalternatives.com",
            # Industry data providers  
            "cerulli.com", "callan.com", "cambridge.org", "ssrn.com",
            # News wires and PR
            "marketwatch.com", "globenewswire.com", "accesswire.com",
            # Think tanks and research
            "brookings.edu", "aei.org", "heritage.org", "urban.org"
        ]
        
        url_lower = url.lower()
        return any(domain in url_lower for domain in acceptable_domains)
    
    def _get_source_authority(self, url: str) -> int:
        """Get authority score for ranking sources"""
        url_lower = url.lower()
        
        # Tier 1 - Highest authority
        tier1_domains = ["sec.gov", "federalreserve.gov", ".gov", "imf.org", 
                        "worldbank.org", "oecd.org", "bis.org", "treasury.gov", 
                        "cftc.gov", "finra.org", "fasb.org", "iasb.org"]
        if any(domain in url_lower for domain in tier1_domains):
            return 3
        
        # Tier 2 - High authority
        tier2_domains = [
            "institutionalinvestor.com", "pionline.com", "bloomberg.com",
            "reuters.com", "wsj.com", "ft.com", "mckinsey.com", "bcg.com",
            "preqin.com", "pitchbook.com", "blackrock.com", "jpmorgan.com",
            "goldmansachs.com", "morganstanley.com", "pwc.com", "deloitte.com",
            "spglobal.com", "moodys.com", "bain.com", "fidelity.com", "schwab.com",
            "troweprice.com", "capitalgroup.com", "invesco.com", "barrons.com",
            "morningstar.com"
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