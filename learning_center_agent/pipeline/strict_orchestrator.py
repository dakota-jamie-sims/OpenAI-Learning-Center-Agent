"""
Strict orchestrator with enhanced validation - Updated for Responses API
"""
import json
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from learning_center_agent.pipeline.base_orchestrator import BaseOrchestrator
from learning_center_agent.config import (
    DEFAULT_MODELS,
    MIN_WORD_COUNT,
    MIN_SOURCES,
    REQUIRE_DAKOTA_URLS,
)


class StrictOrchestrator(BaseOrchestrator):
    """Strict orchestrator with validation using Responses API"""
    
    def __init__(self):
        super().__init__()
        self.validation_results = []
        
    def generate_article(self, topic: str, word_count: int = 1500) -> Dict[str, Any]:
        """Generate article with strict validation"""
        
        print(f"\n🚀 Strict generation for: {topic}")
        print(f"📏 Requirements: {word_count} words, {MIN_SOURCES}+ sources")
        
        article_dir = self.create_output_directory(topic)
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        try:
            # Research phase
            print("\n📚 Research phase...")
            kb_insights = self._search_knowledge_base(topic)
            web_research = self._perform_web_research(topic)
            
            # Generation phase
            print("\n📝 Generation phase...")
            article_content = self._generate_validated_article(
                topic, word_count, kb_insights, web_research
            )
            
            # Validation phase
            print("\n🔍 Validation phase...")
            validation_results = self._validate_article(article_content)
            
            # If validation fails, attempt to fix
            if not validation_results["all_passed"]:
                print("📝 Fixing validation issues...")
                article_content = self._fix_validation_issues(
                    article_content, validation_results
                )
                # Re-validate
                validation_results = self._validate_article(article_content)
            
            # Save article
            article_path = article_dir / "article.md"
            article_path.write_text(article_content)
            print(f"✅ Article saved: {article_path}")
            
            # Generate supporting content
            print("\n📊 Generating supporting content...")
            summary = self._generate_summary(article_content, date_str)
            social = self._generate_social(article_content, topic, date_str)
            metadata = self._generate_metadata(
                article_content, topic, date_str, validation_results
            )
            
            # Save all files
            (article_dir / "summary.md").write_text(summary)
            (article_dir / "social.md").write_text(social)
            (article_dir / "metadata.md").write_text(metadata)
            (article_dir / "validation-report.json").write_text(
                json.dumps(validation_results, indent=2)
            )
            
            # Quality report
            quality_report = self._generate_quality_report(
                article_content, validation_results
            )
            (article_dir / "quality-report.md").write_text(quality_report)
            
            print(f"\n✨ Strict generation complete!")
            print(f"📁 Output directory: {article_dir}")
            
            return {
                "status": "success",
                "output_dir": str(article_dir),
                "files": {
                    "article": str(article_path),
                    "summary": str(article_dir / "summary.md"),
                    "social": str(article_dir / "social.md"),
                    "metadata": str(article_dir / "metadata.md"),
                    "validation_report": str(article_dir / "validation-report.json"),
                    "quality_report": str(article_dir / "quality-report.md")
                },
                "validation": validation_results,
                "quality_score": validation_results.get("quality_score", 0)
            }
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "output_dir": str(article_dir)
            }
    
    def _search_knowledge_base(self, topic: str) -> str:
        """Search knowledge base with validation"""
        return self.search_knowledge_base(topic, max_results=10)
    
    def _perform_web_research(self, topic: str) -> str:
        """Perform thorough web research"""
        prompt = f"""Research {topic} comprehensively:

Requirements:
- Find {MIN_SOURCES}+ authoritative sources
- Focus on 2024-2025 data
- Include institutional investor perspectives
- Verify all statistics
- Provide exact URLs for citations

Return detailed findings with source URLs."""

        return self.create_response(
            prompt,
            model=DEFAULT_MODELS["web_researcher"],
            reasoning_effort="high",
            verbosity="high"
        )
    
    def _generate_validated_article(
        self, topic: str, word_count: int, kb_insights: str, web_research: str
    ) -> str:
        """Generate article with strict requirements"""
        prompt = f"""Write a comprehensive article about: {topic}

Knowledge Base:
{kb_insights}

Research Findings:
{web_research}

STRICT REQUIREMENTS:
- EXACTLY {word_count} words (tolerance: ±50 words)
- MINIMUM {MIN_SOURCES} inline citations with real URLs
- Include at least 3 Dakota-specific URLs if required: {REQUIRE_DAKOTA_URLS}
- Professional tone for institutional investors
- Data-driven with specific statistics
- Clear structure with 5+ sections
- Actionable insights throughout

Format all citations as: [Source Name, Date](actual_url)"""

        return self.create_response(
            prompt,
            model=DEFAULT_MODELS["writer"],
            reasoning_effort="high",
            verbosity="high",
            max_tokens=5000
        )
    
    def _validate_article(self, article_content: str) -> Dict[str, Any]:
        """Comprehensive article validation"""
        validations = {
            "word_count": self._validate_word_count(article_content),
            "citations": self._validate_citations(article_content),
            "structure": self._validate_structure(article_content),
            "quality": self._validate_quality(article_content)
        }
        
        all_passed = all(v["passed"] for v in validations.values())
        quality_score = sum(v.get("score", 0) for v in validations.values()) / len(validations)
        
        return {
            "all_passed": all_passed,
            "quality_score": quality_score,
            "validations": validations,
            "timestamp": datetime.now().isoformat()
        }
    
    def _validate_word_count(self, content: str) -> Dict[str, Any]:
        """Validate word count requirement"""
        word_count = len(content.split())
        target = MIN_WORD_COUNT
        tolerance = 50
        
        passed = abs(word_count - target) <= tolerance
        
        return {
            "passed": passed,
            "actual": word_count,
            "target": target,
            "tolerance": tolerance,
            "score": 100 if passed else max(0, 100 - abs(word_count - target))
        }
    
    def _validate_citations(self, content: str) -> Dict[str, Any]:
        """Validate citation requirements"""
        import re
        
        # Find citations in format [Source, Date](URL)
        citation_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        citations = re.findall(citation_pattern, content)
        
        valid_urls = []
        dakota_urls = []
        
        for source, url in citations:
            if url.startswith('http'):
                valid_urls.append(url)
                if 'dakota' in url.lower():
                    dakota_urls.append(url)
        
        passed = len(valid_urls) >= MIN_SOURCES
        if REQUIRE_DAKOTA_URLS:
            passed = passed and len(dakota_urls) >= 3
        
        return {
            "passed": passed,
            "total_citations": len(citations),
            "valid_urls": len(valid_urls),
            "dakota_urls": len(dakota_urls),
            "required": MIN_SOURCES,
            "score": min(100, (len(valid_urls) / MIN_SOURCES) * 100)
        }
    
    def _validate_structure(self, content: str) -> Dict[str, Any]:
        """Validate article structure"""
        lines = content.split('\n')
        
        # Count headers
        h1_count = sum(1 for line in lines if line.startswith('# '))
        h2_count = sum(1 for line in lines if line.startswith('## '))
        h3_count = sum(1 for line in lines if line.startswith('### '))
        
        total_sections = h1_count + h2_count + h3_count
        passed = total_sections >= 5
        
        return {
            "passed": passed,
            "h1_sections": h1_count,
            "h2_sections": h2_count,
            "h3_sections": h3_count,
            "total_sections": total_sections,
            "required_sections": 5,
            "score": min(100, (total_sections / 5) * 100)
        }
    
    def _validate_quality(self, content: str) -> Dict[str, Any]:
        """Validate content quality using AI"""
        prompt = f"""Analyze this article's quality:

{content[:2000]}...

Rate on:
1. Professional tone (0-100)
2. Data richness (0-100)
3. Actionable insights (0-100)
4. Clarity (0-100)

Return JSON with scores and overall quality_score."""

        response = self.create_response(
            prompt,
            model=DEFAULT_MODELS["metrics"],
            reasoning_effort="medium",
            verbosity="low"
        )
        
        scores = self.parse_json_response(response)
        quality_score = scores.get("quality_score", 75)
        
        return {
            "passed": quality_score >= 70,
            "quality_score": quality_score,
            "scores": scores,
            "score": quality_score
        }
    
    def _fix_validation_issues(
        self, content: str, validation_results: Dict[str, Any]
    ) -> str:
        """Attempt to fix validation issues"""
        issues = []
        
        validations = validation_results["validations"]
        
        if not validations["word_count"]["passed"]:
            actual = validations["word_count"]["actual"]
            target = validations["word_count"]["target"]
            issues.append(f"Word count is {actual}, need exactly {target}")
        
        if not validations["citations"]["passed"]:
            actual = validations["citations"]["valid_urls"]
            required = validations["citations"]["required"]
            issues.append(f"Only {actual} valid citations, need {required}+")
        
        if not issues:
            return content
        
        fix_prompt = f"""Fix these issues in the article:

Issues:
{chr(10).join(f"- {issue}" for issue in issues)}

Article:
{content}

Return the corrected article maintaining all existing content and structure."""

        return self.create_response(
            fix_prompt,
            model=DEFAULT_MODELS["writer"],
            reasoning_effort="medium",
            verbosity="high",
            max_tokens=5000
        )
    
    def _generate_summary(self, content: str, date_str: str) -> str:
        """Generate executive summary"""
        prompt = f"""Create an executive summary:

{content[:3000]}...

Focus on:
- Key statistics and findings
- Actionable recommendations
- Investment implications
- Risk factors

Keep under 300 words."""

        summary = self.create_response(
            prompt,
            model=DEFAULT_MODELS["summary"],
            reasoning_effort="low",
            verbosity="medium"
        )
        
        return f"""---
title: Executive Summary
date: {date_str}
type: strict_validation
---

{summary}"""
    
    def _generate_social(self, content: str, topic: str, date_str: str) -> str:
        """Generate social media content"""
        prompt = f"""Create social media content for: {topic}

Article excerpt:
{content[:2000]}...

Generate:
1. LinkedIn post (300 words, professional tone)
2. Twitter thread (5-7 tweets with statistics)
3. Email snippet (150 words, action-oriented)

Include specific data points."""

        social = self.create_response(
            prompt,
            model=DEFAULT_MODELS["social"],
            reasoning_effort="minimal",
            verbosity="medium"
        )
        
        return f"""---
title: Social Media Content
date: {date_str}
topic: {topic}
---

{social}"""
    
    def _generate_metadata(
        self, content: str, topic: str, date_str: str, validation_results: Dict
    ) -> str:
        """Generate enhanced metadata"""
        prompt = f"""Generate comprehensive metadata for: {topic}

Article excerpt:
{content[:1500]}...

Create JSON with:
- title (SEO-optimized)
- description (150-160 chars)
- keywords (8-10 relevant terms)
- categories (2-3)
- tags (5-8)
- reading_time
- difficulty_level
- target_audience"""

        metadata = self.create_response(
            prompt,
            model=DEFAULT_MODELS["metrics"],
            reasoning_effort="minimal",
            verbosity="low"
        )
        
        metadata_dict = self.parse_json_response(metadata)
        metadata_dict["validation_status"] = "passed" if validation_results["all_passed"] else "failed"
        metadata_dict["quality_score"] = validation_results["quality_score"]
        
        return f"""---
title: Article Metadata
date: {date_str}
generated_at: {datetime.now().isoformat()}
---

{json.dumps(metadata_dict, indent=2)}"""
    
    def _generate_quality_report(
        self, content: str, validation_results: Dict
    ) -> str:
        """Generate comprehensive quality report"""
        validations = validation_results["validations"]
        
        report = f"""---
title: Quality Assurance Report
date: {datetime.now().strftime("%Y-%m-%d")}
overall_score: {validation_results["quality_score"]:.1f}/100
status: {"PASSED" if validation_results["all_passed"] else "NEEDS REVIEW"}
---

# Quality Assurance Report

## Overall Results
- **Status**: {"✅ PASSED" if validation_results["all_passed"] else "⚠️ NEEDS REVIEW"}
- **Quality Score**: {validation_results["quality_score"]:.1f}/100
- **Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Validation Results

### Word Count
- **Status**: {"✅ Passed" if validations["word_count"]["passed"] else "❌ Failed"}
- **Actual**: {validations["word_count"]["actual"]} words
- **Target**: {validations["word_count"]["target"]} words (±{validations["word_count"]["tolerance"]})
- **Score**: {validations["word_count"]["score"]}/100

### Citations
- **Status**: {"✅ Passed" if validations["citations"]["passed"] else "❌ Failed"}
- **Total Citations**: {validations["citations"]["total_citations"]}
- **Valid URLs**: {validations["citations"]["valid_urls"]}
- **Dakota URLs**: {validations["citations"]["dakota_urls"]}
- **Required**: {validations["citations"]["required"]}+ citations
- **Score**: {validations["citations"]["score"]}/100

### Structure
- **Status**: {"✅ Passed" if validations["structure"]["passed"] else "❌ Failed"}
- **H1 Sections**: {validations["structure"]["h1_sections"]}
- **H2 Sections**: {validations["structure"]["h2_sections"]}
- **H3 Sections**: {validations["structure"]["h3_sections"]}
- **Total Sections**: {validations["structure"]["total_sections"]}
- **Required**: {validations["structure"]["required_sections"]}+ sections
- **Score**: {validations["structure"]["score"]}/100

### Content Quality
- **Status**: {"✅ Passed" if validations["quality"]["passed"] else "❌ Failed"}
- **Quality Score**: {validations["quality"]["quality_score"]}/100
- **Details**: {json.dumps(validations["quality"].get("scores", {}), indent=2)}

## Recommendations
"""
        
        if not validation_results["all_passed"]:
            report += "\n### Areas for Improvement\n"
            
            if not validations["word_count"]["passed"]:
                report += "- Adjust word count to meet target requirement\n"
            
            if not validations["citations"]["passed"]:
                report += "- Add more authoritative sources with valid URLs\n"
                if REQUIRE_DAKOTA_URLS and validations["citations"]["dakota_urls"] < 3:
                    report += "- Include more Dakota-specific resources\n"
            
            if not validations["structure"]["passed"]:
                report += "- Add more section headers for better organization\n"
            
            if not validations["quality"]["passed"]:
                report += "- Enhance content quality with more data and insights\n"
        else:
            report += "\nAll validation criteria met. Article meets strict quality standards."
        
        return report