"""Fact Checker V3 - Optimized with caching and parallel verification"""

import asyncio
import re
from typing import Dict, Any, List, Tuple

from .base_agent_v2 import DakotaBaseAgentV2
from src.services.kb_search_production_v2 import search_kb_production_v2, batch_search_kb_production_v2
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DakotaFactCheckerV3(DakotaBaseAgentV2):
    """Optimized fact checker with parallel claim verification"""
    
    def __init__(self):
        super().__init__("fact_checker", model_override="gpt-5-mini")
        self.verification_cache = {}
        self.source_cache = {}
    
    async def _execute_impl(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute optimized fact checking"""
        article_file = task.get("article_file", "")
        metadata_file = task.get("metadata_file", "")
        use_cache = task.get("use_cache", True)
        
        self.update_status("active", "Starting optimized fact checking")
        
        try:
            # Read files
            with open(article_file, 'r') as f:
                article_content = f.read()
            
            with open(metadata_file, 'r') as f:
                metadata_content = f.read()
            
            # Extract claims to verify
            claims = await self._extract_claims(article_content)
            
            if not claims:
                self.logger.warning("No verifiable claims found")
                return self.format_response(True, data={
                    "approved": True,
                    "verified_facts": [],
                    "unverified_claims": [],
                    "confidence_score": 1.0,
                    "sources_verified": 0
                })
            
            # Verify claims in parallel
            verification_results = await self._verify_claims_parallel(claims, use_cache)
            
            # Analyze results
            verified_count = sum(1 for v in verification_results if v["verified"])
            total_claims = len(verification_results)
            confidence_score = verified_count / total_claims if total_claims > 0 else 0
            
            # Determine approval (require 100% verification)
            approved = verified_count == total_claims
            
            # Prepare response
            verified_facts = [v for v in verification_results if v["verified"]]
            unverified_claims = [v for v in verification_results if not v["verified"]]
            
            self.update_status("completed", 
                f"Verified {verified_count}/{total_claims} claims - {'APPROVED' if approved else 'REJECTED'}")
            
            return self.format_response(True, data={
                "approved": approved,
                "verified_facts": verified_facts,
                "unverified_claims": unverified_claims,
                "confidence_score": confidence_score,
                "sources_verified": len(set(v.get("source", "") for v in verified_facts if v.get("source"))),
                "issues": self._format_issues(unverified_claims) if not approved else None
            })
            
        except Exception as e:
            self.logger.error(f"Fact checking error: {e}")
            return self.format_response(False, error=str(e))
    
    async def _extract_claims(self, content: str) -> List[Dict[str, Any]]:
        """Extract verifiable claims from content"""
        prompt = f"""Extract verifiable claims from this article that need fact-checking.

Focus on:
- Statistics and numbers
- Market data and trends
- Company/organization information
- Investment performance claims
- Geographic-specific data

Article excerpt:
{content[:2000]}

Return claims in this format:
CLAIM: [specific claim]
TYPE: [statistic/trend/company/performance/geographic]

Extract up to 10 most important claims."""
        
        try:
            response = await self.query_llm(prompt, max_tokens=500)
            
            claims = []
            claim_pattern = r'CLAIM: (.+?)\nTYPE: (.+?)(?:\n|$)'
            
            for match in re.finditer(claim_pattern, response, re.MULTILINE):
                claims.append({
                    "claim": match.group(1).strip(),
                    "type": match.group(2).strip()
                })
            
            return claims[:10]  # Limit to 10 claims
            
        except Exception as e:
            self.logger.error(f"Claim extraction error: {e}")
            return []
    
    async def _verify_claims_parallel(self, claims: List[Dict[str, Any]], use_cache: bool) -> List[Dict[str, Any]]:
        """Verify multiple claims in parallel"""
        # Group claims by type for batch searching
        claim_groups = {}
        for claim in claims:
            claim_type = claim["type"]
            if claim_type not in claim_groups:
                claim_groups[claim_type] = []
            claim_groups[claim_type].append(claim)
        
        # Create verification tasks
        verification_tasks = []
        
        for claim in claims:
            if use_cache and claim["claim"] in self.verification_cache:
                # Use cached result
                verification_tasks.append(
                    asyncio.create_task(
                        asyncio.sleep(0.01).then(lambda: self.verification_cache[claim["claim"]])
                    )
                )
            else:
                # Verify claim
                verification_tasks.append(
                    asyncio.create_task(self._verify_single_claim(claim))
                )
        
        # Execute all verifications in parallel
        results = await asyncio.gather(*verification_tasks, return_exceptions=True)
        
        # Process results and cache
        verified_results = []
        for claim, result in zip(claims, results):
            if isinstance(result, Exception):
                self.logger.error(f"Verification failed for claim: {claim['claim']}")
                verified_results.append({
                    "claim": claim["claim"],
                    "verified": False,
                    "error": str(result)
                })
            else:
                if use_cache:
                    self.verification_cache[claim["claim"]] = result
                verified_results.append(result)
        
        return verified_results
    
    async def _verify_single_claim(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a single claim against KB"""
        try:
            # Search for verification
            search_query = self._generate_verification_query(claim)
            
            # Use cached search if available
            if search_query in self.source_cache:
                search_result = self.source_cache[search_query]
            else:
                search_result = await search_kb_production_v2(search_query, max_results=3)
                self.source_cache[search_query] = search_result
            
            if not search_result.get("success") or not search_result.get("results"):
                return {
                    "claim": claim["claim"],
                    "verified": False,
                    "reason": "No sources found"
                }
            
            # Verify against search results
            verification = await self._check_claim_against_sources(
                claim["claim"],
                search_result["results"]
            )
            
            return {
                "claim": claim["claim"],
                "verified": verification["verified"],
                "confidence": verification["confidence"],
                "source": verification.get("source", ""),
                "reason": verification.get("reason", "")
            }
            
        except Exception as e:
            self.logger.error(f"Claim verification error: {e}")
            return {
                "claim": claim["claim"],
                "verified": False,
                "error": str(e)
            }
    
    def _generate_verification_query(self, claim: Dict[str, Any]) -> str:
        """Generate search query for claim verification"""
        claim_text = claim["claim"]
        claim_type = claim["type"]
        
        # Extract key terms
        if claim_type == "statistic":
            # Focus on numbers and metrics
            return re.sub(r'[^\w\s\d%$]', '', claim_text)
        elif claim_type == "company":
            # Extract company names
            return claim_text
        else:
            # General search
            return claim_text[:100]
    
    async def _check_claim_against_sources(self, claim: str, sources: str) -> Dict[str, Any]:
        """Check if claim is supported by sources"""
        prompt = f"""Verify if this claim is supported by the Dakota KB sources:

CLAIM: {claim}

SOURCES:
{sources[:1500]}

Analyze if the claim is:
1. VERIFIED - Directly supported by sources
2. PARTIALLY VERIFIED - Related info found but not exact
3. NOT VERIFIED - No supporting evidence

Return:
VERDICT: [VERIFIED/PARTIALLY VERIFIED/NOT VERIFIED]
CONFIDENCE: [0-1 score]
REASON: [Brief explanation]"""
        
        try:
            response = await self.query_llm(prompt, max_tokens=200, use_cache=True)
            
            # Parse response
            verdict_match = re.search(r'VERDICT: (.+)', response)
            confidence_match = re.search(r'CONFIDENCE: ([\d.]+)', response)
            reason_match = re.search(r'REASON: (.+)', response)
            
            verdict = verdict_match.group(1).strip() if verdict_match else "NOT VERIFIED"
            confidence = float(confidence_match.group(1)) if confidence_match else 0.0
            reason = reason_match.group(1).strip() if reason_match else ""
            
            return {
                "verified": verdict == "VERIFIED",
                "confidence": confidence,
                "reason": reason,
                "source": "Dakota Knowledge Base"
            }
            
        except Exception as e:
            self.logger.error(f"Source checking error: {e}")
            return {
                "verified": False,
                "confidence": 0.0,
                "reason": "Verification error"
            }
    
    def _format_issues(self, unverified_claims: List[Dict[str, Any]]) -> List[str]:
        """Format unverified claims as issues"""
        issues = []
        for claim in unverified_claims:
            issue = f"Unverified claim: {claim['claim']}"
            if claim.get("reason"):
                issue += f" - {claim['reason']}"
            issues.append(issue)
        return issues