"""
Specialized agents for quality assurance and compliance
"""
from typing import Dict, Any, List, Tuple, Optional
import re
import json
from datetime import datetime

from src.agents.multi_agent_base import BaseAgent, AgentMessage, AgentStatus
from src.config import DEFAULT_MODELS, MIN_WORD_COUNT, MIN_SOURCES


class FactCheckerAgent(BaseAgent):
    """Agent specialized in fact-checking and verification"""
    
    def __init__(self):
        super().__init__(
            agent_id="fact_checker_001",
            agent_type="fact_checker",
            team="quality"
        )
        self.capabilities = [
            "verify_facts",
            "check_statistics",
            "validate_claims",
            "cross_reference",
            "accuracy_assessment"
        ]
        self.model = DEFAULT_MODELS.get("fact_checker", "gpt-5")
    
    def validate_task(self, task: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate fact-checking tasks"""
        valid_tasks = [
            "verify_facts", "check_statistics", "validate_claims",
            "cross_reference", "accuracy_assessment", "verify_sources"
        ]
        
        if task not in valid_tasks:
            return False, f"Task '{task}' not supported by FactCheckerAgent"
        
        if "content" not in payload and "claims" not in payload:
            return False, "Missing 'content' or 'claims' in payload"
        
        return True, "Valid task"
    
    def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process fact-checking request"""
        task = message.task
        payload = message.payload
        
        if task == "verify_facts":
            result = self._verify_all_facts(payload)
        elif task == "check_statistics":
            result = self._check_statistics(payload)
        elif task == "validate_claims":
            result = self._validate_specific_claims(payload)
        elif task == "cross_reference":
            result = self._cross_reference_sources(payload)
        elif task == "accuracy_assessment":
            result = self._assess_overall_accuracy(payload)
        else:
            result = self._verify_source_claims(payload)
        
        return self._create_response(message, result)
    
    def _verify_all_facts(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Verify all facts in content"""
        content = payload.get("content", "")
        sources = payload.get("sources", [])
        
        # Extract factual claims
        claims = self._extract_factual_claims(content)
        
        # Verify each claim
        verification_results = []
        for claim in claims:
            verification = self._verify_single_claim(claim, sources)
            verification_results.append(verification)
        
        # Calculate accuracy score
        verified_count = sum(1 for v in verification_results if v["status"] == "VERIFIED")
        accuracy_score = (verified_count / len(verification_results) * 100) if verification_results else 100
        
        return {
            "success": True,
            "total_claims": len(claims),
            "verified_claims": verified_count,
            "unverified_claims": len(claims) - verified_count,
            "accuracy_score": accuracy_score,
            "verification_details": verification_results,
            "requires_correction": accuracy_score < 90
        }
    
    def _check_statistics(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Check all statistics in content"""
        content = payload.get("content", "")
        
        # Extract statistics
        statistics = self._extract_statistics(content)
        
        # Verify each statistic
        stat_checks = []
        for stat in statistics:
            check_result = self._verify_statistic(stat)
            stat_checks.append(check_result)
        
        valid_stats = sum(1 for s in stat_checks if s["valid"])
        
        return {
            "success": True,
            "total_statistics": len(statistics),
            "valid_statistics": valid_stats,
            "invalid_statistics": len(statistics) - valid_stats,
            "statistics_details": stat_checks,
            "recommendations": self._generate_stat_recommendations(stat_checks)
        }
    
    def _validate_specific_claims(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate specific claims provided"""
        claims = payload.get("claims", [])
        context = payload.get("context", "")
        
        validation_results = []
        for claim in claims:
            validation = self._deep_validate_claim(claim, context)
            validation_results.append(validation)
        
        confidence_scores = [v["confidence"] for v in validation_results]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        return {
            "success": True,
            "claims_validated": len(claims),
            "validation_results": validation_results,
            "average_confidence": avg_confidence,
            "high_confidence_claims": sum(1 for v in validation_results if v["confidence"] > 80),
            "low_confidence_claims": sum(1 for v in validation_results if v["confidence"] < 60)
        }
    
    def _cross_reference_sources(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Cross-reference claims across multiple sources"""
        content = payload.get("content", "")
        sources = payload.get("sources", [])
        
        # Extract claims with their sources
        sourced_claims = self._extract_sourced_claims(content)
        
        # Cross-reference each claim
        cross_ref_results = []
        for claim, source in sourced_claims:
            result = self._check_source_consistency(claim, source, sources)
            cross_ref_results.append(result)
        
        consistency_score = sum(r["consistency_score"] for r in cross_ref_results) / len(cross_ref_results) if cross_ref_results else 100
        
        return {
            "success": True,
            "claims_checked": len(sourced_claims),
            "consistency_score": consistency_score,
            "cross_reference_results": cross_ref_results,
            "conflicting_claims": [r for r in cross_ref_results if r["has_conflicts"]],
            "well_supported_claims": [r for r in cross_ref_results if r["support_level"] == "strong"]
        }
    
    def _assess_overall_accuracy(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive accuracy assessment"""
        content = payload.get("content", "")
        
        # Multiple accuracy checks
        fact_check = self._verify_all_facts({"content": content})
        stat_check = self._check_statistics({"content": content})
        
        # Date accuracy
        date_accuracy = self._check_date_accuracy(content)
        
        # Quote accuracy
        quote_accuracy = self._check_quote_accuracy(content)
        
        # Calculate overall accuracy
        accuracy_components = {
            "factual_accuracy": fact_check["accuracy_score"],
            "statistical_accuracy": (stat_check["valid_statistics"] / max(stat_check["total_statistics"], 1)) * 100,
            "date_accuracy": date_accuracy["accuracy_score"],
            "quote_accuracy": quote_accuracy["accuracy_score"]
        }
        
        overall_accuracy = sum(accuracy_components.values()) / len(accuracy_components)
        
        return {
            "success": True,
            "overall_accuracy_score": overall_accuracy,
            "accuracy_breakdown": accuracy_components,
            "total_issues": fact_check["unverified_claims"] + stat_check["invalid_statistics"],
            "recommendation": self._generate_accuracy_recommendation(overall_accuracy),
            "detailed_results": {
                "facts": fact_check,
                "statistics": stat_check,
                "dates": date_accuracy,
                "quotes": quote_accuracy
            }
        }
    
    def _verify_source_claims(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Verify claims match their cited sources"""
        content = payload.get("content", "")
        sources = payload.get("sources", [])
        
        # Extract claims with citations
        cited_claims = self._extract_cited_claims(content)
        
        verification_results = []
        for claim, citation in cited_claims:
            result = self._verify_claim_matches_source(claim, citation, sources)
            verification_results.append(result)
        
        matches = sum(1 for r in verification_results if r["matches_source"])
        
        return {
            "success": True,
            "claims_with_sources": len(cited_claims),
            "verified_matches": matches,
            "mismatched_claims": len(cited_claims) - matches,
            "verification_details": verification_results,
            "source_accuracy_rate": (matches / len(cited_claims) * 100) if cited_claims else 100
        }
    
    def _extract_factual_claims(self, content: str) -> List[Dict[str, str]]:
        """Extract factual claims from content"""
        claims = []
        sentences = content.split('.')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Look for factual indicators
            if any(indicator in sentence.lower() for indicator in [
                'percent', '%', 'million', 'billion', 'increased', 'decreased',
                'grew', 'fell', 'rose', 'dropped', 'study', 'report', 'according'
            ]):
                claims.append({
                    "claim": sentence,
                    "type": self._classify_claim_type(sentence),
                    "confidence_required": self._assess_claim_importance(sentence)
                })
        
        return claims
    
    def _verify_single_claim(self, claim: Dict[str, str], sources: List[Dict]) -> Dict[str, Any]:
        """Verify a single factual claim"""
        claim_text = claim["claim"]
        claim_type = claim["type"]
        
        verification_prompt = f"""Verify this {claim_type} claim:
"{claim_text}"

Available sources: {len(sources)}

Assess:
1. Is the claim factually accurate?
2. Is it properly attributed?
3. Is the data current?
4. Are there any nuances or caveats?

Return verification status: VERIFIED, PARTIALLY_VERIFIED, or UNVERIFIED"""

        verification = self.query_llm(
            verification_prompt,
            reasoning_effort="high",
            verbosity="medium"
        )
        
        # Parse verification result
        status = "UNVERIFIED"
        if "VERIFIED" in verification and "PARTIALLY" not in verification:
            status = "VERIFIED"
        elif "PARTIALLY" in verification:
            status = "PARTIALLY_VERIFIED"
        
        return {
            "claim": claim_text,
            "type": claim_type,
            "status": status,
            "verification_notes": verification,
            "requires_correction": status == "UNVERIFIED"
        }
    
    def _extract_statistics(self, content: str) -> List[Dict[str, Any]]:
        """Extract statistics from content"""
        statistics = []
        
        # Pattern for percentages
        percent_pattern = r'(\d+\.?\d*)\s*(?:%|percent)'
        for match in re.finditer(percent_pattern, content):
            context_start = max(0, match.start() - 50)
            context_end = min(len(content), match.end() + 50)
            context = content[context_start:context_end]
            
            statistics.append({
                "value": match.group(1),
                "type": "percentage",
                "context": context,
                "position": match.start()
            })
        
        # Pattern for large numbers
        number_pattern = r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:million|billion|trillion)'
        for match in re.finditer(number_pattern, content):
            context_start = max(0, match.start() - 50)
            context_end = min(len(content), match.end() + 50)
            context = content[context_start:context_end]
            
            statistics.append({
                "value": match.group(0),
                "type": "large_number",
                "context": context,
                "position": match.start()
            })
        
        return statistics
    
    def _verify_statistic(self, stat: Dict[str, Any]) -> Dict[str, Any]:
        """Verify a single statistic"""
        stat_prompt = f"""Verify this statistic:
Value: {stat['value']}
Type: {stat['type']}
Context: {stat['context']}

Check:
1. Is the number reasonable for this context?
2. Does it align with known data?
3. Is it properly attributed?
4. Is it current?

Return assessment."""

        assessment = self.query_llm(
            stat_prompt,
            reasoning_effort="medium",
            verbosity="low"
        )
        
        # Simple validation
        valid = not any(word in assessment.lower() for word in ['incorrect', 'wrong', 'false', 'outdated'])
        
        return {
            "statistic": stat['value'],
            "type": stat['type'],
            "valid": valid,
            "assessment": assessment,
            "context": stat['context'][:100] + "..."
        }
    
    def _generate_stat_recommendations(self, stat_checks: List[Dict]) -> List[str]:
        """Generate recommendations for statistics"""
        recommendations = []
        
        invalid_stats = [s for s in stat_checks if not s["valid"]]
        
        if invalid_stats:
            recommendations.append(f"Review and correct {len(invalid_stats)} invalid statistics")
            
            for stat in invalid_stats[:3]:  # Top 3
                recommendations.append(f"Verify statistic '{stat['statistic']}' - {stat['assessment'][:100]}...")
        
        # Check for missing attributions
        unattributed = [s for s in stat_checks if "attribution" in s["assessment"].lower()]
        if unattributed:
            recommendations.append(f"Add source attribution for {len(unattributed)} statistics")
        
        return recommendations
    
    def _deep_validate_claim(self, claim: str, context: str) -> Dict[str, Any]:
        """Deep validation of a specific claim"""
        validation_prompt = f"""Perform deep validation of this claim:
Claim: "{claim}"
Context: {context}

Validate:
1. Factual accuracy
2. Logical consistency
3. Supporting evidence
4. Potential biases
5. Alternative interpretations

Provide confidence score (0-100) and detailed analysis."""

        validation = self.query_llm(
            validation_prompt,
            reasoning_effort="high",
            verbosity="high"
        )
        
        # Extract confidence score
        confidence_match = re.search(r'confidence[:\s]+(\d+)', validation.lower())
        confidence = int(confidence_match.group(1)) if confidence_match else 75
        
        return {
            "claim": claim,
            "confidence": confidence,
            "validation_details": validation,
            "issues_found": self._extract_validation_issues(validation),
            "requires_revision": confidence < 70
        }
    
    def _extract_sourced_claims(self, content: str) -> List[Tuple[str, str]]:
        """Extract claims with their sources"""
        sourced_claims = []
        
        # Pattern for sentences ending with citations
        sentences = content.split('.')
        for sentence in sentences:
            if '[' in sentence and '](' in sentence:
                # Extract claim and source
                claim = re.sub(r'\[[^\]]+\]\([^)]+\)', '', sentence).strip()
                source_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', sentence)
                if source_match:
                    source = source_match.group(1)
                    sourced_claims.append((claim, source))
        
        return sourced_claims
    
    def _check_source_consistency(self, claim: str, source: str, all_sources: List[Dict]) -> Dict[str, Any]:
        """Check if claim is consistent across sources"""
        consistency_prompt = f"""Check consistency of this claim across sources:
Claim: "{claim}"
Primary source: {source}
Available sources: {len(all_sources)}

Assess:
1. Do other sources support this claim?
2. Are there conflicting reports?
3. What's the consensus view?
4. Are there important caveats?

Provide consistency score (0-100)."""

        consistency_check = self.query_llm(
            consistency_prompt,
            reasoning_effort="medium",
            verbosity="medium"
        )
        
        # Extract consistency score
        score_match = re.search(r'consistency[:\s]+(\d+)', consistency_check.lower())
        consistency_score = int(score_match.group(1)) if score_match else 80
        
        has_conflicts = "conflict" in consistency_check.lower() or "contradict" in consistency_check.lower()
        support_level = "strong" if consistency_score > 80 else "moderate" if consistency_score > 60 else "weak"
        
        return {
            "claim": claim[:100] + "...",
            "source": source,
            "consistency_score": consistency_score,
            "has_conflicts": has_conflicts,
            "support_level": support_level,
            "analysis": consistency_check
        }
    
    def _check_date_accuracy(self, content: str) -> Dict[str, Any]:
        """Check accuracy of dates in content"""
        import re
        from datetime import datetime
        
        current_year = datetime.now().year
        
        # Extract years
        year_pattern = r'\b(19|20)\d{2}\b'
        years = [(int(match.group()), match.start()) for match in re.finditer(year_pattern, content)]
        
        issues = []
        for year, position in years:
            # Check for future dates
            if year > current_year:
                context_start = max(0, position - 50)
                context_end = min(len(content), position + 50)
                context = content[context_start:context_end]
                issues.append({
                    "type": "future_date",
                    "year": year,
                    "context": context
                })
            
            # Check for very old dates that might be errors
            if year < 2000 and "historical" not in content[max(0, position-100):position+100].lower():
                context_start = max(0, position - 50)
                context_end = min(len(content), position + 50)
                context = content[context_start:context_end]
                issues.append({
                    "type": "potentially_outdated",
                    "year": year,
                    "context": context
                })
        
        accuracy_score = 100 - (len(issues) * 10)
        
        return {
            "total_dates": len(years),
            "issues_found": len(issues),
            "accuracy_score": max(0, accuracy_score),
            "date_issues": issues
        }
    
    def _check_quote_accuracy(self, content: str) -> Dict[str, Any]:
        """Check accuracy of quotes"""
        # Extract quotes
        quote_pattern = r'"([^"]+)"'
        quotes = re.findall(quote_pattern, content)
        
        if not quotes:
            return {
                "total_quotes": 0,
                "accuracy_score": 100,
                "issues": []
            }
        
        # For each quote, check if it's properly attributed
        issues = []
        for quote in quotes:
            # Check if quote is followed by attribution
            quote_pos = content.find(f'"{quote}"')
            following_text = content[quote_pos:quote_pos + 200]
            
            has_attribution = any(attr in following_text.lower() for attr in [
                'said', 'says', 'stated', 'according', 'wrote', 'explained'
            ])
            
            if not has_attribution:
                issues.append({
                    "quote": quote[:50] + "...",
                    "issue": "Missing attribution"
                })
        
        accuracy_score = 100 - (len(issues) / len(quotes) * 50)
        
        return {
            "total_quotes": len(quotes),
            "attributed_quotes": len(quotes) - len(issues),
            "accuracy_score": accuracy_score,
            "issues": issues
        }
    
    def _generate_accuracy_recommendation(self, accuracy_score: float) -> str:
        """Generate recommendation based on accuracy score"""
        if accuracy_score >= 95:
            return "Excellent accuracy - minor review recommended"
        elif accuracy_score >= 90:
            return "Good accuracy - address specific issues noted"
        elif accuracy_score >= 80:
            return "Acceptable accuracy - significant fact-checking needed"
        elif accuracy_score >= 70:
            return "Below standard - comprehensive fact-checking required"
        else:
            return "Major accuracy issues - extensive revision needed"
    
    def _extract_cited_claims(self, content: str) -> List[Tuple[str, str]]:
        """Extract claims that have citations"""
        cited_claims = []
        
        # Split by sentences and look for citations
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        for sentence in sentences:
            # Check if sentence has a citation
            citation_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', sentence)
            if citation_match:
                # Remove citation to get claim
                claim = re.sub(r'\[[^\]]+\]\([^)]+\)', '', sentence).strip()
                citation = citation_match.group(1)
                cited_claims.append((claim, citation))
        
        return cited_claims
    
    def _verify_claim_matches_source(self, claim: str, citation: str, sources: List[Dict]) -> Dict[str, Any]:
        """Verify claim matches its cited source"""
        verify_prompt = f"""Verify this claim matches its source:
Claim: "{claim}"
Citation: {citation}

Based on available sources, check:
1. Does the source support this claim?
2. Is the claim accurately representing the source?
3. Are there any misinterpretations?
4. Is important context missing?

Assess match quality."""

        verification = self.query_llm(
            verify_prompt,
            reasoning_effort="medium",
            verbosity="medium"
        )
        
        matches = not any(word in verification.lower() for word in [
            'mismatch', 'incorrect', 'misrepresent', 'false', 'unsupported'
        ])
        
        return {
            "claim": claim[:100] + "...",
            "citation": citation,
            "matches_source": matches,
            "verification_notes": verification
        }
    
    def _classify_claim_type(self, sentence: str) -> str:
        """Classify the type of factual claim"""
        sentence_lower = sentence.lower()
        
        if any(word in sentence_lower for word in ['percent', '%']):
            return "statistical"
        elif any(word in sentence_lower for word in ['million', 'billion', 'trillion']):
            return "numerical"
        elif any(word in sentence_lower for word in ['study', 'research', 'report']):
            return "research-based"
        elif any(word in sentence_lower for word in ['increased', 'decreased', 'grew', 'fell']):
            return "trend"
        else:
            return "general"
    
    def _assess_claim_importance(self, sentence: str) -> str:
        """Assess importance level of a claim"""
        # Key indicators of important claims
        if any(word in sentence.lower() for word in ['major', 'significant', 'critical', 'key']):
            return "high"
        elif any(word in sentence.lower() for word in ['according', 'report', 'study']):
            return "medium"
        else:
            return "standard"
    
    def _extract_validation_issues(self, validation_text: str) -> List[str]:
        """Extract validation issues from text"""
        issues = []
        
        issue_keywords = [
            'incorrect', 'inaccurate', 'false', 'misleading',
            'outdated', 'unsupported', 'questionable', 'bias'
        ]
        
        lines = validation_text.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in issue_keywords):
                issues.append(line.strip())
        
        return issues[:5]  # Top 5 issues


class ComplianceAgent(BaseAgent):
    """Agent specialized in compliance and regulatory checks"""
    
    def __init__(self):
        super().__init__(
            agent_id="compliance_agent_001",
            agent_type="compliance",
            team="quality"
        )
        self.capabilities = [
            "check_compliance",
            "verify_disclaimers",
            "check_regulations",
            "validate_claims",
            "risk_assessment"
        ]
        self.model = DEFAULT_MODELS.get("compliance", "gpt-5")
    
    def validate_task(self, task: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate compliance tasks"""
        valid_tasks = [
            "check_compliance", "verify_disclaimers", "check_regulations",
            "validate_claims", "risk_assessment", "review_content"
        ]
        
        if task not in valid_tasks:
            return False, f"Task '{task}' not supported by ComplianceAgent"
        
        return True, "Valid task"
    
    def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process compliance request"""
        task = message.task
        payload = message.payload
        
        if task == "check_compliance":
            result = self._check_full_compliance(payload)
        elif task == "verify_disclaimers":
            result = self._verify_disclaimers(payload)
        elif task == "check_regulations":
            result = self._check_regulatory_compliance(payload)
        elif task == "validate_claims":
            result = self._validate_investment_claims(payload)
        elif task == "risk_assessment":
            result = self._assess_compliance_risks(payload)
        else:
            result = self._review_content_compliance(payload)
        
        return self._create_response(message, result)
    
    def _check_full_compliance(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive compliance check"""
        content = payload.get("content", "")
        content_type = payload.get("content_type", "article")
        
        # Run multiple compliance checks
        checks = {
            "disclaimers": self._check_required_disclaimers(content),
            "investment_advice": self._check_investment_advice_compliance(content),
            "performance_claims": self._check_performance_claims(content),
            "regulatory_terms": self._check_regulatory_terminology(content),
            "risk_disclosures": self._check_risk_disclosures(content)
        }
        
        # Calculate compliance score
        total_checks = len(checks)
        passed_checks = sum(1 for check in checks.values() if check["compliant"])
        compliance_score = (passed_checks / total_checks) * 100
        
        # Identify critical issues
        critical_issues = []
        for check_name, check_result in checks.items():
            if not check_result["compliant"] and check_result.get("critical", False):
                critical_issues.extend(check_result.get("issues", []))
        
        return {
            "success": True,
            "compliance_score": compliance_score,
            "fully_compliant": compliance_score == 100,
            "checks_performed": checks,
            "critical_issues": critical_issues,
            "recommendations": self._generate_compliance_recommendations(checks)
        }
    
    def _verify_disclaimers(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Verify required disclaimers are present"""
        content = payload.get("content", "")
        required_disclaimers = payload.get("required_disclaimers", [
            "past performance",
            "investment risk",
            "not investment advice",
            "consult advisor"
        ])
        
        found_disclaimers = []
        missing_disclaimers = []
        
        for disclaimer in required_disclaimers:
            if self._check_disclaimer_present(content, disclaimer):
                found_disclaimers.append(disclaimer)
            else:
                missing_disclaimers.append(disclaimer)
        
        return {
            "success": True,
            "disclaimers_required": len(required_disclaimers),
            "disclaimers_found": len(found_disclaimers),
            "disclaimers_missing": len(missing_disclaimers),
            "missing_list": missing_disclaimers,
            "compliant": len(missing_disclaimers) == 0,
            "recommendations": self._generate_disclaimer_text(missing_disclaimers)
        }
    
    def _check_regulatory_compliance(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance with financial regulations"""
        content = payload.get("content", "")
        jurisdiction = payload.get("jurisdiction", "US")
        
        regulatory_checks = {
            "SEC_compliance": self._check_sec_compliance(content),
            "FINRA_compliance": self._check_finra_compliance(content),
            "advertising_rules": self._check_advertising_rules(content),
            "fair_balanced": self._check_fair_balanced_content(content)
        }
        
        issues = []
        for check_name, check_result in regulatory_checks.items():
            if not check_result["compliant"]:
                issues.extend(check_result.get("violations", []))
        
        return {
            "success": True,
            "jurisdiction": jurisdiction,
            "regulatory_checks": regulatory_checks,
            "total_violations": len(issues),
            "violations": issues,
            "compliant": len(issues) == 0,
            "risk_level": self._assess_regulatory_risk(issues)
        }
    
    def _validate_investment_claims(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Validate investment-related claims"""
        content = payload.get("content", "")
        
        # Extract investment claims
        investment_claims = self._extract_investment_claims(content)
        
        validation_results = []
        for claim in investment_claims:
            validation = self._validate_single_investment_claim(claim)
            validation_results.append(validation)
        
        non_compliant = [v for v in validation_results if not v["compliant"]]
        
        return {
            "success": True,
            "total_claims": len(investment_claims),
            "compliant_claims": len(investment_claims) - len(non_compliant),
            "non_compliant_claims": len(non_compliant),
            "validation_details": validation_results,
            "requires_revision": len(non_compliant) > 0,
            "revision_suggestions": self._generate_claim_revisions(non_compliant)
        }
    
    def _assess_compliance_risks(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Assess compliance risks in content"""
        content = payload.get("content", "")
        
        risk_factors = {
            "performance_guarantees": self._check_performance_guarantees(content),
            "misleading_statements": self._check_misleading_statements(content),
            "unsubstantiated_claims": self._check_unsubstantiated_claims(content),
            "selective_disclosure": self._check_selective_disclosure(content),
            "conflict_of_interest": self._check_conflict_disclosure(content)
        }
        
        # Calculate risk score
        risk_scores = {
            "performance_guarantees": 100 if risk_factors["performance_guarantees"]["found"] else 0,
            "misleading_statements": risk_factors["misleading_statements"]["risk_score"],
            "unsubstantiated_claims": risk_factors["unsubstantiated_claims"]["count"] * 20,
            "selective_disclosure": 50 if risk_factors["selective_disclosure"]["found"] else 0,
            "conflict_of_interest": 30 if not risk_factors["conflict_of_interest"]["disclosed"] else 0
        }
        
        overall_risk = min(100, sum(risk_scores.values()) / len(risk_scores))
        
        return {
            "success": True,
            "overall_risk_score": overall_risk,
            "risk_level": self._categorize_risk_level(overall_risk),
            "risk_factors": risk_factors,
            "risk_breakdown": risk_scores,
            "mitigation_recommendations": self._generate_risk_mitigation(risk_factors)
        }
    
    def _review_content_compliance(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """General content compliance review"""
        content = payload.get("content", "")
        
        review_prompt = f"""Review this content for compliance issues:

{content[:2000]}...

Check for:
1. Investment advice without disclaimers
2. Misleading or exaggerated claims
3. Unbalanced presentation of risks/rewards
4. Missing regulatory disclosures
5. Promotional language issues

Identify any compliance concerns."""

        review = self.query_llm(
            review_prompt,
            reasoning_effort="high",
            verbosity="high"
        )
        
        issues = self._extract_compliance_issues(review)
        
        return {
            "success": True,
            "review_complete": True,
            "issues_found": len(issues),
            "compliance_issues": issues,
            "overall_assessment": self._generate_compliance_assessment(issues),
            "recommended_actions": self._generate_compliance_actions(issues)
        }
    
    def _check_required_disclaimers(self, content: str) -> Dict[str, Any]:
        """Check for required disclaimers"""
        required_phrases = [
            "past performance",
            "not guarantee future",
            "investment risks",
            "consult",
            "not investment advice"
        ]
        
        found = []
        missing = []
        
        content_lower = content.lower()
        for phrase in required_phrases:
            if phrase in content_lower:
                found.append(phrase)
            else:
                missing.append(phrase)
        
        return {
            "compliant": len(missing) == 0,
            "found": found,
            "missing": missing,
            "critical": True
        }
    
    def _check_investment_advice_compliance(self, content: str) -> Dict[str, Any]:
        """Check investment advice compliance"""
        advice_indicators = [
            "you should invest",
            "we recommend buying",
            "best investment",
            "guaranteed returns",
            "can't lose"
        ]
        
        issues = []
        for indicator in advice_indicators:
            if indicator in content.lower():
                issues.append(f"Potential investment advice: '{indicator}'")
        
        return {
            "compliant": len(issues) == 0,
            "issues": issues,
            "critical": True
        }
    
    def _check_performance_claims(self, content: str) -> Dict[str, Any]:
        """Check performance claims compliance"""
        # Look for performance numbers
        performance_pattern = r'(\d+\.?\d*)\s*(?:%|percent)\s*(?:return|gain|growth|performance)'
        matches = re.findall(performance_pattern, content, re.IGNORECASE)
        
        issues = []
        if matches and "past performance" not in content.lower():
            issues.append("Performance claims without past performance disclaimer")
        
        if "guarantee" in content.lower() and any(match for match in matches):
            issues.append("Potential guaranteed return claim")
        
        return {
            "compliant": len(issues) == 0,
            "performance_claims": len(matches),
            "issues": issues,
            "critical": len(issues) > 0
        }
    
    def _check_regulatory_terminology(self, content: str) -> Dict[str, Any]:
        """Check proper use of regulatory terms"""
        regulated_terms = {
            "fiduciary": "Requires proper context",
            "guaranteed": "Cannot guarantee investment returns",
            "risk-free": "No investment is risk-free",
            "approved by SEC": "SEC does not approve investments"
        }
        
        issues = []
        for term, concern in regulated_terms.items():
            if term in content.lower():
                issues.append(f"Use of '{term}': {concern}")
        
        return {
            "compliant": len(issues) == 0,
            "issues": issues,
            "critical": False
        }
    
    def _check_risk_disclosures(self, content: str) -> Dict[str, Any]:
        """Check for adequate risk disclosures"""
        risk_terms = ["risk", "loss", "volatility", "uncertainty"]
        risk_mentions = sum(1 for term in risk_terms if term in content.lower())
        
        # Check balance of risk vs reward mentions
        reward_terms = ["return", "gain", "profit", "growth"]
        reward_mentions = sum(1 for term in reward_terms if term in content.lower())
        
        balanced = risk_mentions >= reward_mentions * 0.3  # At least 30% risk mentions
        
        return {
            "compliant": balanced and risk_mentions > 0,
            "risk_mentions": risk_mentions,
            "reward_mentions": reward_mentions,
            "balanced": balanced,
            "issues": [] if balanced else ["Unbalanced risk/reward presentation"]
        }
    
    def _check_disclaimer_present(self, content: str, disclaimer_type: str) -> bool:
        """Check if specific disclaimer is present"""
        disclaimer_patterns = {
            "past performance": [
                "past performance",
                "historical returns",
                "not indicative of future"
            ],
            "investment risk": [
                "investment risk",
                "risk of loss",
                "investments may lose value"
            ],
            "not investment advice": [
                "not investment advice",
                "educational purposes",
                "not a recommendation"
            ],
            "consult advisor": [
                "consult",
                "speak with",
                "professional advice"
            ]
        }
        
        patterns = disclaimer_patterns.get(disclaimer_type, [disclaimer_type])
        content_lower = content.lower()
        
        return any(pattern in content_lower for pattern in patterns)
    
    def _generate_disclaimer_text(self, missing_disclaimers: List[str]) -> Dict[str, str]:
        """Generate appropriate disclaimer text"""
        disclaimer_templates = {
            "past performance": "Past performance is not indicative of future results.",
            "investment risk": "All investments involve risk, including potential loss of principal.",
            "not investment advice": "This content is for educational purposes only and should not be considered investment advice.",
            "consult advisor": "Please consult with a qualified financial advisor before making investment decisions."
        }
        
        recommendations = {}
        for disclaimer in missing_disclaimers:
            recommendations[disclaimer] = disclaimer_templates.get(disclaimer, f"Add {disclaimer} disclaimer")
        
        return recommendations
    
    def _check_sec_compliance(self, content: str) -> Dict[str, Any]:
        """Check SEC compliance requirements"""
        violations = []
        
        # Check for testimonials without disclaimers
        if "client" in content.lower() and "results" in content.lower():
            if "not typical" not in content.lower():
                violations.append("Client testimonials without 'results not typical' disclaimer")
        
        # Check for cherry-picking disclosure
        if "best performing" in content.lower() or "top performer" in content.lower():
            if "selected" not in content.lower():
                violations.append("Performance cherry-picking without disclosure")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations
        }
    
    def _check_finra_compliance(self, content: str) -> Dict[str, Any]:
        """Check FINRA compliance requirements"""
        violations = []
        
        # Check for balanced presentation
        if content.count("benefit") > content.count("risk") * 3:
            violations.append("Unbalanced presentation of benefits vs risks")
        
        # Check for promissory language
        promissory_terms = ["will earn", "guaranteed", "assured", "promise"]
        for term in promissory_terms:
            if term in content.lower():
                violations.append(f"Promissory language: '{term}'")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations
        }
    
    def _check_advertising_rules(self, content: str) -> Dict[str, Any]:
        """Check advertising rule compliance"""
        violations = []
        
        # Check for untrue statements
        absolute_terms = ["always", "never", "best", "only", "unique"]
        for term in absolute_terms:
            if term in content.lower():
                # Check if properly qualified
                context_start = content.lower().find(term)
                context = content[max(0, context_start-50):context_start+50]
                if "one of" not in context.lower() and "among" not in context.lower():
                    violations.append(f"Unqualified absolute claim: '{term}'")
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations
        }
    
    def _check_fair_balanced_content(self, content: str) -> Dict[str, Any]:
        """Check for fair and balanced content"""
        # Count positive vs negative/neutral language
        positive_terms = ["profit", "gain", "growth", "return", "opportunity", "benefit"]
        negative_terms = ["risk", "loss", "volatility", "downside", "concern", "challenge"]
        
        positive_count = sum(content.lower().count(term) for term in positive_terms)
        negative_count = sum(content.lower().count(term) for term in negative_terms)
        
        balance_ratio = negative_count / max(positive_count, 1)
        balanced = balance_ratio >= 0.3  # At least 30% negative to positive
        
        return {
            "compliant": balanced,
            "positive_mentions": positive_count,
            "risk_mentions": negative_count,
            "balance_ratio": balance_ratio,
            "violations": [] if balanced else ["Content not fairly balanced"]
        }
    
    def _extract_investment_claims(self, content: str) -> List[str]:
        """Extract investment-related claims"""
        claims = []
        sentences = content.split('.')
        
        investment_keywords = [
            "return", "performance", "yield", "growth",
            "investment", "portfolio", "asset", "fund"
        ]
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in investment_keywords):
                # Check if sentence makes a claim
                if any(claim_word in sentence.lower() for claim_word in [
                    "will", "can", "should", "expect", "typical", "average"
                ]):
                    claims.append(sentence.strip())
        
        return claims
    
    def _validate_single_investment_claim(self, claim: str) -> Dict[str, Any]:
        """Validate a single investment claim"""
        issues = []
        
        # Check for guaranteed returns
        if "guarante" in claim.lower():
            issues.append("Cannot guarantee investment returns")
        
        # Check for promissory language
        if any(word in claim.lower() for word in ["will earn", "will return", "will grow"]):
            issues.append("Promissory language about future performance")
        
        # Check for unqualified superlatives
        if any(word in claim.lower() for word in ["best", "highest", "superior", "outperform"]):
            if not any(qualifier in claim.lower() for qualifier in ["may", "might", "could", "historically"]):
                issues.append("Unqualified performance comparison")
        
        return {
            "claim": claim[:100] + "...",
            "compliant": len(issues) == 0,
            "issues": issues
        }
    
    def _generate_claim_revisions(self, non_compliant_claims: List[Dict]) -> List[Dict[str, str]]:
        """Generate revisions for non-compliant claims"""
        revisions = []
        
        for claim_result in non_compliant_claims[:3]:  # Top 3
            claim = claim_result["claim"]
            issues = claim_result["issues"]
            
            revision = {
                "original": claim,
                "issues": issues,
                "suggested_revision": self._suggest_claim_revision(claim, issues)
            }
            revisions.append(revision)
        
        return revisions
    
    def _suggest_claim_revision(self, claim: str, issues: List[str]) -> str:
        """Suggest revision for a claim"""
        revised = claim
        
        # Handle guaranteed returns
        if any("guarantee" in issue.lower() for issue in issues):
            revised = revised.replace("guaranteed", "potential")
            revised = revised.replace("will", "may")
        
        # Handle promissory language
        if any("promissory" in issue.lower() for issue in issues):
            revised = revised.replace("will earn", "has historically earned")
            revised = revised.replace("will return", "has the potential to return")
        
        # Add disclaimers
        if revised != claim:
            revised += " Past performance does not guarantee future results."
        
        return revised
    
    def _check_performance_guarantees(self, content: str) -> Dict[str, bool]:
        """Check for performance guarantees"""
        guarantee_phrases = [
            "guaranteed return",
            "guaranteed performance",
            "will earn",
            "assured return",
            "promise"
        ]
        
        found = any(phrase in content.lower() for phrase in guarantee_phrases)
        
        return {
            "found": found,
            "phrases": [p for p in guarantee_phrases if p in content.lower()]
        }
    
    def _check_misleading_statements(self, content: str) -> Dict[str, Any]:
        """Check for potentially misleading statements"""
        misleading_patterns = [
            r"always\s+(?:profit|gain|return)",
            r"never\s+(?:lose|loss|down)",
            r"risk[\s-]free",
            r"guaranteed\s+(?!not)"
        ]
        
        found_patterns = []
        for pattern in misleading_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                found_patterns.append(pattern)
        
        risk_score = len(found_patterns) * 25
        
        return {
            "patterns_found": found_patterns,
            "risk_score": min(100, risk_score)
        }
    
    def _check_unsubstantiated_claims(self, content: str) -> Dict[str, int]:
        """Check for unsubstantiated claims"""
        claim_indicators = [
            "proven",
            "studies show",
            "research indicates",
            "data shows",
            "evidence suggests"
        ]
        
        # Count claims
        claim_count = 0
        for indicator in claim_indicators:
            claim_count += content.lower().count(indicator)
        
        # Count citations
        citation_count = content.count('[')
        
        # Unsubstantiated if more claims than citations
        unsubstantiated = max(0, claim_count - citation_count)
        
        return {
            "count": unsubstantiated,
            "total_claims": claim_count,
            "citations": citation_count
        }
    
    def _check_selective_disclosure(self, content: str) -> Dict[str, bool]:
        """Check for selective disclosure issues"""
        selective_indicators = [
            "select period",
            "certain conditions",
            "specific circumstances",
            "cherry-pick"
        ]
        
        found = any(indicator in content.lower() for indicator in selective_indicators)
        
        # Check if properly disclosed
        disclosure_terms = ["selected", "not representative", "specific period"]
        disclosed = any(term in content.lower() for term in disclosure_terms)
        
        return {
            "found": found and not disclosed,
            "properly_disclosed": disclosed
        }
    
    def _check_conflict_disclosure(self, content: str) -> Dict[str, bool]:
        """Check for conflict of interest disclosure"""
        conflict_indicators = [
            "we own",
            "we hold",
            "our position",
            "dakota owns",
            "affiliate"
        ]
        
        has_potential_conflict = any(indicator in content.lower() for indicator in conflict_indicators)
        
        disclosure_present = any(phrase in content.lower() for phrase in [
            "disclosure",
            "conflict of interest",
            "may have a position"
        ])
        
        return {
            "potential_conflict": has_potential_conflict,
            "disclosed": disclosure_present or not has_potential_conflict
        }
    
    def _categorize_risk_level(self, risk_score: float) -> str:
        """Categorize compliance risk level"""
        if risk_score >= 70:
            return "HIGH"
        elif risk_score >= 40:
            return "MEDIUM"
        elif risk_score >= 20:
            return "LOW"
        else:
            return "MINIMAL"
    
    def _generate_risk_mitigation(self, risk_factors: Dict[str, Any]) -> List[str]:
        """Generate risk mitigation recommendations"""
        recommendations = []
        
        if risk_factors["performance_guarantees"]["found"]:
            recommendations.append("Remove all performance guarantees and add appropriate disclaimers")
        
        if risk_factors["misleading_statements"]["risk_score"] > 50:
            recommendations.append("Review and revise absolute statements about performance")
        
        if risk_factors["unsubstantiated_claims"]["count"] > 0:
            recommendations.append(f"Add citations for {risk_factors['unsubstantiated_claims']['count']} unsubstantiated claims")
        
        if risk_factors["selective_disclosure"]["found"]:
            recommendations.append("Add disclosure about selective time periods or conditions")
        
        if not risk_factors["conflict_of_interest"]["disclosed"]:
            recommendations.append("Add conflict of interest disclosure if applicable")
        
        return recommendations
    
    def _extract_compliance_issues(self, review_text: str) -> List[Dict[str, str]]:
        """Extract compliance issues from review text"""
        issues = []
        lines = review_text.split('\n')
        
        issue_keywords = [
            "compliance", "violation", "required", "missing",
            "must", "should", "need", "lack"
        ]
        
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in issue_keywords):
                issue = {
                    "description": line.strip(),
                    "severity": self._assess_issue_severity(line),
                    "category": self._categorize_issue(line)
                }
                issues.append(issue)
        
        return issues
    
    def _assess_issue_severity(self, issue_text: str) -> str:
        """Assess severity of compliance issue"""
        high_severity_terms = ["violation", "prohibited", "illegal", "must"]
        medium_severity_terms = ["should", "recommended", "advised", "suggested"]
        
        issue_lower = issue_text.lower()
        
        if any(term in issue_lower for term in high_severity_terms):
            return "HIGH"
        elif any(term in issue_lower for term in medium_severity_terms):
            return "MEDIUM"
        else:
            return "LOW"
    
    def _categorize_issue(self, issue_text: str) -> str:
        """Categorize compliance issue"""
        issue_lower = issue_text.lower()
        
        if "disclaimer" in issue_lower:
            return "disclaimer"
        elif "risk" in issue_lower:
            return "risk_disclosure"
        elif "performance" in issue_lower or "return" in issue_lower:
            return "performance_claims"
        elif "advice" in issue_lower:
            return "investment_advice"
        else:
            return "general"
    
    def _generate_compliance_assessment(self, issues: List[Dict]) -> str:
        """Generate overall compliance assessment"""
        if not issues:
            return "Content appears to be compliant with standard requirements"
        
        high_severity = sum(1 for issue in issues if issue["severity"] == "HIGH")
        
        if high_severity > 0:
            return f"CRITICAL: {high_severity} high-severity compliance issues require immediate attention"
        elif len(issues) > 5:
            return "Multiple compliance issues identified - comprehensive review recommended"
        else:
            return "Minor compliance issues identified - targeted revisions needed"
    
    def _generate_compliance_actions(self, issues: List[Dict]) -> List[str]:
        """Generate specific compliance actions"""
        actions = []
        
        # Group by category
        categories = {}
        for issue in issues:
            cat = issue["category"]
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(issue)
        
        # Generate actions by category
        if "disclaimer" in categories:
            actions.append(f"Add {len(categories['disclaimer'])} missing disclaimers")
        
        if "risk_disclosure" in categories:
            actions.append("Enhance risk disclosure sections")
        
        if "performance_claims" in categories:
            actions.append("Review and qualify all performance claims")
        
        if "investment_advice" in categories:
            actions.append("Add 'not investment advice' disclaimer or revise content")
        
        # Priority action for high severity
        high_severity = [i for i in issues if i["severity"] == "HIGH"]
        if high_severity:
            actions.insert(0, f"ADDRESS IMMEDIATELY: {len(high_severity)} critical compliance issues")
        
        return actions[:5]  # Top 5 actions
    
    def _generate_compliance_recommendations(self, checks: Dict[str, Dict]) -> List[str]:
        """Generate compliance recommendations based on checks"""
        recommendations = []
        
        for check_name, result in checks.items():
            if not result["compliant"]:
                if check_name == "disclaimers":
                    missing = result.get("missing", [])
                    recommendations.append(f"Add missing disclaimers: {', '.join(missing)}")
                elif check_name == "investment_advice":
                    recommendations.append("Remove direct investment advice or add proper disclaimers")
                elif check_name == "performance_claims":
                    recommendations.append("Add past performance disclaimer to all performance claims")
                elif check_name == "risk_disclosures":
                    recommendations.append("Balance risk disclosures with benefit statements")
                elif check_name == "regulatory_terms":
                    issues = result.get("issues", [])
                    for issue in issues[:2]:  # Top 2 issues
                        recommendations.append(f"Address regulatory term issue: {issue}")
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _assess_regulatory_risk(self, violations: List[str]) -> str:
        """Assess regulatory risk level based on violations"""
        if not violations:
            return "LOW"
        elif len(violations) == 1:
            return "MEDIUM"
        elif len(violations) <= 3:
            return "HIGH"
        else:
            return "CRITICAL"


class QualityAssuranceAgent(BaseAgent):
    """Agent specialized in overall quality assurance"""
    
    def __init__(self):
        super().__init__(
            agent_id="qa_agent_001",
            agent_type="quality_assurance",
            team="quality"
        )
        self.capabilities = [
            "quality_review",
            "readability_check",
            "coherence_check",
            "completeness_check",
            "final_approval"
        ]
        self.model = DEFAULT_MODELS.get("quality", "gpt-5")
    
    def validate_task(self, task: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate QA tasks"""
        valid_tasks = [
            "quality_review", "readability_check", "coherence_check",
            "completeness_check", "final_approval", "improvement_suggestions"
        ]
        
        if task not in valid_tasks:
            return False, f"Task '{task}' not supported by QualityAssuranceAgent"
        
        return True, "Valid task"
    
    def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process QA request"""
        task = message.task
        payload = message.payload
        
        if task == "quality_review":
            result = self._comprehensive_quality_review(payload)
        elif task == "readability_check":
            result = self._check_readability(payload)
        elif task == "coherence_check":
            result = self._check_coherence(payload)
        elif task == "completeness_check":
            result = self._check_completeness(payload)
        elif task == "final_approval":
            result = self._final_quality_approval(payload)
        else:
            result = self._generate_improvement_suggestions(payload)
        
        return self._create_response(message, result)
    
    def _comprehensive_quality_review(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive quality review of content"""
        content = payload.get("content", "")
        requirements = payload.get("requirements", {})
        
        # Run all quality checks
        quality_checks = {
            "readability": self._assess_readability(content),
            "structure": self._assess_structure(content),
            "coherence": self._assess_coherence(content),
            "completeness": self._assess_completeness(content, requirements),
            "engagement": self._assess_engagement(content),
            "professionalism": self._assess_professionalism(content),
            "data_quality": self._assess_data_quality(content),
            "actionability": self._assess_actionability(content)
        }
        
        # Calculate overall quality score
        scores = [check["score"] for check in quality_checks.values()]
        overall_score = sum(scores) / len(scores)
        
        # Identify areas needing improvement
        improvement_areas = []
        for area, check in quality_checks.items():
            if check["score"] < 80:
                improvement_areas.append({
                    "area": area,
                    "score": check["score"],
                    "issues": check.get("issues", [])
                })
        
        return {
            "success": True,
            "overall_quality_score": overall_score,
            "quality_grade": self._calculate_quality_grade(overall_score),
            "quality_checks": quality_checks,
            "improvement_areas": improvement_areas,
            "meets_standards": overall_score >= 85,
            "recommendations": self._generate_quality_recommendations(quality_checks)
        }
    
    def _check_readability(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Check content readability"""
        content = payload.get("content", "")
        target_audience = payload.get("target_audience", "institutional investors")
        
        # Calculate readability metrics
        metrics = self._calculate_readability_metrics(content)
        
        # Assess appropriateness for audience
        audience_appropriate = self._assess_audience_appropriateness(metrics, target_audience)
        
        # Find complex sections
        complex_sections = self._identify_complex_sections(content)
        
        return {
            "success": True,
            "readability_score": metrics["flesch_score"],
            "grade_level": metrics["grade_level"],
            "audience_appropriate": audience_appropriate,
            "metrics": metrics,
            "complex_sections": complex_sections,
            "recommendations": self._generate_readability_recommendations(metrics, complex_sections)
        }
    
    def _check_coherence(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Check content coherence and flow"""
        content = payload.get("content", "")
        
        # Analyze paragraph transitions
        transition_analysis = self._analyze_transitions(content)
        
        # Check logical flow
        flow_analysis = self._analyze_logical_flow(content)
        
        # Check theme consistency
        theme_consistency = self._analyze_theme_consistency(content)
        
        coherence_score = (
            transition_analysis["score"] * 0.3 +
            flow_analysis["score"] * 0.4 +
            theme_consistency["score"] * 0.3
        )
        
        return {
            "success": True,
            "coherence_score": coherence_score,
            "transition_quality": transition_analysis,
            "logical_flow": flow_analysis,
            "theme_consistency": theme_consistency,
            "is_coherent": coherence_score >= 80,
            "improvement_suggestions": self._generate_coherence_suggestions(
                transition_analysis, flow_analysis, theme_consistency
            )
        }
    
    def _check_completeness(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Check content completeness"""
        content = payload.get("content", "")
        requirements = payload.get("requirements", {})
        
        completeness_checks = {
            "word_count": self._check_word_count(content, requirements.get("word_count", 1500)),
            "sections": self._check_required_sections(content, requirements.get("sections", [])),
            "citations": self._check_citation_requirements(content, requirements.get("min_citations", 10)),
            "key_points": self._check_key_points_coverage(content, requirements.get("key_points", [])),
            "dakota_perspective": self._check_dakota_perspective(content)
        }
        
        # Calculate completeness score
        met_requirements = sum(1 for check in completeness_checks.values() if check["complete"])
        completeness_score = (met_requirements / len(completeness_checks)) * 100
        
        return {
            "success": True,
            "completeness_score": completeness_score,
            "requirements_met": met_requirements,
            "total_requirements": len(completeness_checks),
            "completeness_details": completeness_checks,
            "is_complete": completeness_score >= 90,
            "missing_elements": self._identify_missing_elements(completeness_checks)
        }
    
    def _final_quality_approval(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Final quality approval check"""
        content = payload.get("content", "")
        quality_reports = payload.get("quality_reports", {})
        
        # Compile all quality metrics
        approval_criteria = {
            "content_quality": self._assess_overall_content_quality(content, quality_reports),
            "technical_accuracy": quality_reports.get("fact_check", {}).get("accuracy_score", 0),
            "compliance_status": quality_reports.get("compliance", {}).get("compliance_score", 0),
            "readability_score": quality_reports.get("readability", {}).get("score", 0),
            "completeness": quality_reports.get("completeness", {}).get("score", 0)
        }
        
        # Check if all criteria meet thresholds
        thresholds = {
            "content_quality": 85,
            "technical_accuracy": 90,
            "compliance_status": 95,
            "readability_score": 80,
            "completeness": 95
        }
        
        criteria_met = {}
        for criterion, score in approval_criteria.items():
            criteria_met[criterion] = score >= thresholds.get(criterion, 80)
        
        approved = all(criteria_met.values())
        
        # Generate approval report
        approval_report = self._generate_approval_report(
            approval_criteria, criteria_met, thresholds
        )
        
        return {
            "success": True,
            "approved": approved,
            "approval_criteria": approval_criteria,
            "criteria_met": criteria_met,
            "approval_report": approval_report,
            "conditions": self._generate_approval_conditions(criteria_met),
            "final_score": sum(approval_criteria.values()) / len(approval_criteria)
        }
    
    def _generate_improvement_suggestions(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Generate specific improvement suggestions"""
        content = payload.get("content", "")
        quality_issues = payload.get("quality_issues", [])
        
        suggestions = {
            "high_priority": [],
            "medium_priority": [],
            "low_priority": []
        }
        
        # Analyze content for improvements
        improvement_areas = self._analyze_improvement_areas(content)
        
        # Prioritize suggestions
        for area in improvement_areas:
            suggestion = {
                "area": area["type"],
                "specific_action": area["action"],
                "expected_impact": area["impact"],
                "location": area.get("location", "general")
            }
            
            if area["priority"] == "high":
                suggestions["high_priority"].append(suggestion)
            elif area["priority"] == "medium":
                suggestions["medium_priority"].append(suggestion)
            else:
                suggestions["low_priority"].append(suggestion)
        
        # Add issue-specific suggestions
        for issue in quality_issues:
            suggestion = self._generate_issue_suggestion(issue)
            suggestions[suggestion["priority"]].append(suggestion["suggestion"])
        
        return {
            "success": True,
            "total_suggestions": sum(len(s) for s in suggestions.values()),
            "suggestions": suggestions,
            "estimated_improvement": self._estimate_quality_improvement(suggestions),
            "implementation_order": self._prioritize_implementation(suggestions)
        }
    
    def _assess_readability(self, content: str) -> Dict[str, Any]:
        """Assess content readability"""
        metrics = self._calculate_readability_metrics(content)
        
        # Score based on appropriateness for institutional investors
        score = 100
        
        # Ideal range for professional content
        if metrics["flesch_score"] < 30:
            score -= 20  # Too complex
        elif metrics["flesch_score"] > 60:
            score -= 10  # Too simple
        
        if metrics["avg_sentence_length"] > 25:
            score -= 10
        
        if metrics["complex_word_percentage"] > 20:
            score -= 10
        
        issues = []
        if score < 100:
            if metrics["flesch_score"] < 30:
                issues.append("Content too complex for efficient reading")
            if metrics["avg_sentence_length"] > 25:
                issues.append("Sentences too long on average")
        
        return {
            "score": max(0, score),
            "metrics": metrics,
            "issues": issues
        }
    
    def _assess_structure(self, content: str) -> Dict[str, Any]:
        """Assess content structure"""
        lines = content.split('\n')
        
        # Count structural elements
        headers = [line for line in lines if line.startswith('#')]
        paragraphs = content.split('\n\n')
        
        score = 100
        issues = []
        
        # Check header distribution
        if len(headers) < 5:
            score -= 20
            issues.append("Insufficient section headers")
        
        # Check paragraph length variation
        para_lengths = [len(p.split()) for p in paragraphs if p.strip()]
        if para_lengths:
            avg_length = sum(para_lengths) / len(para_lengths)
            if avg_length > 150:
                score -= 10
                issues.append("Paragraphs too long on average")
        
        # Check for introduction and conclusion
        has_intro = any(word in content[:500].lower() for word in ['introduction', 'overview', 'executive summary'])
        has_conclusion = any(word in content[-500:].lower() for word in ['conclusion', 'summary', 'takeaway'])
        
        if not has_intro:
            score -= 10
            issues.append("No clear introduction")
        
        if not has_conclusion:
            score -= 10
            issues.append("No clear conclusion")
        
        return {
            "score": max(0, score),
            "headers": len(headers),
            "paragraphs": len(paragraphs),
            "issues": issues
        }
    
    def _assess_coherence(self, content: str) -> Dict[str, Any]:
        """Assess content coherence"""
        coherence_prompt = f"""Assess the coherence of this content:

{content[:1500]}...

Rate coherence (0-100) based on:
1. Logical flow between sections
2. Consistent themes throughout
3. Clear progression of ideas
4. Smooth transitions
5. Unity of purpose

Identify any coherence issues."""

        assessment = self.query_llm(
            coherence_prompt,
            reasoning_effort="high",
            verbosity="medium"
        )
        
        # Extract score
        score_match = re.search(r'coherence[:\s]+(\d+)', assessment.lower())
        score = int(score_match.group(1)) if score_match else 80
        
        # Extract issues
        issues = []
        if "jump" in assessment.lower() or "disconnect" in assessment.lower():
            issues.append("Abrupt transitions between topics")
        if "inconsistent" in assessment.lower():
            issues.append("Inconsistent themes or messaging")
        
        return {
            "score": score,
            "assessment": assessment,
            "issues": issues
        }
    
    def _assess_completeness(self, content: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Assess content completeness"""
        score = 100
        issues = []
        
        # Check word count
        word_count = len(content.split())
        target_words = requirements.get("word_count", 1500)
        if abs(word_count - target_words) > 100:
            score -= 20
            issues.append(f"Word count {word_count} deviates from target {target_words}")
        
        # Check citations
        citation_count = content.count('[')
        min_citations = requirements.get("min_citations", 10)
        if citation_count < min_citations:
            score -= 15
            issues.append(f"Only {citation_count} citations, need {min_citations}")
        
        # Check for required sections
        required_sections = requirements.get("sections", [])
        for section in required_sections:
            if section.lower() not in content.lower():
                score -= 10
                issues.append(f"Missing required section: {section}")
        
        return {
            "score": max(0, score),
            "word_count": word_count,
            "citation_count": citation_count,
            "issues": issues
        }
    
    def _assess_engagement(self, content: str) -> Dict[str, Any]:
        """Assess content engagement level"""
        score = 80  # Base score
        issues = []
        
        # Check for engagement elements
        engagement_elements = {
            "questions": content.count('?'),
            "examples": len(re.findall(r'for example|such as|instance', content, re.I)),
            "data_points": len(re.findall(r'\d+\.?\d*\s*%', content)),
            "action_words": len(re.findall(r'consider|evaluate|implement|review|assess', content, re.I))
        }
        
        # Adjust score based on elements
        if engagement_elements["questions"] > 0:
            score += 5
        else:
            issues.append("No engaging questions")
        
        if engagement_elements["examples"] >= 3:
            score += 5
        else:
            issues.append("Insufficient examples")
        
        if engagement_elements["data_points"] >= 5:
            score += 5
        else:
            issues.append("Needs more data points")
        
        if engagement_elements["action_words"] >= 5:
            score += 5
        else:
            issues.append("Lacks actionable language")
        
        return {
            "score": min(100, score),
            "engagement_elements": engagement_elements,
            "issues": issues
        }
    
    def _assess_professionalism(self, content: str) -> Dict[str, Any]:
        """Assess professional tone and quality"""
        score = 100
        issues = []
        
        # Check for unprofessional elements
        informal_words = ['gonna', 'wanna', 'stuff', 'things', 'basically', 'actually', 'very']
        informal_count = sum(content.lower().count(word) for word in informal_words)
        
        if informal_count > 5:
            score -= 15
            issues.append(f"Too many informal words ({informal_count})")
        
        # Check for professional terminology
        professional_terms = [
            'strategic', 'institutional', 'portfolio', 'allocation',
            'analysis', 'framework', 'methodology', 'approach'
        ]
        prof_count = sum(content.lower().count(term) for term in professional_terms)
        
        if prof_count < 10:
            score -= 10
            issues.append("Lacks professional terminology")
        
        # Check for passive voice (simplified check)
        passive_indicators = ['was', 'were', 'been', 'being']
        passive_count = sum(content.lower().count(word) for word in passive_indicators)
        
        if passive_count > 20:
            score -= 5
            issues.append("Excessive passive voice")
        
        return {
            "score": max(0, score),
            "informal_words": informal_count,
            "professional_terms": prof_count,
            "issues": issues
        }
    
    def _assess_data_quality(self, content: str) -> Dict[str, Any]:
        """Assess quality of data presentation"""
        score = 80  # Base score
        issues = []
        
        # Count data elements
        statistics = len(re.findall(r'\d+\.?\d*\s*%', content))
        numbers = len(re.findall(r'\$?\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|trillion))?', content))
        
        # Check for data quality
        if statistics < 5:
            score -= 10
            issues.append("Insufficient statistical data")
        elif statistics > 15:
            score += 10
        
        if numbers < 3:
            score -= 10
            issues.append("Needs more concrete numbers")
        elif numbers > 10:
            score += 10
        
        # Check for data context
        data_with_context = len(re.findall(r'\d+.*(?:compared|versus|from|increased|decreased)', content))
        if data_with_context < statistics / 2:
            score -= 5
            issues.append("Data lacks comparative context")
        
        return {
            "score": min(100, max(0, score)),
            "statistics_count": statistics,
            "numbers_count": numbers,
            "contextualized_data": data_with_context,
            "issues": issues
        }
    
    def _assess_actionability(self, content: str) -> Dict[str, Any]:
        """Assess how actionable the content is"""
        score = 70  # Base score
        issues = []
        
        # Check for action-oriented language
        action_phrases = [
            'recommend', 'suggest', 'consider', 'evaluate',
            'implement', 'review', 'assess', 'analyze',
            'next steps', 'action items', 'key takeaway'
        ]
        
        action_count = sum(content.lower().count(phrase) for phrase in action_phrases)
        
        if action_count < 5:
            score -= 20
            issues.append("Lacks actionable recommendations")
        elif action_count >= 10:
            score += 20
        else:
            score += 10
        
        # Check for specific guidance
        guidance_phrases = ['should', 'could', 'may want to', 'advisable']
        guidance_count = sum(content.lower().count(phrase) for phrase in guidance_phrases)
        
        if guidance_count >= 5:
            score += 10
        else:
            issues.append("Needs more specific guidance")
        
        return {
            "score": min(100, max(0, score)),
            "action_phrases": action_count,
            "guidance_phrases": guidance_count,
            "issues": issues
        }
    
    def _calculate_quality_grade(self, score: float) -> str:
        """Calculate letter grade for quality"""
        if score >= 95:
            return "A+"
        elif score >= 90:
            return "A"
        elif score >= 85:
            return "B+"
        elif score >= 80:
            return "B"
        elif score >= 75:
            return "C+"
        elif score >= 70:
            return "C"
        else:
            return "D"
    
    def _generate_quality_recommendations(self, quality_checks: Dict[str, Dict]) -> List[str]:
        """Generate quality improvement recommendations"""
        recommendations = []
        
        # Sort checks by score (lowest first)
        sorted_checks = sorted(quality_checks.items(), key=lambda x: x[1]["score"])
        
        for check_name, check_result in sorted_checks[:3]:  # Focus on worst 3
            if check_result["score"] < 90:
                issues = check_result.get("issues", [])
                
                if check_name == "readability":
                    recommendations.append("Simplify complex sentences and reduce jargon")
                elif check_name == "structure":
                    recommendations.append("Add clear section headers and improve organization")
                elif check_name == "coherence":
                    recommendations.append("Improve transitions between sections")
                elif check_name == "engagement":
                    recommendations.append("Add more examples and actionable insights")
                elif check_name == "data_quality":
                    recommendations.append("Include more statistics with context")
                
                # Add specific issues
                for issue in issues[:1]:  # Top issue
                    recommendations.append(f"Fix: {issue}")
        
        return recommendations[:5]
    
    def _calculate_readability_metrics(self, content: str) -> Dict[str, float]:
        """Calculate detailed readability metrics"""
        words = content.split()
        sentences = [s.strip() for s in re.split(r'[.!?]+', content) if s.strip()]
        
        # Basic metrics
        word_count = len(words)
        sentence_count = len(sentences)
        
        # Average sentence length
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        # Count syllables (simplified)
        syllable_count = 0
        complex_words = 0
        for word in words:
            syllables = max(1, len(re.findall(r'[aeiouAEIOU]', word)))
            syllable_count += syllables
            if syllables >= 3:
                complex_words += 1
        
        # Flesch Reading Ease
        if sentence_count > 0 and word_count > 0:
            flesch_score = 206.835 - 1.015 * avg_sentence_length - 84.6 * (syllable_count / word_count)
        else:
            flesch_score = 0
        
        # Grade level
        grade_level = 0.39 * avg_sentence_length + 11.8 * (syllable_count / max(word_count, 1)) - 15.59
        
        return {
            "flesch_score": max(0, min(100, flesch_score)),
            "grade_level": max(0, grade_level),
            "avg_sentence_length": avg_sentence_length,
            "complex_word_percentage": (complex_words / max(word_count, 1)) * 100,
            "word_count": word_count,
            "sentence_count": sentence_count
        }
    
    def _assess_audience_appropriateness(self, metrics: Dict[str, float], audience: str) -> bool:
        """Assess if readability is appropriate for audience"""
        if audience == "institutional investors":
            # Professional audience - moderate complexity acceptable
            return 30 <= metrics["flesch_score"] <= 50 and 12 <= metrics["grade_level"] <= 16
        else:
            # General professional audience
            return 40 <= metrics["flesch_score"] <= 60 and 10 <= metrics["grade_level"] <= 14
    
    def _identify_complex_sections(self, content: str) -> List[Dict[str, Any]]:
        """Identify sections that are too complex"""
        paragraphs = content.split('\n\n')
        complex_sections = []
        
        for i, para in enumerate(paragraphs):
            if len(para.split()) < 20:  # Skip short paragraphs
                continue
            
            metrics = self._calculate_readability_metrics(para)
            
            if metrics["flesch_score"] < 20 or metrics["avg_sentence_length"] > 30:
                complex_sections.append({
                    "paragraph": i + 1,
                    "preview": para[:100] + "...",
                    "flesch_score": metrics["flesch_score"],
                    "avg_sentence_length": metrics["avg_sentence_length"],
                    "issue": "Very complex - simplify language and shorten sentences"
                })
        
        return complex_sections[:3]  # Top 3 complex sections
    
    def _generate_readability_recommendations(self, metrics: Dict[str, float], 
                                           complex_sections: List[Dict]) -> List[str]:
        """Generate readability recommendations"""
        recommendations = []
        
        if metrics["flesch_score"] < 30:
            recommendations.append("Simplify language - target 30-50 Flesch score for professional content")
        
        if metrics["avg_sentence_length"] > 20:
            recommendations.append(f"Reduce average sentence length from {metrics['avg_sentence_length']:.1f} to 15-20 words")
        
        if metrics["complex_word_percentage"] > 20:
            recommendations.append("Replace complex terms with simpler alternatives where possible")
        
        if complex_sections:
            recommendations.append(f"Revise {len(complex_sections)} particularly complex sections")
        
        return recommendations
    
    def _analyze_transitions(self, content: str) -> Dict[str, Any]:
        """Analyze paragraph transitions"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        transition_words = [
            'however', 'therefore', 'furthermore', 'additionally',
            'moreover', 'consequently', 'nevertheless', 'similarly',
            'in contrast', 'on the other hand', 'as a result'
        ]
        
        transitions_found = 0
        for i in range(1, len(paragraphs)):
            para_start = paragraphs[i][:200].lower()
            if any(word in para_start for word in transition_words):
                transitions_found += 1
        
        transition_ratio = transitions_found / max(len(paragraphs) - 1, 1)
        score = min(100, transition_ratio * 150)  # 67% transitions = 100 score
        
        return {
            "score": score,
            "transitions_found": transitions_found,
            "total_transitions_needed": len(paragraphs) - 1,
            "transition_ratio": transition_ratio
        }
    
    def _analyze_logical_flow(self, content: str) -> Dict[str, Any]:
        """Analyze logical flow of content"""
        flow_prompt = f"""Analyze the logical flow of this content:

{content[:2000]}...

Rate flow (0-100) based on:
1. Clear progression of ideas
2. Each section builds on previous
3. No unexplained jumps
4. Consistent narrative thread

Identify any flow issues."""

        analysis = self.query_llm(
            flow_prompt,
            reasoning_effort="medium",
            verbosity="medium"
        )
        
        # Extract score
        score_match = re.search(r'flow[:\s]+(\d+)', analysis.lower())
        score = int(score_match.group(1)) if score_match else 75
        
        return {
            "score": score,
            "analysis": analysis
        }
    
    def _analyze_theme_consistency(self, content: str) -> Dict[str, Any]:
        """Analyze theme consistency throughout content"""
        # Extract main themes from beginning
        intro = content[:1000]
        
        theme_prompt = f"""Identify main themes in this introduction:
{intro}

Then check if these themes are consistently maintained throughout."""

        theme_analysis = self.query_llm(
            theme_prompt,
            reasoning_effort="medium",
            verbosity="low"
        )
        
        # Simple consistency check
        score = 85  # Base score
        
        # Check for Dakota mentions throughout
        dakota_mentions = content.lower().count('dakota')
        if dakota_mentions < 3:
            score -= 10
        
        # Check for consistent terminology
        if "private equity" in content and "PE" in content:
            # Both full and abbreviated forms used - good
            score += 5
        
        return {
            "score": min(100, score),
            "analysis": theme_analysis,
            "dakota_integration": dakota_mentions
        }
    
    def _generate_coherence_suggestions(self, transitions: Dict, flow: Dict, themes: Dict) -> List[str]:
        """Generate coherence improvement suggestions"""
        suggestions = []
        
        if transitions["score"] < 80:
            suggestions.append("Add transition phrases between paragraphs to improve flow")
        
        if flow["score"] < 80:
            suggestions.append("Reorganize sections for better logical progression")
        
        if themes["score"] < 80:
            suggestions.append("Maintain consistent themes throughout the article")
        
        if themes["dakota_integration"] < 3:
            suggestions.append("Integrate Dakota perspective more consistently")
        
        return suggestions
    
    def _check_word_count(self, content: str, target: int) -> Dict[str, Any]:
        """Check word count requirement"""
        actual = len(content.split())
        tolerance = 50
        
        return {
            "complete": abs(actual - target) <= tolerance,
            "actual": actual,
            "target": target,
            "difference": actual - target
        }
    
    def _check_required_sections(self, content: str, required_sections: List[str]) -> Dict[str, Any]:
        """Check for required sections"""
        found_sections = []
        missing_sections = []
        
        content_lower = content.lower()
        for section in required_sections:
            if section.lower() in content_lower:
                found_sections.append(section)
            else:
                missing_sections.append(section)
        
        return {
            "complete": len(missing_sections) == 0,
            "found": found_sections,
            "missing": missing_sections
        }
    
    def _check_citation_requirements(self, content: str, min_citations: int) -> Dict[str, Any]:
        """Check citation requirements"""
        citation_count = content.count('[')
        
        return {
            "complete": citation_count >= min_citations,
            "actual": citation_count,
            "required": min_citations,
            "surplus": max(0, citation_count - min_citations)
        }
    
    def _check_key_points_coverage(self, content: str, key_points: List[str]) -> Dict[str, Any]:
        """Check coverage of key points"""
        covered = []
        missing = []
        
        content_lower = content.lower()
        for point in key_points:
            if point.lower() in content_lower:
                covered.append(point)
            else:
                missing.append(point)
        
        return {
            "complete": len(missing) == 0,
            "covered": covered,
            "missing": missing
        }
    
    def _check_dakota_perspective(self, content: str) -> Dict[str, Any]:
        """Check for Dakota perspective inclusion"""
        dakota_mentions = content.lower().count('dakota')
        has_perspective = dakota_mentions >= 3
        
        return {
            "complete": has_perspective,
            "mentions": dakota_mentions,
            "has_perspective": has_perspective
        }
    
    def _identify_missing_elements(self, completeness_checks: Dict[str, Dict]) -> List[str]:
        """Identify missing elements from completeness checks"""
        missing = []
        
        for check_name, result in completeness_checks.items():
            if not result["complete"]:
                if check_name == "word_count":
                    diff = result["difference"]
                    if diff < 0:
                        missing.append(f"Add {abs(diff)} more words")
                    else:
                        missing.append(f"Reduce by {diff} words")
                elif check_name == "sections":
                    for section in result["missing"]:
                        missing.append(f"Add section: {section}")
                elif check_name == "citations":
                    needed = result["required"] - result["actual"]
                    missing.append(f"Add {needed} more citations")
                elif check_name == "key_points":
                    for point in result["missing"]:
                        missing.append(f"Cover key point: {point}")
                elif check_name == "dakota_perspective":
                    missing.append("Add more Dakota-specific insights")
        
        return missing
    
    def _assess_overall_content_quality(self, content: str, reports: Dict[str, Any]) -> float:
        """Assess overall content quality from multiple reports"""
        # Weight different aspects
        weights = {
            "readability": 0.2,
            "accuracy": 0.3,
            "completeness": 0.2,
            "engagement": 0.15,
            "structure": 0.15
        }
        
        scores = {
            "readability": reports.get("readability", {}).get("score", 80),
            "accuracy": reports.get("fact_check", {}).get("accuracy_score", 85),
            "completeness": reports.get("completeness", {}).get("score", 90),
            "engagement": 85,  # Default if not separately assessed
            "structure": 85    # Default if not separately assessed
        }
        
        weighted_score = sum(scores[aspect] * weights[aspect] for aspect in weights)
        
        return weighted_score
    
    def _generate_approval_report(self, criteria: Dict[str, float], 
                                 criteria_met: Dict[str, bool], 
                                 thresholds: Dict[str, float]) -> str:
        """Generate detailed approval report"""
        report_lines = ["# Quality Approval Report\n"]
        
        # Overall status
        if all(criteria_met.values()):
            report_lines.append("**STATUS: APPROVED** ✅\n")
        else:
            report_lines.append("**STATUS: NOT APPROVED** ❌\n")
        
        # Criteria breakdown
        report_lines.append("## Criteria Assessment:\n")
        
        for criterion, score in criteria.items():
            met = criteria_met[criterion]
            threshold = thresholds.get(criterion, 80)
            status = "✅" if met else "❌"
            
            report_lines.append(f"- **{criterion.replace('_', ' ').title()}**: {score:.1f}/100 (Required: {threshold}) {status}")
        
        # Failed criteria details
        failed = [c for c, met in criteria_met.items() if not met]
        if failed:
            report_lines.append("\n## Failed Criteria:")
            for criterion in failed:
                score = criteria[criterion]
                threshold = thresholds[criterion]
                deficit = threshold - score
                report_lines.append(f"- {criterion}: {deficit:.1f} points below threshold")
        
        return '\n'.join(report_lines)
    
    def _generate_approval_conditions(self, criteria_met: Dict[str, bool]) -> List[str]:
        """Generate conditions for approval"""
        conditions = []
        
        if not criteria_met.get("content_quality", True):
            conditions.append("Improve overall content quality through editing")
        
        if not criteria_met.get("technical_accuracy", True):
            conditions.append("Verify and correct all factual claims")
        
        if not criteria_met.get("compliance_status", True):
            conditions.append("Address all compliance issues immediately")
        
        if not criteria_met.get("readability_score", True):
            conditions.append("Simplify complex sections for better readability")
        
        if not criteria_met.get("completeness", True):
            conditions.append("Add missing required elements")
        
        return conditions if conditions else ["No conditions - ready for publication"]
    
    def _analyze_improvement_areas(self, content: str) -> List[Dict[str, Any]]:
        """Analyze specific areas for improvement"""
        improvement_areas = []
        
        # Check introduction strength
        intro = content[:500]
        if not any(word in intro.lower() for word in ['compelling', 'critical', 'essential', 'significant']):
            improvement_areas.append({
                "type": "introduction",
                "action": "Strengthen introduction with compelling hook",
                "impact": "Increase reader engagement",
                "priority": "high"
            })
        
        # Check data density
        data_density = len(re.findall(r'\d+', content)) / len(content.split())
        if data_density < 0.02:  # Less than 2% numbers
            improvement_areas.append({
                "type": "data",
                "action": "Add more specific data points and statistics",
                "impact": "Enhance credibility and authority",
                "priority": "high"
            })
        
        # Check conclusion strength
        conclusion = content[-500:]
        if not any(word in conclusion.lower() for word in ['action', 'implement', 'next step', 'recommend']):
            improvement_areas.append({
                "type": "conclusion",
                "action": "Add clear call-to-action in conclusion",
                "impact": "Improve article actionability",
                "priority": "medium"
            })
        
        # Check example usage
        example_count = content.lower().count('example') + content.lower().count('instance')
        if example_count < 3:
            improvement_areas.append({
                "type": "examples",
                "action": "Add concrete examples to illustrate key points",
                "impact": "Improve understanding and retention",
                "priority": "medium"
            })
        
        return improvement_areas
    
    def _generate_issue_suggestion(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Generate suggestion for specific issue"""
        issue_type = issue.get("type", "general")
        severity = issue.get("severity", "medium")
        
        suggestion = {
            "priority": "high" if severity == "high" else "medium",
            "suggestion": {
                "issue": issue.get("description", "Quality issue"),
                "action": self._get_action_for_issue(issue_type),
                "location": issue.get("location", "general")
            }
        }
        
        return suggestion
    
    def _get_action_for_issue(self, issue_type: str) -> str:
        """Get specific action for issue type"""
        actions = {
            "readability": "Simplify sentence structure and reduce jargon",
            "accuracy": "Verify claim with authoritative source",
            "structure": "Reorganize content with clear sections",
            "citation": "Add proper source attribution",
            "coherence": "Improve transition between ideas",
            "completeness": "Add missing required element"
        }
        
        return actions.get(issue_type, "Review and revise content")
    
    def _estimate_quality_improvement(self, suggestions: Dict[str, List]) -> float:
        """Estimate potential quality improvement from suggestions"""
        # Rough estimates of impact
        impact_scores = {
            "high_priority": 5,
            "medium_priority": 3,
            "low_priority": 1
        }
        
        total_impact = 0
        for priority, suggestion_list in suggestions.items():
            total_impact += len(suggestion_list) * impact_scores.get(priority, 1)
        
        # Assume each point of impact improves quality by 1%
        estimated_improvement = min(20, total_impact)  # Cap at 20%
        
        return estimated_improvement
    
    def _prioritize_implementation(self, suggestions: Dict[str, List]) -> List[str]:
        """Create prioritized implementation order"""
        implementation_order = []
        
        # High priority first
        for suggestion in suggestions.get("high_priority", []):
            if isinstance(suggestion, dict):
                implementation_order.append(suggestion.get("specific_action", str(suggestion)))
            else:
                implementation_order.append(str(suggestion))
        
        # Then medium priority
        for suggestion in suggestions.get("medium_priority", [])[:3]:  # Top 3
            if isinstance(suggestion, dict):
                implementation_order.append(suggestion.get("specific_action", str(suggestion)))
            else:
                implementation_order.append(str(suggestion))
        
        return implementation_order[:7]  # Return top 7 actions