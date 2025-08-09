from openai import OpenAI
from typing import Optional, Dict, Any, List
import re
from pathlib import Path

class ReviewerAgent:
    """Agent responsible for reviewing, fact-checking, and analyzing article quality"""
    
    def __init__(self, client: OpenAI, model: str = "gpt-4"):
        self.client = client
        self.model = model
        self.name = "reviewer_agent"
        
        # Load prompts
        prompts_dir = Path(__file__).parent.parent / "prompts"
        self.fact_checker_prompt = self._load_prompt(prompts_dir / "dakota-fact-checker.md")
        self.claim_checker_prompt = self._load_prompt(prompts_dir / "dakota-claim-checker.md")
        self.metrics_prompt = self._load_prompt(prompts_dir / "dakota-metrics-analyzer.md")
        
        # Use default prompts if files don't exist
        if not self.fact_checker_prompt:
            self.fact_checker_prompt = self._get_default_fact_checker_prompt()
        if not self.claim_checker_prompt:
            self.claim_checker_prompt = self._get_default_claim_checker_prompt()
        if not self.metrics_prompt:
            self.metrics_prompt = self._get_default_metrics_prompt()
    
    def _load_prompt(self, path: Path) -> str:
        """Load prompt from file"""
        if path.exists():
            with open(path, 'r') as f:
                return f.read()
        return ""
    
    def _get_default_fact_checker_prompt(self) -> str:
        return """You are a meticulous fact-checker for Dakota's Learning Center.
        Verify all claims, statistics, and sources in articles.
        Ensure accuracy and credibility of all content."""
    
    def _get_default_claim_checker_prompt(self) -> str:
        return """You are an expert claim verifier for Dakota's Learning Center.
        Identify and verify all factual claims made in articles.
        Flag any unsupported or questionable statements."""
    
    def _get_default_metrics_prompt(self) -> str:
        return """You are a content quality analyst for Dakota's Learning Center.
        Analyze articles for readability, engagement, and alignment with Dakota's standards.
        Provide actionable feedback for improvement."""
    
    def review_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive review of an article"""
        article_content = article.get('article', '')
        
        # Perform different types of reviews
        fact_check = self.fact_check(article_content)
        claim_check = self.check_claims(article_content)
        metrics = self.analyze_metrics(article_content)
        
        # Compile overall review
        review_summary = self._compile_review(fact_check, claim_check, metrics)
        
        return {
            "article_topic": article.get('topic', 'Unknown'),
            "fact_check": fact_check,
            "claim_check": claim_check,
            "metrics_analysis": metrics,
            "review_summary": review_summary,
            "approval_status": review_summary['approved'],
            "required_revisions": review_summary['revisions'],
            "status": "success"
        }
    
    def fact_check(self, content: str) -> Dict[str, Any]:
        """Check facts and verify sources"""
        # Extract all claims with sources
        sourced_claims = re.findall(r'([^.]+\[[^\]]+\]\([^)]+\)[^.]*\.)', content)
        
        # Extract statistics and numbers
        statistics = re.findall(r'(\d+(?:\.\d+)?%|\$[\d,]+(?:\.\d+)?(?:\s*(?:billion|million|thousand))?|\d+(?:,\d+)*(?:\s*(?:billion|million|thousand))?)', content)
        
        prompt = f"""Review the following article content for factual accuracy:

{content}

Please verify:
1. Are all statistics properly sourced?
2. Are the sources credible and current?
3. Are there any unsupported claims?
4. Do the facts align with known financial/investment data?

Provide a detailed fact-check report."""

        messages = [
            {"role": "system", "content": self.fact_checker_prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3
            )
            
            return {
                "sourced_claims_count": len(sourced_claims),
                "statistics_found": len(statistics),
                "fact_check_report": response.choices[0].message.content,
                "status": "completed"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def check_claims(self, content: str) -> Dict[str, Any]:
        """Verify all claims made in the article"""
        prompt = f"""Identify and verify all claims in this article:

