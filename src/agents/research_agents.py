"""
Specialized research agents for information gathering
"""
from typing import Dict, Any, List, Tuple, Optional
import json
import re
from datetime import datetime

from src.agents.multi_agent_base import BaseAgent, AgentMessage, AgentStatus
from src.config import DEFAULT_MODELS, MIN_SOURCES
from src.services.web_search import search_web
from src.services.kb_search import KnowledgeBaseSearcher
from src.utils.logging import get_logger

logger = get_logger(__name__)


class WebResearchAgent(BaseAgent):
    """Agent specialized in web research and current data gathering"""
    
    def __init__(self):
        super().__init__(
            agent_id="web_researcher_001",
            agent_type="web_researcher",
            team="research"
        )
        self.capabilities = [
            "web_search",
            "news_analysis",
            "market_data",
            "trend_identification",
            "source_verification"
        ]
        self.model = DEFAULT_MODELS.get("web_researcher", "gpt-5")
    
    def validate_task(self, task: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate if task is web research related"""
        valid_tasks = [
            "search_web", "find_sources", "verify_claim",
            "get_market_data", "find_news", "research_topic"
        ]
        
        if task not in valid_tasks:
            return False, f"Task '{task}' not supported by WebResearchAgent"
        
        if task in ["search_web", "research_topic"] and "query" not in payload:
            return False, "Missing 'query' in payload"
        
        return True, "Valid task"
    
    def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process research request"""
        task = message.task
        payload = message.payload
        
        if task == "research_topic":
            result = self._comprehensive_research(payload["query"])
        elif task == "find_sources":
            result = self._find_authoritative_sources(payload["query"])
        elif task == "verify_claim":
            result = self._verify_claim(payload["claim"])
        elif task == "get_market_data":
            result = self._get_market_data(payload["query"])
        else:
            result = self._basic_search(payload["query"])
        
        return self._create_response(message, result)
    
    def _comprehensive_research(self, query: str) -> Dict[str, Any]:
        """Perform comprehensive research on a topic"""
        try:
            # Search for current information
            search_results = search_web(query)
            
            # Check if search failed
            if not search_results:
                return {
                    "success": False,
                    "error": "Web search returned no results",
                    "search_query": query,
                    "timestamp": datetime.now().isoformat()
                }
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return {
                "success": False,
                "error": f"Web search failed: {str(e)}",
                "search_query": query,
                "timestamp": datetime.now().isoformat()
            }
        
        # Analyze and synthesize results
        analysis_prompt = f"""Analyze these search results for: {query}

Results:
{json.dumps(search_results, indent=2)}

Provide:
1. Key findings with dates and sources
2. Relevant statistics and data points
3. Market trends and insights
4. Authoritative sources with URLs
5. Areas needing further research

Focus on 2024-2025 data and institutional investor perspectives."""

        analysis = self.query_llm(
            analysis_prompt,
            reasoning_effort="high",
            verbosity="high"
        )
        
        # Extract sources from analysis and combine with search results
        sources = self._extract_sources(analysis)
        
        # Add search results as sources if we don't have enough
        for result in search_results[:5]:  # Top 5 search results
            if isinstance(result, dict) and result.get("url"):
                sources.append({
                    "url": result.get("url", ""),
                    "title": result.get("title", ""),
                    "date": datetime.now().strftime("%Y-%m-%d")
                })
        
        return {
            "success": True,
            "research_summary": analysis,
            "sources": sources,
            "search_query": query,
            "timestamp": datetime.now().isoformat()
        }
    
    def _find_authoritative_sources(self, query: str) -> Dict[str, Any]:
        """Find authoritative sources for a topic"""
        # Search for specific types of sources
        source_queries = [
            f"{query} site:*.edu research paper",
            f"{query} site:*.gov statistics data",
            f"{query} institutional investor report",
            f"{query} McKinsey Bain BCG analysis"
        ]
        
        all_sources = []
        for sq in source_queries:
            results = search_web(sq)
            all_sources.extend(results.get("sources", []))
        
        # Rank and filter sources
        ranked_sources = self._rank_sources(all_sources)
        
        return {
            "success": True,
            "sources": ranked_sources[:MIN_SOURCES * 2],  # Return more than minimum
            "total_found": len(all_sources),
            "query": query
        }
    
    def _verify_claim(self, claim: str) -> Dict[str, Any]:
        """Verify a specific claim or statistic"""
        verification_prompt = f"""Verify this claim: {claim}

Search for:
1. Original source of the claim
2. Supporting evidence
3. Contradicting evidence
4. Expert opinions
5. Fact-checking results

Provide verification status: VERIFIED, PARTIALLY_VERIFIED, or UNVERIFIED"""

        # Search for verification
        search_results = search_web(f"verify {claim} fact check")
        
        verification = self.query_llm(
            f"{verification_prompt}\n\nSearch results:\n{json.dumps(search_results)}",
            reasoning_effort="high",
            verbosity="medium"
        )
        
        return {
            "success": True,
            "claim": claim,
            "verification_result": verification,
            "sources": search_results.get("sources", [])
        }
    
    def _get_market_data(self, query: str) -> Dict[str, Any]:
        """Get specific market data and statistics"""
        # Search for market data
        market_search = search_web(f"{query} market data statistics 2024 2025")
        
        # Extract numerical data
        data_prompt = f"""Extract market data from these results for: {query}

Results: {json.dumps(market_search)}

Extract:
1. Specific numbers and percentages
2. Growth rates and trends
3. Market sizes and valuations
4. Comparisons and benchmarks
5. Time periods for each data point

Format as structured data."""

        market_data = self.query_llm(
            data_prompt,
            reasoning_effort="medium",
            verbosity="medium"
        )
        
        return {
            "success": True,
            "market_data": market_data,
            "sources": market_search.get("sources", []),
            "query": query
        }
    
    def _basic_search(self, query: str) -> Dict[str, Any]:
        """Perform basic web search"""
        results = search_web(query)
        return {
            "success": True,
            "results": results,
            "query": query
        }
    
    def _extract_sources(self, text: str) -> List[Dict[str, str]]:
        """Extract sources from text"""
        sources = []
        
        # Pattern for URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:!?]'
        urls = re.findall(url_pattern, text)
        
        # Pattern for citations like [Source, Date]
        citation_pattern = r'\[([^\]]+)\]'
        citations = re.findall(citation_pattern, text)
        
        for i, url in enumerate(urls):
            source = {
                "url": url,
                "title": citations[i] if i < len(citations) else f"Source {i+1}",
                "date": datetime.now().strftime("%Y-%m-%d")
            }
            sources.append(source)
        
        return sources
    
    def _rank_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank sources by credibility"""
        # Simple ranking based on domain authority
        domain_scores = {
            ".edu": 10,
            ".gov": 10,
            ".org": 8,
            "mckinsey.com": 9,
            "bain.com": 9,
            "bcg.com": 9,
            "harvard.edu": 10,
            "wharton.upenn.edu": 10,
            "mit.edu": 10,
            "stanford.edu": 10,
            "dakota.com": 10
        }
        
        for source in sources:
            url = source.get("url", "")
            score = 5  # Default score
            
            for domain, domain_score in domain_scores.items():
                if domain in url.lower():
                    score = domain_score
                    break
            
            source["credibility_score"] = score
        
        # Sort by credibility score
        return sorted(sources, key=lambda x: x.get("credibility_score", 0), reverse=True)


class KnowledgeBaseAgent(BaseAgent):
    """Agent specialized in Dakota knowledge base searches"""
    
    def __init__(self):
        super().__init__(
            agent_id="kb_researcher_001",
            agent_type="kb_researcher",
            team="research"
        )
        self.capabilities = [
            "dakota_kb_search",
            "article_retrieval",
            "investment_insights",
            "dakota_philosophy",
            "historical_data"
        ]
        self.model = DEFAULT_MODELS.get("kb_researcher", "gpt-5-mini")
        # Try to use optimized searcher, fallback to original if not available
        try:
            from src.services.kb_search_optimized import get_kb_searcher
            self.kb_searcher = get_kb_searcher()
            self.use_optimized = True
        except ImportError:
            from src.services.kb_search import KnowledgeBaseSearcher
            self.kb_searcher = KnowledgeBaseSearcher()
            self.use_optimized = False
    
    def validate_task(self, task: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate if task is KB related"""
        valid_tasks = [
            "search_kb", "find_dakota_insights", "get_investment_philosophy",
            "find_similar_articles", "get_historical_context"
        ]
        
        if task not in valid_tasks:
            return False, f"Task '{task}' not supported by KnowledgeBaseAgent"
        
        if "query" not in payload:
            return False, "Missing 'query' in payload"
        
        return True, "Valid task"
    
    def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process KB search request"""
        task = message.task
        payload = message.payload
        
        if task == "search_kb":
            result = self._search_knowledge_base(payload["query"])
        elif task == "find_dakota_insights":
            result = self._find_dakota_specific_insights(payload["query"])
        elif task == "get_investment_philosophy":
            result = self._get_investment_philosophy(payload["query"])
        elif task == "find_similar_articles":
            result = self._find_similar_articles(payload["query"])
        else:
            result = self._get_historical_context(payload["query"])
        
        return self._create_response(message, result)
    
    def _search_knowledge_base(self, query: str) -> Dict[str, Any]:
        """Search Dakota knowledge base"""
        try:
            # Perform KB search with timeout
            if self.use_optimized:
                results = self.kb_searcher.search(query, max_results=5, timeout=10)
            else:
                results = self.kb_searcher.search(query)
            
            # Check for errors in results
            if isinstance(results, dict) and not results.get("success", True):
                return {"success": False, "error": results.get("error", "KB search failed"), "query": query}
            
            # Analyze results
            analysis_prompt = f"""Analyze these Dakota knowledge base results for: {query}

Results:
{json.dumps(results, indent=2)}

Extract:
1. Key Dakota-specific insights
2. Investment philosophy points
3. Historical performance data
4. Relevant article references
5. Expert perspectives from Dakota team

Focus on institutional investor needs."""

            analysis = self.query_llm(
                analysis_prompt,
                reasoning_effort="medium",
                verbosity="high"
            )
            
            return {
                "success": True,
                "kb_insights": analysis,
                "raw_results": results,
                "query": query,
                "source": "dakota_knowledge_base"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    def _find_dakota_specific_insights(self, query: str) -> Dict[str, Any]:
        """Find Dakota-specific insights and perspectives"""
        # Search for Dakota-specific content
        dakota_query = f"{query} Dakota perspective institutional investors"
        results = self.kb_searcher.search(dakota_query)
        if isinstance(results, dict) and not results.get("success", True):
            return {"success": False, "error": results.get("error", "KB search failed"), "query": query}
        
        # Extract Dakota insights
        insight_prompt = f"""Extract Dakota-specific insights for: {query}

From these results:
{json.dumps(results, indent=2)}

Focus on:
1. Dakota's unique perspective
2. Differentiating factors
3. Value propositions for institutions
4. Case studies and examples
5. Dakota team expertise

Provide actionable insights."""

        insights = self.query_llm(
            insight_prompt,
            reasoning_effort="medium",
            verbosity="medium"
        )
        
        return {
            "success": True,
            "dakota_insights": insights,
            "supporting_articles": self._extract_article_refs(results),
            "query": query
        }
    
    def _get_investment_philosophy(self, query: str) -> Dict[str, Any]:
        """Get Dakota's investment philosophy related to query"""
        philosophy_search = self.kb_searcher.search(
            f"Dakota investment philosophy {query}"
        )
        
        philosophy_prompt = f"""Explain Dakota's investment philosophy regarding: {query}

Based on:
{json.dumps(philosophy_search, indent=2)}

Cover:
1. Core principles
2. Risk management approach
3. Due diligence process
4. Portfolio construction
5. Long-term perspective

Relate specifically to the query topic."""

        philosophy = self.query_llm(
            philosophy_prompt,
            reasoning_effort="high",
            verbosity="high"
        )
        
        return {
            "success": True,
            "investment_philosophy": philosophy,
            "query": query,
            "references": self._extract_article_refs(philosophy_search)
        }
    
    def _find_similar_articles(self, query: str) -> Dict[str, Any]:
        """Find similar articles in knowledge base"""
        similar_search = self.kb_searcher.search(query, limit=10)
        
        # Rank by relevance
        ranked_articles = self._rank_articles_by_relevance(similar_search, query)
        
        return {
            "success": True,
            "similar_articles": ranked_articles[:5],
            "total_found": len(similar_search),
            "query": query
        }
    
    def _get_historical_context(self, query: str) -> Dict[str, Any]:
        """Get historical context from knowledge base"""
        historical_search = self.kb_searcher.search(
            f"{query} historical performance trends evolution"
        )
        
        context_prompt = f"""Provide historical context for: {query}

From Dakota knowledge base:
{json.dumps(historical_search, indent=2)}

Include:
1. Historical trends and evolution
2. Past performance and outcomes
3. Lessons learned
4. Market cycles
5. Long-term perspectives

Focus on institutional investor relevance."""

        context = self.query_llm(
            context_prompt,
            reasoning_effort="medium",
            verbosity="high"
        )
        
        return {
            "success": True,
            "historical_context": context,
            "sources": self._extract_article_refs(historical_search),
            "query": query
        }
    
    def _extract_article_refs(self, results: Any) -> List[Dict[str, str]]:
        """Extract article references from KB results"""
        articles = []
        
        # Extract from results structure
        if isinstance(results, dict):
            if "articles" in results:
                articles = results["articles"]
            elif "results" in results:
                articles = results["results"]
        elif isinstance(results, list):
            articles = results
        
        # Format references
        refs = []
        for article in articles[:5]:  # Top 5 articles
            ref = {
                "title": article.get("title", "Untitled"),
                "url": article.get("url", ""),
                "date": article.get("date", ""),
                "relevance": article.get("relevance_score", 0)
            }
            refs.append(ref)
        
        return refs
    
    def _rank_articles_by_relevance(self, articles: List[Dict], query: str) -> List[Dict]:
        """Rank articles by relevance to query"""
        query_terms = query.lower().split()
        
        for article in articles:
            score = 0
            title = article.get("title", "").lower()
            content = article.get("content", "").lower()
            
            # Score based on term matches
            for term in query_terms:
                score += title.count(term) * 3  # Title matches worth more
                score += content.count(term)
            
            article["relevance_score"] = score
        
        return sorted(articles, key=lambda x: x.get("relevance_score", 0), reverse=True)


class DataValidationAgent(BaseAgent):
    """Agent specialized in data validation and fact-checking"""
    
    def __init__(self):
        super().__init__(
            agent_id="data_validator_001",
            agent_type="data_validator",
            team="research"
        )
        self.capabilities = [
            "fact_checking",
            "source_validation",
            "data_consistency",
            "citation_verification",
            "freshness_check"
        ]
        self.model = DEFAULT_MODELS.get("fact_checker", "gpt-5")
    
    def validate_task(self, task: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate if task is data validation related"""
        valid_tasks = [
            "validate_facts", "check_sources", "verify_data",
            "check_consistency", "validate_citations", "check_freshness"
        ]
        
        if task not in valid_tasks:
            return False, f"Task '{task}' not supported by DataValidationAgent"
        
        if task == "validate_facts" and "content" not in payload:
            return False, "Missing 'content' in payload"
        
        return True, "Valid task"
    
    def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process validation request"""
        task = message.task
        payload = message.payload
        
        if task == "validate_facts":
            result = self._validate_all_facts(payload["content"])
        elif task == "check_sources":
            result = self._check_source_credibility(payload["sources"])
        elif task == "verify_data":
            result = self._verify_data_points(payload["data"])
        elif task == "check_consistency":
            result = self._check_consistency(payload["content"])
        elif task == "validate_citations":
            result = self._validate_citations(payload["content"])
        else:
            result = self._check_data_freshness(payload["content"])
        
        return self._create_response(message, result)
    
    def _validate_all_facts(self, content: str) -> Dict[str, Any]:
        """Validate all facts in content"""
        validation_prompt = f"""Fact-check this content:

{content[:3000]}...

For each claim or statistic:
1. Identify the specific claim
2. Assess verifiability
3. Check for supporting evidence
4. Note any concerns
5. Suggest corrections if needed

Return structured validation results."""

        validation = self.query_llm(
            validation_prompt,
            reasoning_effort="high",
            verbosity="high"
        )
        
        # Extract specific issues
        issues = self._extract_validation_issues(validation)
        
        return {
            "success": True,
            "validation_complete": True,
            "issues_found": len(issues),
            "issues": issues,
            "overall_credibility": self._calculate_credibility_score(issues),
            "detailed_report": validation
        }
    
    def _check_source_credibility(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check credibility of sources"""
        # Return early if no sources are provided
        if not sources:
            return {
                "success": False,
                "error": "No sources provided",
                "sources_checked": 0,
                "average_credibility": 0,
                "results": [],
                "highly_credible": [],
                "low_credibility": [],
            }

        credibility_results = []
        
        for source in sources:
            url = source.get("url", "")
            
            # Check domain credibility
            credibility = self._assess_domain_credibility(url)
            
            # Check content freshness
            freshness = self._assess_content_freshness(source)
            
            result = {
                "source": url,
                "credibility_score": credibility["score"],
                "credibility_notes": credibility["notes"],
                "freshness": freshness,
                "recommended": credibility["score"] >= 7
            }
            credibility_results.append(result)
        
        # Overall assessment
        avg_credibility = (
            sum(r["credibility_score"] for r in credibility_results) / len(credibility_results)
            if credibility_results
            else 0
        )
        
        return {
            "success": True,
            "sources_checked": len(sources),
            "average_credibility": avg_credibility,
            "results": credibility_results,
            "highly_credible": [r for r in credibility_results if r["credibility_score"] >= 8],
            "low_credibility": [r for r in credibility_results if r["credibility_score"] < 6]
        }
    
    def _verify_data_points(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify specific data points"""
        verification_results = []
        
        for data_point in data:
            claim = data_point.get("claim", "")
            value = data_point.get("value", "")
            source = data_point.get("source", "")
            
            # Verify the data point
            verification_prompt = f"""Verify this data point:
Claim: {claim}
Value: {value}
Source: {source}

Check if this is accurate and current."""

            verification = self.query_llm(
                verification_prompt,
                reasoning_effort="medium",
                verbosity="low"
            )
            
            result = {
                "data_point": claim,
                "value": value,
                "verification_status": self._parse_verification_status(verification),
                "notes": verification
            }
            verification_results.append(result)
        
        verified_count = sum(1 for r in verification_results if r["verification_status"] == "VERIFIED")
        
        return {
            "success": True,
            "data_points_checked": len(data),
            "verified": verified_count,
            "unverified": len(data) - verified_count,
            "results": verification_results
        }
    
    def _check_consistency(self, content: str) -> Dict[str, Any]:
        """Check internal consistency of content"""
        consistency_prompt = f"""Check this content for internal consistency:

{content[:3000]}...

Look for:
1. Contradicting statements
2. Inconsistent data points
3. Logical inconsistencies
4. Timeline conflicts
5. Statistical impossibilities

Report any inconsistencies found."""

        consistency_check = self.query_llm(
            consistency_prompt,
            reasoning_effort="high",
            verbosity="medium"
        )
        
        inconsistencies = self._extract_inconsistencies(consistency_check)
        
        return {
            "success": True,
            "consistent": len(inconsistencies) == 0,
            "inconsistencies_found": len(inconsistencies),
            "details": inconsistencies,
            "report": consistency_check
        }
    
    def _validate_citations(self, content: str) -> Dict[str, Any]:
        """Validate all citations in content"""
        import re
        
        # Extract citations
        citation_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        citations = re.findall(citation_pattern, content)
        
        validation_results = []
        for source_text, url in citations:
            # Validate URL format
            url_valid = self._is_valid_url(url)
            
            # Check if URL is accessible (simplified check)
            accessible = url_valid and not url.startswith('example.com')
            
            result = {
                "citation": f"[{source_text}]({url})",
                "url_valid": url_valid,
                "accessible": accessible,
                "source_text": source_text,
                "url": url
            }
            validation_results.append(result)
        
        valid_count = sum(1 for r in validation_results if r["url_valid"] and r["accessible"])
        
        return {
            "success": True,
            "total_citations": len(citations),
            "valid_citations": valid_count,
            "invalid_citations": len(citations) - valid_count,
            "results": validation_results,
            "meets_minimum": valid_count >= MIN_SOURCES
        }
    
    def _check_data_freshness(self, content: str) -> Dict[str, Any]:
        """Check if data is current"""
        import re
        
        # Extract dates and years
        year_pattern = r'\b(19|20)\d{2}\b'
        years = [int(y) for y in re.findall(year_pattern, content)]
        
        current_year = datetime.now().year
        
        # Analyze freshness
        if years:
            most_recent = max(years)
            oldest = min(years)
            avg_year = sum(years) / len(years)
            
            freshness_score = max(0, 100 - (current_year - most_recent) * 20)
        else:
            most_recent = oldest = avg_year = None
            freshness_score = 50  # Unknown freshness
        
        # Check for outdated references
        outdated_threshold = current_year - 2
        outdated_refs = [y for y in years if y < outdated_threshold]
        
        return {
            "success": True,
            "current_year": current_year,
            "most_recent_year": most_recent,
            "oldest_year": oldest,
            "average_year": round(avg_year) if avg_year else None,
            "freshness_score": freshness_score,
            "outdated_references": len(outdated_refs),
            "total_year_references": len(years),
            "is_current": freshness_score >= 80
        }
    
    def _extract_validation_issues(self, validation_text: str) -> List[Dict[str, str]]:
        """Extract validation issues from text"""
        # Simple extraction - in production would use more sophisticated parsing
        issues = []
        
        lines = validation_text.split('\n')
        current_issue = None
        
        for line in lines:
            if any(word in line.lower() for word in ['incorrect', 'false', 'outdated', 'unverified', 'concern']):
                if current_issue:
                    issues.append(current_issue)
                current_issue = {
                    "type": "validation_issue",
                    "description": line.strip(),
                    "severity": self._assess_severity(line)
                }
            elif current_issue and line.strip():
                current_issue["description"] += " " + line.strip()
        
        if current_issue:
            issues.append(current_issue)
        
        return issues
    
    def _calculate_credibility_score(self, issues: List[Dict]) -> float:
        """Calculate overall credibility score"""
        if not issues:
            return 100.0
        
        # Deduct points for issues based on severity
        score = 100.0
        severity_deductions = {
            "high": 20,
            "medium": 10,
            "low": 5
        }
        
        for issue in issues:
            severity = issue.get("severity", "medium")
            score -= severity_deductions.get(severity, 10)
        
        return max(0, score)
    
    def _assess_domain_credibility(self, url: str) -> Dict[str, Any]:
        """Assess credibility of a domain"""
        high_credibility_domains = [
            ".edu", ".gov", "mckinsey.com", "bain.com", "bcg.com",
            "harvard.edu", "wharton.upenn.edu", "stanford.edu",
            "mit.edu", "dakota.com", "wsj.com", "ft.com", "bloomberg.com"
        ]
        
        medium_credibility_domains = [
            ".org", "reuters.com", "forbes.com", "businessinsider.com",
            "cnbc.com", "economist.com"
        ]
        
        score = 5  # Default score
        notes = []
        
        url_lower = url.lower()
        
        for domain in high_credibility_domains:
            if domain in url_lower:
                score = 9
                notes.append(f"High credibility domain: {domain}")
                break
        
        if score == 5:
            for domain in medium_credibility_domains:
                if domain in url_lower:
                    score = 7
                    notes.append(f"Medium credibility domain: {domain}")
                    break
        
        if score == 5:
            notes.append("Unknown domain - requires further verification")
        
        return {
            "score": score,
            "notes": notes
        }
    
    def _assess_content_freshness(self, source: Dict[str, Any]) -> Dict[str, Any]:
        """Assess freshness of content"""
        date_str = source.get("date", "")
        current_year = datetime.now().year
        
        if date_str:
            try:
                # Try to extract year
                year_match = re.search(r'(20\d{2})', date_str)
                if year_match:
                    year = int(year_match.group(1))
                    age = current_year - year
                    
                    if age == 0:
                        return {"status": "current", "age": age, "score": 10}
                    elif age == 1:
                        return {"status": "recent", "age": age, "score": 8}
                    elif age <= 2:
                        return {"status": "acceptable", "age": age, "score": 6}
                    else:
                        return {"status": "outdated", "age": age, "score": 3}
            except:
                pass
        
        return {"status": "unknown", "age": None, "score": 5}
    
    def _parse_verification_status(self, verification_text: str) -> str:
        """Parse verification status from text"""
        text_lower = verification_text.lower()
        
        if any(word in text_lower for word in ['verified', 'correct', 'accurate', 'confirmed']):
            return "VERIFIED"
        elif any(word in text_lower for word in ['partially', 'mostly', 'generally']):
            return "PARTIALLY_VERIFIED"
        else:
            return "UNVERIFIED"
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL format is valid"""
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        return bool(re.match(url_pattern, url))
    
    def _extract_inconsistencies(self, consistency_text: str) -> List[Dict[str, str]]:
        """Extract inconsistencies from text"""
        inconsistencies = []
        
        # Simple extraction based on keywords
        lines = consistency_text.split('\n')
        
        for i, line in enumerate(lines):
            if any(word in line.lower() for word in ['contradict', 'inconsistent', 'conflict', 'mismatch']):
                inconsistency = {
                    "type": "inconsistency",
                    "description": line.strip(),
                    "location": f"Line {i+1}"
                }
                
                # Try to get context from next line
                if i + 1 < len(lines) and lines[i + 1].strip():
                    inconsistency["context"] = lines[i + 1].strip()
                
                inconsistencies.append(inconsistency)
        
        return inconsistencies
    
    def _assess_severity(self, text: str) -> str:
        """Assess severity of an issue"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['critical', 'false', 'incorrect', 'major']):
            return "high"
        elif any(word in text_lower for word in ['outdated', 'unclear', 'minor']):
            return "low"
        else:
            return "medium"