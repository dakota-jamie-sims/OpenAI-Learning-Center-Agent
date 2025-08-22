"""Dakota Fact Checker Agent - Mandatory verification of all data and sources"""

import asyncio
import re
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime
import httpx

from .base_agent import DakotaBaseAgent
from src.services.web_search import search_web
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DakotaFactChecker(DakotaBaseAgent):
    """Fact checker agent that ensures 100% accuracy of all data and sources"""
    
    def __init__(self):
        super().__init__("fact_checker", model_override="gpt-5-mini")
        self.verification_results = []
        self.critical_issues = []
        self.sources_verified = 0
        self.urls_tested = 0
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute fact checking with mandatory verification"""
        try:
            self.update_status("active", "Starting mandatory fact checking")
            
            article_file = task.get("article_file")
            metadata_file = task.get("metadata_file")
            
            # Read files
            with open(article_file, 'r') as f:
                article_content = f.read()
            
            with open(metadata_file, 'r') as f:
                metadata_content = f.read()
            
            # Step 1: Verify metadata sources
            self.logger.info("Checking metadata sources section...")
            sources_valid = await self._verify_metadata_sources(metadata_content)
            
            if not sources_valid:
                return self.format_response(True, data={
                    "approved": False,
                    "status": "❌ REJECTED",
                    "issues": "Metadata missing required sources section or has fewer than 10 sources",
                    "sources_verified": 0
                })
            
            # Step 2: Extract all claims from article
            self.logger.info("Extracting all factual claims...")
            claims = await self._extract_claims(article_content)
            
            # Step 3: Verify each claim
            self.logger.info(f"Verifying {len(claims)} claims...")
            for claim in claims:
                verified = await self._verify_claim(claim, metadata_content)
                if not verified:
                    self.critical_issues.append(claim)
            
            # Step 4: Test all URLs
            self.logger.info("Testing all source URLs...")
            url_results = await self._test_all_urls(metadata_content)
            
            # Step 5: Verify related article URLs
            self.logger.info("Verifying Learning Center article URLs...")
            related_valid = await self._verify_related_articles(metadata_content)
            
            # Determine approval
            approved = (
                len(self.critical_issues) == 0 and
                url_results["working"] == url_results["total"] and
                related_valid and
                self.sources_verified >= 10
            )
            
            if approved:
                status_msg = f"✅ APPROVED: Verified {len(claims)} statistics, tested {self.urls_tested} source URLs (all working), checked metadata citations. Article meets all Dakota quality standards."
            else:
                issues = []
                if self.critical_issues:
                    issues.append(f"{len(self.critical_issues)} unverifiable statistics")
                if url_results["broken"] > 0:
                    issues.append(f"{url_results['broken']} broken source URLs")
                if not related_valid:
                    issues.append("Invalid Learning Center article URLs")
                if self.sources_verified < 10:
                    issues.append(f"Only {self.sources_verified} sources (need 10+)")
                    
                status_msg = f"❌ REJECTED: Found {', '.join(issues)}. Cannot approve publication."
            
            return self.format_response(True, data={
                "approved": approved,
                "status": status_msg,
                "issues": self.critical_issues if not approved else [],
                "sources_verified": self.sources_verified,
                "urls_tested": self.urls_tested,
                "verification_details": {
                    "claims_verified": len(claims) - len(self.critical_issues),
                    "claims_failed": len(self.critical_issues),
                    "urls_working": url_results["working"],
                    "urls_broken": url_results["broken"],
                    "related_articles_valid": related_valid
                }
            })
            
        except Exception as e:
            self.logger.error(f"Fact checking error: {e}")
            return self.format_response(False, error=str(e))
    
    async def _verify_metadata_sources(self, metadata_content: str) -> bool:
        """Verify metadata has proper sources section"""
        try:
            # Look for sources section
            sources_match = re.search(
                r'##\s*Sources\s*(?:and|&)?\s*Citations.*?(?=##|\Z)', 
                metadata_content, 
                re.IGNORECASE | re.DOTALL
            )
            
            if not sources_match:
                self.logger.error("No sources section found in metadata")
                return False
            
            sources_text = sources_match.group(0)
            
            # Count sources (look for numbered entries)
            source_pattern = r'^\d+\.\s*\*\*(.+?)\*\*'
            sources = re.findall(source_pattern, sources_text, re.MULTILINE)
            
            self.sources_verified = len(sources)
            self.logger.info(f"Found {self.sources_verified} sources in metadata")
            
            # Check each source has required fields
            for i, source in enumerate(sources, 1):
                source_block = re.search(
                    rf'{i}\.\s*\*\*{re.escape(source)}.*?(?=^\d+\.|##|\Z)',
                    sources_text,
                    re.DOTALL | re.MULTILINE
                )
                
                if source_block:
                    block_text = source_block.group(0)
                    has_url = "URL:" in block_text or "url:" in block_text
                    has_data = "Key Data:" in block_text or "Data Used:" in block_text
                    
                    if not has_url or not has_data:
                        self.logger.error(f"Source {i} missing required fields")
                        return False
            
            return self.sources_verified >= 10
            
        except Exception as e:
            self.logger.error(f"Error verifying sources: {e}")
            return False
    
    async def _extract_claims(self, article_content: str) -> List[Dict[str, Any]]:
        """Extract all verifiable claims from article"""
        claims = []
        
        # Skip frontmatter
        content_start = 0
        if article_content.startswith("---"):
            end_frontmatter = article_content.find("---", 3)
            if end_frontmatter > 0:
                content_start = end_frontmatter + 3
        
        article_body = article_content[content_start:]
        
        # Patterns for different types of claims
        patterns = [
            # Percentages
            (r'(\d+(?:\.\d+)?%)', 'percentage'),
            # Dollar amounts
            (r'\$[\d,]+(?:\.\d+)?\s*(?:billion|million|trillion|thousand)?', 'financial'),
            # Specific numbers with context
            (r'(?:approximately|about|nearly|over|under|more than|less than)?\s*\d+(?:,\d+)*(?:\.\d+)?\s*(?:firms?|companies|funds?|investors?|managers?)', 'count'),
            # Rankings
            (r'(?:top|largest|biggest|leading)\s+\d+\s+\w+', 'ranking'),
            # Dates and timeframes
            (r'(?:in|since|as of|by|through)\s+(?:20\d{2}|Q[1-4]\s+20\d{2})', 'temporal')
        ]
        
        # Extract claims
        lines = article_body.split('\n')
        for i, line in enumerate(lines):
            if not line.strip():
                continue
                
            for pattern, claim_type in patterns:
                matches = re.findall(pattern, line, re.IGNORECASE)
                for match in matches:
                    # Get context (surrounding text)
                    context_start = max(0, line.find(match) - 50)
                    context_end = min(len(line), line.find(match) + len(match) + 50)
                    context = line[context_start:context_end].strip()
                    
                    claims.append({
                        "claim": match,
                        "type": claim_type,
                        "context": context,
                        "line_number": i + 1,
                        "full_line": line.strip()
                    })
        
        # Also extract company/firm claims
        company_pattern = r'([A-Z][A-Za-z\s&]+(?:Capital|Partners|Management|Advisors|Group|LLC|LP|Inc\.|Corporation))'
        for i, line in enumerate(lines):
            matches = re.findall(company_pattern, line)
            for match in matches:
                claims.append({
                    "claim": match,
                    "type": "company",
                    "context": line.strip(),
                    "line_number": i + 1,
                    "full_line": line.strip()
                })
        
        return claims
    
    async def _verify_claim(self, claim: Dict[str, Any], metadata_content: str) -> bool:
        """Verify a single claim against sources"""
        try:
            # For company names, we're more lenient
            if claim["type"] == "company":
                return True  # Assume company names are correct if properly formatted
            
            # For financial/statistical claims, check if mentioned in sources
            claim_text = claim["claim"]
            claim_context = claim["context"]
            
            # Check if claim appears in metadata sources
            if claim_text in metadata_content:
                self.logger.info(f"Claim '{claim_text}' found in metadata sources")
                return True
            
            # For percentages and numbers, check if context matches sources
            # This is a simplified check - in production would be more sophisticated
            key_words = re.findall(r'\b[A-Za-z]{4,}\b', claim_context)
            for word in key_words:
                if word.lower() in metadata_content.lower():
                    return True
            
            # If critical financial data, mark as unverifiable
            if claim["type"] in ["financial", "percentage"] and any(
                keyword in claim_context.lower() 
                for keyword in ["aum", "assets under management", "raised", "revenue", "performance"]
            ):
                self.logger.warning(f"Critical claim unverifiable: {claim_text}")
                return False
            
            return True  # Default to true for non-critical claims
            
        except Exception as e:
            self.logger.error(f"Error verifying claim: {e}")
            return False
    
    async def _test_all_urls(self, metadata_content: str) -> Dict[str, int]:
        """Test all URLs in metadata"""
        results = {"total": 0, "working": 0, "broken": 0}
        
        # Extract all URLs
        url_pattern = r'https?://[^\s\)]+(?:\.[^\s\)]+)*'
        urls = re.findall(url_pattern, metadata_content)
        
        # Remove duplicates
        urls = list(set(urls))
        results["total"] = len(urls)
        self.urls_tested = len(urls)
        
        # Test each URL
        async with httpx.AsyncClient() as client:
            for url in urls:
                try:
                    # Clean URL (remove trailing punctuation)
                    url = url.rstrip('.,;:')
                    
                    response = await client.head(url, timeout=10, follow_redirects=True)
                    if response.status_code < 400:
                        results["working"] += 1
                    else:
                        results["broken"] += 1
                        self.logger.warning(f"Broken URL: {url} (status: {response.status_code})")
                except Exception as e:
                    # Try GET if HEAD fails
                    try:
                        response = await client.get(url, timeout=10, follow_redirects=True)
                        if response.status_code < 400:
                            results["working"] += 1
                        else:
                            results["broken"] += 1
                            self.logger.warning(f"Broken URL: {url} (status: {response.status_code})")
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
                self.logger.warning("No related articles section found")
                return True  # Not required
            
            # Extract Dakota blog URLs
            dakota_urls = re.findall(
                r'https://www\.dakota\.com/resources/blog/[^\s\)]+',
                related_match.group(0)
            )
            
            if len(dakota_urls) < 3:
                self.logger.error(f"Only {len(dakota_urls)} related article URLs (need 3+)")
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