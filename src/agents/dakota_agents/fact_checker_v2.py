"""Dakota Fact Checker V2 - With true source content verification"""

import asyncio
import re
import json
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import httpx
from difflib import SequenceMatcher
from urllib.parse import urlparse

from .base_agent import DakotaBaseAgent
from src.services.web_search import search_web
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DakotaFactCheckerV2(DakotaBaseAgent):
    """Enhanced fact checker that actually verifies claims against source content"""
    
    def __init__(self):
        super().__init__("fact_checker_v2", model_override="gpt-5-mini")
        self.verification_results = []
        self.critical_issues = []
        self.sources_verified = 0
        self.urls_tested = 0
        self.source_cache = {}  # Cache fetched sources
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fact checking with true source verification"""
        try:
            self.update_status("active", "Starting enhanced fact checking with source verification")
            
            article_file = task.get("article_file")
            metadata_file = task.get("metadata_file")
            
            # Read files
            with open(article_file, 'r') as f:
                article_content = f.read()
            
            with open(metadata_file, 'r') as f:
                metadata_content = f.read()
            
            # Step 1: Extract sources from metadata
            self.logger.info("Extracting sources from metadata...")
            sources = await self._extract_sources_with_urls(metadata_content)
            
            if len(sources) < 10:
                return self.format_response(True, data={
                    "approved": False,
                    "status": "❌ REJECTED",
                    "issues": f"Only {len(sources)} sources found (need 10+)",
                    "sources_verified": 0
                })
            
            # Step 2: Extract all claims from article
            self.logger.info("Extracting all factual claims...")
            claims = await self._extract_claims_with_context(article_content)
            
            # Step 3: Fetch and cache source content
            self.logger.info(f"Fetching content from {len(sources)} sources...")
            await self._fetch_source_content(sources)
            
            # Step 4: Verify each claim against actual source content
            self.logger.info(f"Verifying {len(claims)} claims against source content...")
            verification_results = []
            
            for claim in claims:
                result = await self._verify_claim_in_sources(claim, sources)
                verification_results.append(result)
                
                if not result["verified"]:
                    self.critical_issues.append({
                        "claim": claim["claim"],
                        "context": claim["context"],
                        "issue": result["issue"],
                        "severity": "HIGH" if claim["type"] in ["financial", "percentage"] else "MEDIUM"
                    })
            
            # Step 5: Test all URLs
            self.logger.info("Testing all source URLs...")
            url_results = await self._test_all_urls(sources)
            
            # Step 6: Verify related article URLs
            self.logger.info("Verifying Learning Center article URLs...")
            related_valid = await self._verify_related_articles(metadata_content)
            
            # Calculate verification statistics
            verified_count = sum(1 for r in verification_results if r["verified"])
            verification_rate = (verified_count / len(claims)) * 100 if claims else 0
            
            # Determine approval
            approved = (
                verification_rate >= 90 and  # 90% of claims verified
                url_results["working"] == url_results["total"] and
                related_valid and
                len(sources) >= 10
            )
            
            if approved:
                status_msg = f"✅ APPROVED: Verified {verified_count}/{len(claims)} claims ({verification_rate:.0f}%), tested {self.urls_tested} source URLs (all working), confirmed all claims appear in cited sources."
            else:
                issues = []
                if verification_rate < 90:
                    issues.append(f"Only {verification_rate:.0f}% of claims verified in sources")
                if url_results["broken"] > 0:
                    issues.append(f"{url_results['broken']} broken source URLs")
                if not related_valid:
                    issues.append("Invalid Learning Center article URLs")
                    
                status_msg = f"❌ REJECTED: {', '.join(issues)}. Cannot approve publication."
            
            return self.format_response(True, data={
                "approved": approved,
                "status": status_msg,
                "issues": self.critical_issues if not approved else [],
                "sources_verified": len(sources),
                "urls_tested": self.urls_tested,
                "verification_details": {
                    "claims_total": len(claims),
                    "claims_verified": verified_count,
                    "verification_rate": verification_rate,
                    "sources_fetched": len(self.source_cache),
                    "urls_working": url_results["working"],
                    "urls_broken": url_results["broken"],
                    "related_articles_valid": related_valid
                }
            })
            
        except Exception as e:
            self.logger.error(f"Fact checking error: {e}")
            return self.format_response(False, error=str(e))
    
    async def _extract_sources_with_urls(self, metadata_content: str) -> List[Dict[str, Any]]:
        """Extract sources with their URLs from metadata"""
        sources = []
        
        # Find sources section
        sources_match = re.search(
            r'##\s*Sources\s*(?:and|&)?\s*Citations.*?(?=##|\Z)', 
            metadata_content, 
            re.IGNORECASE | re.DOTALL
        )
        
        if not sources_match:
            return sources
        
        sources_text = sources_match.group(0)
        
        # Extract each source with its URL
        source_blocks = re.findall(
            r'(\d+)\.\s*\*\*([^*]+)\*\*[^-]*-[^(]*\(([^)]+)\).*?URL:\s*([^\n]+).*?Key Data:\s*([^\n]+)',
            sources_text,
            re.DOTALL
        )
        
        for block in source_blocks:
            sources.append({
                "number": block[0],
                "title": block[1].strip(),
                "date": block[2].strip(),
                "url": block[3].strip(),
                "key_data": block[4].strip(),
                "content": None  # Will be populated when fetched
            })
        
        return sources
    
    async def _extract_claims_with_context(self, article_content: str) -> List[Dict[str, Any]]:
        """Extract claims with better context"""
        claims = []
        
        # Skip frontmatter
        content_start = 0
        if article_content.startswith("---"):
            end_frontmatter = article_content.find("---", 3)
            if end_frontmatter > 0:
                content_start = end_frontmatter + 3
        
        article_body = article_content[content_start:]
        
        # Split into sentences for better context
        sentences = re.split(r'(?<=[.!?])\s+', article_body)
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check for various claim types
            claim_found = False
            
            # Financial claims
            financial_match = re.search(r'\$[\d,]+(?:\.\d+)?\s*(?:billion|million|trillion)?', sentence)
            if financial_match:
                claims.append({
                    "claim": financial_match.group(0),
                    "type": "financial",
                    "context": sentence,
                    "sentence_index": i
                })
                claim_found = True
            
            # Percentage claims
            percentage_match = re.search(r'\d+(?:\.\d+)?%', sentence)
            if percentage_match and not claim_found:
                claims.append({
                    "claim": percentage_match.group(0),
                    "type": "percentage",
                    "context": sentence,
                    "sentence_index": i
                })
                claim_found = True
            
            # Statistical claims
            stat_match = re.search(r'(?:approximately|about|nearly|over|under|more than|less than)?\s*\d+(?:,\d+)*(?:\.\d+)?\s*(?:firms?|companies|funds?|investors?|managers?)', sentence, re.IGNORECASE)
            if stat_match and not claim_found:
                claims.append({
                    "claim": stat_match.group(0),
                    "type": "statistic",
                    "context": sentence,
                    "sentence_index": i
                })
                claim_found = True
            
            # Growth/decline claims
            growth_match = re.search(r'(?:increased?|decreased?|grew|declined?|rose|fell)\s*(?:by)?\s*\d+(?:\.\d+)?%?', sentence, re.IGNORECASE)
            if growth_match and not claim_found:
                claims.append({
                    "claim": growth_match.group(0),
                    "type": "growth",
                    "context": sentence,
                    "sentence_index": i
                })
        
        return claims
    
    async def _fetch_source_content(self, sources: List[Dict[str, Any]]) -> None:
        """Fetch actual content from source URLs"""
        async with httpx.AsyncClient(timeout=30) as client:
            for source in sources:
                url = source["url"]
                
                # Skip if already cached
                if url in self.source_cache:
                    source["content"] = self.source_cache[url]
                    continue
                
                try:
                    self.logger.info(f"Fetching content from: {url}")
                    response = await client.get(url, follow_redirects=True)
                    
                    if response.status_code < 400:
                        # Extract text content (basic HTML stripping)
                        content = response.text
                        
                        # Remove HTML tags (basic)
                        content = re.sub(r'<[^>]+>', ' ', content)
                        content = re.sub(r'\s+', ' ', content)
                        
                        # Cache and store
                        self.source_cache[url] = content[:50000]  # Limit size
                        source["content"] = content[:50000]
                    else:
                        self.logger.warning(f"Failed to fetch {url}: {response.status_code}")
                        source["content"] = ""
                        
                except Exception as e:
                    self.logger.error(f"Error fetching {url}: {e}")
                    source["content"] = ""
                    
                # Small delay to be respectful
                await asyncio.sleep(0.5)
    
    async def _verify_claim_in_sources(self, claim: Dict[str, Any], sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify if a claim appears in any of the sources"""
        claim_text = claim["claim"]
        claim_context = claim["context"]
        
        # Try to find the claim in sources
        for source in sources:
            if not source.get("content"):
                continue
            
            content = source["content"].lower()
            claim_lower = claim_text.lower()
            
            # Direct match
            if claim_lower in content:
                return {
                    "verified": True,
                    "source": source["title"],
                    "match_type": "direct"
                }
            
            # Fuzzy match for numbers
            if claim["type"] in ["financial", "percentage", "statistic"]:
                # Extract numbers from claim
                numbers = re.findall(r'\d+(?:\.\d+)?', claim_text)
                
                for number in numbers:
                    if number in content:
                        # Check if context words appear near the number
                        context_words = re.findall(r'\b[a-zA-Z]{4,}\b', claim_context)
                        nearby_match = False
                        
                        for word in context_words[:5]:  # Check first 5 significant words
                            if word.lower() in content:
                                nearby_match = True
                                break
                        
                        if nearby_match:
                            return {
                                "verified": True,
                                "source": source["title"],
                                "match_type": "fuzzy"
                            }
            
            # Semantic similarity check using LLM
            if claim["type"] in ["financial", "percentage"]:
                verification = await self._llm_verify_claim(claim_text, claim_context, source)
                if verification["verified"]:
                    return verification
        
        # Not found in any source
        return {
            "verified": False,
            "issue": f"Claim '{claim_text}' not found in any cited source"
        }
    
    async def _llm_verify_claim(self, claim: str, context: str, source: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to verify if claim is supported by source content"""
        if not source.get("content"):
            return {"verified": False}
        
        # Extract relevant portion of source
        source_excerpt = source["content"][:3000]
        
        prompt = f"""Verify if this claim is supported by the source content:

CLAIM: {claim}
CONTEXT: {context}

SOURCE EXCERPT from {source['title']}:
{source_excerpt}

Is the claim directly supported by the source? Consider:
1. Does the source mention this specific statistic?
2. Does the source discuss the same topic/entity?
3. Are the numbers consistent?

Respond with only YES or NO."""

        try:
            response = await self.query_llm(prompt, max_tokens=10)
            
            if "YES" in response.upper():
                return {
                    "verified": True,
                    "source": source["title"],
                    "match_type": "semantic"
                }
        except:
            pass
        
        return {"verified": False}
    
    async def _test_all_urls(self, sources: List[Dict[str, Any]]) -> Dict[str, int]:
        """Test all source URLs"""
        results = {"total": len(sources), "working": 0, "broken": 0}
        self.urls_tested = len(sources)
        
        async with httpx.AsyncClient() as client:
            for source in sources:
                url = source["url"]
                
                try:
                    # We already fetched content, so check if we got it
                    if source.get("content"):
                        results["working"] += 1
                    else:
                        response = await client.head(url, timeout=10, follow_redirects=True)
                        if response.status_code < 400:
                            results["working"] += 1
                        else:
                            results["broken"] += 1
                            self.logger.warning(f"Broken URL: {url}")
                except:
                    results["broken"] += 1
                    self.logger.error(f"Failed to test URL: {url}")
        
        return results
    
    async def _verify_related_articles(self, metadata_content: str) -> bool:
        """Verify Learning Center article URLs"""
        try:
            # Find related articles section
            related_match = re.search(
                r'##\s*Related\s+Learning\s+Center\s+Articles.*?(?=##|\Z)',
                metadata_content,
                re.IGNORECASE | re.DOTALL
            )
            
            if not related_match:
                return True  # Not required
            
            # Extract Dakota blog URLs
            dakota_urls = re.findall(
                r'https://www\.dakota\.com/resources/blog/[^\s\)]+',
                related_match.group(0)
            )
            
            if len(dakota_urls) < 3:
                return False
            
            # Test each URL
            all_valid = True
            async with httpx.AsyncClient() as client:
                for url in dakota_urls:
                    try:
                        response = await client.head(url, timeout=10, follow_redirects=True)
                        if response.status_code >= 400:
                            self.logger.error(f"Invalid Dakota URL: {url}")
                            all_valid = False
                    except:
                        self.logger.error(f"Failed to verify Dakota URL: {url}")
                        all_valid = False
            
            return all_valid
            
        except Exception as e:
            self.logger.error(f"Error verifying related articles: {e}")
            return False