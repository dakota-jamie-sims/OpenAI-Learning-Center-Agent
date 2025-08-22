"""Dakota Metrics Analyzer Agent - Analyzes article quality metrics"""

import re
from typing import Dict, Any, List

from .base_agent import DakotaBaseAgent
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DakotaMetricsAnalyzer(DakotaBaseAgent):
    """Analyzes articles for objective quality metrics"""
    
    def __init__(self):
        super().__init__("metrics_analyzer", model_override="gpt-5-mini")
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze article for quality metrics"""
        try:
            self.update_status("active", "Analyzing article metrics")
            
            article_file = task.get("article_file", "")
            target_word_count = task.get("target_word_count", 1750)
            
            # Read article
            with open(article_file, 'r') as f:
                content = f.read()
            
            # Skip frontmatter
            article_body = self._extract_body(content)
            
            # Analyze metrics
            metrics = {
                "word_count": len(article_body.split()),
                "sections": self._count_sections(article_body),
                "key_insights": self._count_key_insights(article_body),
                "inline_citations": self._count_citations(article_body),
                "actionable_items": self._count_actionable_items(article_body),
                "examples_provided": self._count_examples(article_body),
                "statistics_used": self._count_statistics(article_body),
                "headers": self._analyze_headers(article_body),
                "readability": self._assess_readability(article_body)
            }
            
            # Check requirements
            requirements_met = self._check_requirements(metrics, target_word_count)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(metrics, target_word_count)
            
            return self.format_response(True, data={
                **metrics,
                "target_word_count": target_word_count,
                "requirements_met": requirements_met,
                "recommendations": recommendations,
                "quality_score": self._calculate_quality_score(metrics, requirements_met)
            })
            
        except Exception as e:
            self.logger.error(f"Metrics analysis error: {e}")
            return self.format_response(False, error=str(e))
    
    def _extract_body(self, content: str) -> str:
        """Extract article body without frontmatter"""
        if content.startswith("---"):
            # Find end of frontmatter
            end_index = content.find("---", 3)
            if end_index > 0:
                return content[end_index + 3:].strip()
        return content
    
    def _count_sections(self, content: str) -> int:
        """Count main sections (## headers)"""
        return len(re.findall(r'^##\s+[^#]', content, re.MULTILINE))
    
    def _count_key_insights(self, content: str) -> int:
        """Count key insights in the Key Insights section"""
        insights_section = re.search(
            r'##\s*Key\s+Insights.*?(?=##|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )
        
        if insights_section:
            # Count bullet points
            bullets = re.findall(r'^\s*[-•*]\s+', insights_section.group(0), re.MULTILINE)
            return len(bullets)
        return 0
    
    def _count_citations(self, content: str) -> int:
        """Count inline citations"""
        # Look for patterns like (Source, Date) or (Source Name, 2024)
        citation_patterns = [
            r'\([^)]+,\s*\d{4}\)',  # (Source, 2024)
            r'According to [^,]+,',  # According to Source,
            r'[^.]+report(?:s|ed) that',  # X reports that
            r'[^.]+survey(?:s|ed)',  # X surveyed
        ]
        
        total_citations = 0
        for pattern in citation_patterns:
            total_citations += len(re.findall(pattern, content))
        
        return total_citations
    
    def _count_actionable_items(self, content: str) -> int:
        """Count actionable items in Key Takeaways"""
        takeaways_section = re.search(
            r'##\s*Key\s+Takeaways.*?(?=##|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )
        
        if takeaways_section:
            bullets = re.findall(r'^\s*[-•*]\s+', takeaways_section.group(0), re.MULTILINE)
            return len(bullets)
        return 0
    
    def _count_examples(self, content: str) -> int:
        """Count examples and case studies"""
        example_keywords = [
            r'for example',
            r'for instance',
            r'such as',
            r'including',
            r'case study',
            r'consider',
            r'take the case'
        ]
        
        total = 0
        for keyword in example_keywords:
            total += len(re.findall(keyword, content, re.IGNORECASE))
        
        return min(total, 10)  # Cap at 10
    
    def _count_statistics(self, content: str) -> int:
        """Count statistics and data points"""
        stat_patterns = [
            r'\d+(?:\.\d+)?%',  # Percentages
            r'\$[\d,]+(?:\.\d+)?\s*(?:billion|million|trillion)?',  # Dollar amounts
            r'\b\d{1,3}(?:,\d{3})*\b',  # Large numbers with commas
            r'\b\d+x\b',  # Multipliers (5x, 10x)
        ]
        
        total = 0
        for pattern in stat_patterns:
            total += len(re.findall(pattern, content))
        
        return total
    
    def _analyze_headers(self, content: str) -> Dict[str, Any]:
        """Analyze header structure"""
        h1_count = len(re.findall(r'^#\s+[^#]', content, re.MULTILINE))
        h2_count = len(re.findall(r'^##\s+[^#]', content, re.MULTILINE))
        h3_count = len(re.findall(r'^###\s+[^#]', content, re.MULTILINE))
        
        return {
            "h1_count": h1_count,
            "h2_count": h2_count,
            "h3_count": h3_count,
            "hierarchy_valid": h1_count == 1 and h2_count > 3
        }
    
    def _assess_readability(self, content: str) -> Dict[str, Any]:
        """Basic readability assessment"""
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        words_per_sentence = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        # Check paragraph length
        paragraphs = content.split('\n\n')
        avg_paragraph_length = sum(len(p.split()) for p in paragraphs) / len(paragraphs) if paragraphs else 0
        
        return {
            "avg_words_per_sentence": round(words_per_sentence, 1),
            "avg_paragraph_length": round(avg_paragraph_length, 1),
            "readability_score": "Good" if 15 <= words_per_sentence <= 25 else "Needs improvement"
        }
    
    def _check_requirements(self, metrics: Dict[str, Any], target_word_count: int) -> Dict[str, bool]:
        """Check if article meets requirements"""
        return {
            "word_count_met": metrics["word_count"] >= target_word_count * 0.9,  # 90% of target
            "key_insights_met": metrics["key_insights"] >= 4,
            "sections_complete": metrics["sections"] >= 4,
            "citations_met": metrics["inline_citations"] >= 10,
            "actionable_items_met": metrics["actionable_items"] >= 3,
            "examples_met": metrics["examples_provided"] >= 3,
            "header_hierarchy_valid": metrics["headers"]["hierarchy_valid"]
        }
    
    def _generate_recommendations(self, metrics: Dict[str, Any], target_word_count: int) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if metrics["word_count"] < target_word_count * 0.9:
            recommendations.append(f"Expand content by {target_word_count - metrics['word_count']} words")
        
        if metrics["key_insights"] < 4:
            recommendations.append(f"Add {4 - metrics['key_insights']} more key insights")
        
        if metrics["inline_citations"] < 10:
            recommendations.append(f"Add {10 - metrics['inline_citations']} more inline citations")
        
        if metrics["examples_provided"] < 3:
            recommendations.append("Include more specific examples or case studies")
        
        if metrics["statistics_used"] < 10:
            recommendations.append("Add more specific data points and statistics")
        
        return recommendations
    
    def _calculate_quality_score(self, metrics: Dict[str, Any], requirements: Dict[str, bool]) -> int:
        """Calculate overall quality score"""
        # Base score from requirements met
        requirements_score = sum(requirements.values()) / len(requirements) * 50
        
        # Bonus points for exceeding minimums
        bonus_score = 0
        if metrics["inline_citations"] > 15:
            bonus_score += 10
        if metrics["statistics_used"] > 20:
            bonus_score += 10
        if metrics["examples_provided"] > 5:
            bonus_score += 10
        if metrics["word_count"] > 2000:
            bonus_score += 10
        if metrics["readability"]["readability_score"] == "Good":
            bonus_score += 10
        
        return min(100, int(requirements_score + bonus_score))