{content}

For each claim:
1. Is it properly supported?
2. Is it accurate and verifiable?
3. Does it align with Dakota's educational standards?
4. Are there any potentially misleading statements?

Provide a detailed claim analysis."""

        messages = [
            {"role": "system", "content": self.claim_checker_prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3
            )
            
            return {
                "claim_analysis": response.choices[0].message.content,
                "status": "completed"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def analyze_metrics(self, content: str) -> Dict[str, Any]:
        """Analyze article metrics and quality"""
        word_count = len(content.split())
        
        # Count sections
        sections = re.findall(r'^##\s+(.+)$', content, re.MULTILINE)
        
        # Check for required sections
        has_key_insights = "Key Insights at a Glance" in content
        has_key_takeaways = "Key Takeaways" in content
        has_conclusion = "Conclusion" in content or "## Conclusion" in content
        
        # Count sources
        sources = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        
        prompt = f"""Analyze this article for quality metrics:

Word Count: {word_count}
Sections: {len(sections)}
Sources: {len(sources)}

Article Content:
{content[:2000]}... [truncated]

Please evaluate:
1. Readability and flow
2. Engagement and value for institutional investors
3. Alignment with Dakota's brand voice
4. Structure and organization
5. Actionability of insights

Provide a comprehensive quality analysis."""

        messages = [
            {"role": "system", "content": self.metrics_prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.5
            )
            
            return {
                "word_count": word_count,
                "section_count": len(sections),
                "source_count": len(sources),
                "has_required_sections": {
                    "key_insights": has_key_insights,
                    "key_takeaways": has_key_takeaways,
                    "conclusion": has_conclusion
                },
                "quality_analysis": response.choices[0].message.content,
                "status": "completed"
            }
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def _compile_review(self, fact_check: Dict[str, Any], claim_check: Dict[str, Any], 
                       metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Compile all review results into a summary"""
        issues = []
        
        # Check word count
        if metrics.get('word_count', 0) < 1750:
            issues.append(f"Article is too short ({metrics.get('word_count', 0)} words, minimum 1750 required)")
        
        # Check sources
        if metrics.get('source_count', 0) < 10:
            issues.append(f"Insufficient sources ({metrics.get('source_count', 0)}, minimum 10 required)")
        
        # Check required sections
        required_sections = metrics.get('has_required_sections', {})
        for section, present in required_sections.items():
            if not present:
                issues.append(f"Missing required section: {section.replace('_', ' ').title()}")
        
        # Determine approval status
        approved = len(issues) == 0
        
        return {
            "approved": approved,
            "issues": issues,
            "revisions": issues,
            "fact_check_summary": fact_check.get('fact_check_report', 'N/A')[:500] + "...",
            "claim_check_summary": claim_check.get('claim_analysis', 'N/A')[:500] + "...",
            "quality_summary": metrics.get('quality_analysis', 'N/A')[:500] + "..."
        }
    
    def suggest_improvements(self, article: Dict[str, Any], review_results: Dict[str, Any]) -> List[str]:
        """Generate specific improvement suggestions based on review"""
        suggestions = []
        
        # Based on issues found
        for issue in review_results.get('required_revisions', []):
            if 'too short' in issue:
                suggestions.append("Expand key sections with more detail and examples")
            elif 'sources' in issue:
                suggestions.append("Add more credible sources with inline citations")
            elif 'Missing required section' in issue:
                suggestions.append(f"Add the {issue.split(':')[1].strip()} section")
        
        # Additional suggestions based on quality analysis
        if 'readability' in review_results.get('quality_summary', '').lower():
            suggestions.append("Improve readability with clearer transitions and simpler explanations")
        
        if 'engagement' in review_results.get('quality_summary', '').lower():
            suggestions.append("Add more engaging examples and case studies")
        
        return suggestions