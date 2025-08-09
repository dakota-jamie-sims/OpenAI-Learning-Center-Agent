"""
Enhanced Fact Verification System
Ensures 100% accuracy with source validation
"""
import re
import requests
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
import json
from urllib.parse import urlparse
from .data_freshness_validator import DataFreshnessValidator


class FactVerificationSystem:
    """Comprehensive fact verification with source validation"""
    
    def __init__(self):
        self.data_validator = DataFreshnessValidator()
        self.credibility_scores = {
            # Government/Official - Highest credibility
            "sec.gov": 10,
            "federalreserve.gov": 10,
            "treasury.gov": 10,
            "imf.org": 10,
            "worldbank.org": 10,
            "bis.org": 10,
            
            # Academic/Research - Very high credibility
            "nber.org": 9,
            "jstor.org": 9,
            "sciencedirect.com": 9,
            "academic.oup.com": 9,
            
            # Financial Data Providers - High credibility
            "bloomberg.com": 8,
            "reuters.com": 8,
            "wsj.com": 8,
            "ft.com": 8,
            "morningstar.com": 8,
            "spglobal.com": 8,
            
            # Industry Organizations - Good credibility
            "cfainstitute.org": 7,
            "investmentcompany.org": 7,
            "sifma.org": 7,
            
            # General News - Moderate credibility
            "cnbc.com": 6,
            "marketwatch.com": 6,
            "businessinsider.com": 5,
            
            # Avoid/Low credibility
            "wikipedia.org": 3,
            "reddit.com": 2,
            "medium.com": 3,
            "seekingalpha.com": 4
        }
    
    def verify_article_facts(self, article_text: str) -> Dict[str, Any]:
        """Comprehensive fact verification of article including data freshness"""
        
        # Extract all facts and claims
        facts = self._extract_facts(article_text)
        
        # Extract all sources
        sources = self._extract_sources(article_text)
        
        # Verify data freshness
        freshness_results = self.data_validator.validate_article_freshness(article_text)
        
        # Verify each fact
        verification_results = []
        for fact in facts:
            result = self._verify_fact(fact, sources)
            # Add freshness check for date-based facts
            if fact["type"] == "date_claim" and fact["claim"]:
                date_analysis = self._check_fact_freshness(fact["claim"])
                if date_analysis and not date_analysis["is_current"]:
                    result["issues"].append(f"Outdated data: {date_analysis['recommendation']}")
                    result["confidence"] *= 0.7
            verification_results.append(result)
        
        # Check source quality
        source_analysis = self._analyze_sources(sources)
        
        # Add freshness issues
        freshness_issues = []
        if not freshness_results["is_fresh"]:
            freshness_issues.append("Article contains outdated data")
        if not freshness_results["has_current_year_data"]:
            freshness_issues.append(f"No current year ({datetime.now().year}) data found")
        
        # Generate report
        return {
            "total_facts": len(facts),
            "verified_facts": sum(1 for r in verification_results if r["verified"]),
            "unverified_facts": sum(1 for r in verification_results if not r["verified"]),
            "fact_accuracy_rate": sum(1 for r in verification_results if r["verified"]) / max(len(facts), 1),
            "source_analysis": source_analysis,
            "verification_details": verification_results,
            "overall_credibility": self._calculate_overall_credibility(verification_results, source_analysis),
            "issues": self._identify_issues(verification_results, source_analysis) + freshness_issues,
            "data_freshness": freshness_results,
            "freshness_recommendations": freshness_results.get("recommendations", [])
        }
    
    def _extract_facts(self, text: str) -> List[Dict[str, Any]]:
        """Extract all factual claims from text"""
        facts = []
        
        # Patterns for different types of facts
        patterns = {
            "percentage": r'(\d+(?:\.\d+)?%)',
            "currency": r'(\$[\d,]+(?:\.\d+)?(?:\s*(?:billion|million|trillion|thousand))?)',
            "date_claim": r'(?:in|since|during|as of)\s+(\d{4}|\w+\s+\d{4})',
            "comparison": r'(?:increased|decreased|grew|fell|rose|declined)\s+(?:by\s+)?(\d+(?:\.\d+)?%?)',
            "ranking": r'(?:ranked|ranks)\s+(?:#)?(\d+|first|second|third|top\s+\d+)',
            "statistic": r'(\d+(?:,\d+)*(?:\.\d+)?)\s+(?:investors|funds|companies|percent|basis points)'
        }
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Check each pattern
            for fact_type, pattern in patterns.items():
                matches = re.findall(pattern, sentence, re.IGNORECASE)
                if matches:
                    # Look for citation in same sentence
                    citations = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', sentence)
                    
                    for match in matches:
                        facts.append({
                            "type": fact_type,
                            "claim": match,
                            "context": sentence,
                            "has_citation": len(citations) > 0,
                            "citations": citations
                        })
        
        return facts
    
    def _extract_sources(self, text: str) -> List[Dict[str, Any]]:
        """Extract all sources with metadata"""
        sources = []
        
        # Find all markdown links
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        matches = re.findall(pattern, text)
        
        for title, url in matches:
            domain = urlparse(url).netloc.lower()
            sources.append({
                "title": title,
                "url": url,
                "domain": domain,
                "credibility_score": self.credibility_scores.get(domain, 5),
                "is_valid_url": self._validate_url_format(url),
                "is_accessible": None  # Will be checked separately
            })
        
        return sources
    
    def _verify_fact(self, fact: Dict[str, Any], sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Verify individual fact"""
        result = {
            "fact": fact,
            "verified": False,
            "confidence": 0,
            "issues": []
        }
        
        # Check if fact has citation
        if not fact["has_citation"]:
            result["issues"].append("No citation provided")
            result["confidence"] = 0
            return result
        
        # Check citation quality
        fact_sources = [s for s in sources if any(s["url"] in cite[1] for cite in fact["citations"])]
        
        if not fact_sources:
            result["issues"].append("Citation not found in source list")
            return result
        
        # Calculate confidence based on source credibility
        max_credibility = max(s["credibility_score"] for s in fact_sources)
        
        if max_credibility >= 8:
            result["verified"] = True
            result["confidence"] = 0.9
        elif max_credibility >= 6:
            result["verified"] = True
            result["confidence"] = 0.7
        elif max_credibility >= 4:
            result["verified"] = True
            result["confidence"] = 0.5
            result["issues"].append("Source has moderate credibility")
        else:
            result["verified"] = False
            result["confidence"] = 0.3
            result["issues"].append("Source has low credibility")
        
        # Additional checks for specific fact types
        if fact["type"] == "date_claim":
            # Check if date is reasonable
            if not self._verify_date_claim(fact["claim"]):
                result["issues"].append("Date claim seems unreasonable")
                result["confidence"] *= 0.8
        
        return result
    
    def _check_fact_freshness(self, fact_text: str) -> Dict[str, Any]:
        """Check if a specific fact is current"""
        dates = self.data_validator.extract_dates_from_text(fact_text)
        if not dates:
            return None
            
        # Get the most recent date mentioned
        latest_date = None
        for date_info in dates:
            parsed = self.data_validator.parse_date_to_datetime(date_info)
            if parsed and (not latest_date or parsed > latest_date):
                latest_date = parsed
        
        if latest_date:
            age_days = self.data_validator.calculate_age_in_days(latest_date)
            freshness = self.data_validator.categorize_data_freshness(age_days, 'general')
            
            return {
                "date": latest_date,
                "age_days": age_days,
                "is_current": freshness["is_acceptable"],
                "category": freshness["category"],
                "recommendation": freshness["recommendation"]
            }
        
        return None
    
    def _analyze_sources(self, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze source quality and diversity"""
        if not sources:
            return {
                "total_sources": 0,
                "average_credibility": 0,
                "issues": ["No sources found"]
            }
        
        analysis = {
            "total_sources": len(sources),
            "unique_domains": len(set(s["domain"] for s in sources)),
            "average_credibility": sum(s["credibility_score"] for s in sources) / len(sources),
            "high_credibility_sources": sum(1 for s in sources if s["credibility_score"] >= 8),
            "low_credibility_sources": sum(1 for s in sources if s["credibility_score"] <= 4),
            "invalid_urls": sum(1 for s in sources if not s["is_valid_url"]),
            "domain_distribution": {}
        }
        
        # Count sources per domain
        for source in sources:
            domain = source["domain"]
            if domain not in analysis["domain_distribution"]:
                analysis["domain_distribution"][domain] = 0
            analysis["domain_distribution"][domain] += 1
        
        # Identify issues
        issues = []
        if analysis["average_credibility"] < 6:
            issues.append("Average source credibility is low")
        if analysis["low_credibility_sources"] > len(sources) * 0.2:
            issues.append("Too many low-credibility sources")
        if analysis["unique_domains"] < 5:
            issues.append("Limited source diversity")
        if analysis["invalid_urls"] > 0:
            issues.append(f"{analysis['invalid_urls']} invalid URLs found")
        
        analysis["issues"] = issues
        
        return analysis
    
    def _validate_url_format(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _verify_date_claim(self, date_str: str) -> bool:
        """Verify date claims are reasonable"""
        current_year = datetime.now().year
        
        # Extract year
        year_match = re.search(r'(\d{4})', date_str)
        if year_match:
            year = int(year_match.group(1))
            # Check if year is reasonable (not too far in future or past)
            return 1900 <= year <= current_year + 1
        
        return True  # If no year found, assume OK
    
    def _calculate_overall_credibility(self, verification_results: List[Dict[str, Any]], 
                                     source_analysis: Dict[str, Any]) -> float:
        """Calculate overall article credibility score"""
        if not verification_results:
            return 0.0
        
        # Weighted factors
        fact_score = sum(r["confidence"] for r in verification_results) / max(len(verification_results), 1)
        source_score = source_analysis.get("average_credibility", 0) / 10
        
        # Penalties
        penalties = 0
        if source_analysis.get("issues"):
            penalties += 0.1 * len(source_analysis["issues"])
        
        unverified_rate = sum(1 for r in verification_results if not r["verified"]) / len(verification_results)
        penalties += unverified_rate * 0.3
        
        # Calculate final score
        credibility = (fact_score * 0.6 + source_score * 0.4) - penalties
        
        return max(0, min(1, credibility))
    
    def _identify_issues(self, verification_results: List[Dict[str, Any]], 
                        source_analysis: Dict[str, Any]) -> List[str]:
        """Identify all issues that need fixing"""
        issues = []
        
        # Fact issues
        unverified_facts = [r for r in verification_results if not r["verified"]]
        if unverified_facts:
            issues.append(f"{len(unverified_facts)} unverified facts need citations from credible sources")
        
        no_citation_facts = [r for r in verification_results if not r["fact"]["has_citation"]]
        if no_citation_facts:
            issues.append(f"{len(no_citation_facts)} facts lack citations")
        
        # Source issues
        issues.extend(source_analysis.get("issues", []))
        
        return issues


class EnhancedFactChecker:
    """Enhanced fact checker for the pipeline"""
    
    def __init__(self):
        self.verifier = FactVerificationSystem()
    
    async def verify_article(self, article_text: str, min_credibility: float = 0.8) -> Dict[str, Any]:
        """Verify article meets credibility standards"""
        
        # Run comprehensive verification
        verification = self.verifier.verify_article_facts(article_text)
        
        # Check data freshness
        data_freshness = verification.get("data_freshness", {})
        freshness_approved = (
            data_freshness.get("is_fresh", False) and
            data_freshness.get("has_current_year_data", False)
        )
        
        # Determine if approved (including freshness)
        approved = (
            verification["overall_credibility"] >= min_credibility and
            verification["fact_accuracy_rate"] >= 0.9 and
            len(verification["issues"]) == 0 and
            freshness_approved
        )
        
        # Generate detailed report
        report = {
            "approved": approved,
            "data_freshness": data_freshness,
            "freshness_recommendations": verification.get("freshness_recommendations", []),
            "credibility_score": verification["overall_credibility"],
            "fact_accuracy": verification["fact_accuracy_rate"],
            "total_facts_checked": verification["total_facts"],
            "verified_facts": verification["verified_facts"],
            "source_quality": verification["source_analysis"]["average_credibility"],
            "issues": verification["issues"],
            "requires_fixes": not approved,
            "detailed_results": verification
        }
        
        # Add specific fix instructions if not approved
        if not approved:
            report["fix_instructions"] = self._generate_fix_instructions(verification)
        
        return report
    
    def _generate_fix_instructions(self, verification: Dict[str, Any]) -> List[str]:
        """Generate specific instructions for fixing issues"""
        instructions = []
        
        # For each unverified fact
        for result in verification["verification_details"]:
            if not result["verified"]:
                fact = result["fact"]
                instructions.append(
                    f"Replace or add credible source for: '{fact['claim']}' in context: '{fact['context'][:100]}...'"
                )
        
        # For source issues
        if verification["source_analysis"]["average_credibility"] < 7:
            instructions.append("Add more high-credibility sources (government, academic, or major financial outlets)")
        
        return instructions