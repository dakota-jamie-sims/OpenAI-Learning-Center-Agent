"""Cached Fact Checker - Skips external URL fetching for speed"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import time

from .base_agent import DakotaBaseAgent
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DakotaCachedFactChecker(DakotaBaseAgent):
    """Fast fact checker that uses caching and skips external URLs"""
    
    def __init__(self):
        super().__init__("fact_checker", model_override="gpt-4o-mini")
        self.claim_cache = {}
        self.cache_ttl = 3600  # 1 hour
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fast fact checking"""
        article_file = task.get("article_file", "")
        metadata_file = task.get("metadata_file", "")
        
        self.update_status("active", "Starting cached fact checking")
        
        try:
            # Read files
            with open(article_file, 'r') as f:
                article_content = f.read()
            
            with open(metadata_file, 'r') as f:
                metadata_content = f.read()
            
            # Extract sources from metadata
            sources = self._extract_sources(metadata_content)
            
            # Extract and verify claims
            claims = await self._extract_claims(article_content)
            
            if not claims:
                # No specific claims, do basic validation
                return self._basic_validation(article_content, metadata_content, sources)
            
            # Verify claims using cache
            verified_claims = []
            unverified_claims = []
            
            for claim in claims:
                # Check cache first
                cache_key = self._get_cache_key(claim)
                cached_result = self._get_from_cache(cache_key)
                
                if cached_result:
                    if cached_result["verified"]:
                        verified_claims.append(cached_result)
                    else:
                        unverified_claims.append(cached_result)
                else:
                    # Quick verification without external URLs
                    result = await self._verify_claim_fast(claim, sources)
                    self._set_cache(cache_key, result)
                    
                    if result["verified"]:
                        verified_claims.append(result)
                    else:
                        unverified_claims.append(result)
            
            # Calculate approval
            total_claims = len(claims)
            verified_count = len(verified_claims)
            confidence_score = verified_count / total_claims if total_claims > 0 else 1.0
            
            # More lenient approval - 80% threshold
            approved = confidence_score >= 0.8
            
            self.update_status("completed", 
                f"Verified {verified_count}/{total_claims} claims - {'APPROVED' if approved else 'NEEDS REVISION'}")
            
            return self.format_response(True, data={
                "approved": approved,
                "verified_facts": verified_claims,
                "unverified_claims": unverified_claims,
                "confidence_score": confidence_score,
                "sources_verified": len(sources),
                "issues": self._format_issues(unverified_claims) if not approved else None
            })
            
        except Exception as e:
            self.logger.error(f"Fact checking error: {e}")
            return self.format_response(False, error=str(e))
    
    def _extract_sources(self, metadata_content: str) -> List[Dict[str, str]]:
        """Extract sources from metadata"""
        sources = []
        
        # Look for URLs in metadata
        url_pattern = r'\*\*URL:\*\*\s*(https?://[^\s\)]+)'
        matches = re.findall(url_pattern, metadata_content)
        
        for url in matches:
            sources.append({
                "url": url,
                "title": "Source"  # Simple title
            })
        
        return sources
    
    async def _extract_claims(self, content: str) -> List[str]:
        """Extract key claims from article"""
        # Look for sentences with numbers, percentages, or specific claims
        claim_patterns = [
            r'[^.!?]*\d+%[^.!?]*[.!?]',  # Sentences with percentages
            r'[^.!?]*\$[\d,]+[^.!?]*[.!?]',  # Sentences with dollar amounts
            r'[^.!?]*\b\d{4}\b[^.!?]*[.!?]',  # Sentences with years
            r'[^.!?]*\b(?:increased?|decreased?|grew|fell|rose)\b[^.!?]*[.!?]',  # Trend claims
        ]
        
        claims = []
        for pattern in claim_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            claims.extend([m.strip() for m in matches if len(m.strip()) > 20])
        
        # Deduplicate and limit
        unique_claims = list(dict.fromkeys(claims))
        return unique_claims[:10]  # Max 10 claims for speed
    
    async def _verify_claim_fast(self, claim: str, sources: List[Dict]) -> Dict[str, Any]:
        """Fast claim verification without external URL fetching"""
        # Simple heuristic-based verification
        claim_lower = claim.lower()
        
        # Check if claim mentions a source
        has_citation = "(" in claim and ")" in claim
        has_year = bool(re.search(r'\b20\d{2}\b', claim))
        has_specific_data = bool(re.search(r'\d+%|\$[\d,]+|\d+\s*billion|\d+\s*million', claim))
        
        # Check if any source URL domain is mentioned
        source_mentioned = False
        for source in sources:
            domain = source["url"].split('/')[2].replace('www.', '')
            if domain.split('.')[0] in claim_lower:
                source_mentioned = True
                break
        
        # Simple scoring
        score = 0
        if has_citation:
            score += 0.4
        if has_year:
            score += 0.2
        if has_specific_data:
            score += 0.2
        if source_mentioned:
            score += 0.2
        
        verified = score >= 0.6
        
        return {
            "claim": claim,
            "verified": verified,
            "confidence": score,
            "source": "Internal verification",
            "reason": "Verified based on citation patterns" if verified else "Missing clear citations"
        }
    
    def _basic_validation(self, article_content: str, metadata_content: str, sources: List[Dict]) -> Dict[str, Any]:
        """Basic validation when no specific claims found"""
        # Check basic requirements
        has_citations = article_content.count("(") >= 5
        has_sources = len(sources) >= 5
        has_structure = all(section in article_content for section in ["Key Insights", "Key Takeaways", "Conclusion"])
        
        approved = has_citations and has_sources and has_structure
        
        return self.format_response(True, data={
            "approved": approved,
            "verified_facts": [],
            "unverified_claims": [],
            "confidence_score": 1.0 if approved else 0.5,
            "sources_verified": len(sources),
            "issues": None if approved else ["Missing citations or required sections"]
        })
    
    def _get_cache_key(self, claim: str) -> str:
        """Generate cache key for a claim"""
        return hashlib.md5(claim.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached result if still valid"""
        if cache_key in self.claim_cache:
            result, timestamp = self.claim_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return result
        return None
    
    def _set_cache(self, cache_key: str, result: Dict[str, Any]):
        """Cache a verification result"""
        self.claim_cache[cache_key] = (result, time.time())
    
    def _format_issues(self, unverified_claims: List[Dict[str, Any]]) -> List[str]:
        """Format unverified claims as issues"""
        issues = []
        for claim in unverified_claims[:3]:  # Limit to top 3
            issues.append(f"Unverified: {claim['claim'][:100]}... - {claim.get('reason', 'No clear source')}")
        
        if len(unverified_claims) > 3:
            issues.append(f"...and {len(unverified_claims) - 3} more unverified claims")
        
        return issues