"""
Enhanced orchestrator with async support - Updated for Responses API
"""
import asyncio
import json
from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path

from src.pipeline.base_orchestrator import BaseOrchestrator
from src.config import DEFAULT_MODELS


class EnhancedOrchestrator(BaseOrchestrator):
    """Enhanced orchestrator with parallel processing using Responses API"""
    
    def __init__(self):
        super().__init__()
        self.token_usage = {}
        self.total_cost = 0.0
        
    async def generate_article(self, topic: str, word_count: int = 1500) -> Dict[str, Any]:
        """Generate article with parallel processing"""
        
        print(f"\n🚀 Enhanced generation for: {topic}")
        article_dir = self.create_output_directory(topic)
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        try:
            # Parallel knowledge gathering
            print("\n📚 Gathering information (parallel)...")
            kb_task = asyncio.create_task(self._gather_knowledge_base(topic))
            web_task = asyncio.create_task(self._gather_web_research(topic))
            
            kb_insights, web_results = await asyncio.gather(kb_task, web_task)
            print("✅ Information gathering complete")
            
            # Generate main article
            print("\n📝 Writing article...")
            article_content = await self._generate_main_article(
                topic, word_count, kb_insights, web_results
            )
            
            article_path = article_dir / "article.md"
            article_path.write_text(article_content)
            print("✅ Article saved")
            
            # Parallel supporting content generation
            print("\n📊 Generating supporting content (parallel)...")
            summary_task = asyncio.create_task(
                self._generate_summary_async(article_content, date_str)
            )
            social_task = asyncio.create_task(
                self._generate_social_async(article_content, topic, date_str)
            )
            metadata_task = asyncio.create_task(
                self._generate_metadata_async(article_content, topic, date_str)
            )
            fact_check_task = asyncio.create_task(
                self._fact_check_async(article_content)
            )
            
            results = await asyncio.gather(
                summary_task, social_task, metadata_task, fact_check_task
            )
            
            summary_content, social_content, metadata_content, fact_check_result = results
            
            # Save all content
            (article_dir / "summary.md").write_text(summary_content)
            (article_dir / "social.md").write_text(social_content)
            (article_dir / "metadata.md").write_text(metadata_content)
            (article_dir / "fact-check.json").write_text(json.dumps(fact_check_result, indent=2))
            
            print("✅ All supporting content generated")
            
            # Generate usage report
            usage_report = self._generate_usage_report()
            (article_dir / "usage-report.md").write_text(usage_report)
            
            print(f"\n✨ Enhanced generation complete!")
            print(f"📁 Output directory: {article_dir}")
            
            return {
                "status": "success",
                "output_dir": str(article_dir),
                "files": {
                    "article": str(article_path),
                    "summary": str(article_dir / "summary.md"),
                    "social": str(article_dir / "social.md"),
                    "metadata": str(article_dir / "metadata.md"),
                    "fact_check": str(article_dir / "fact-check.json"),
                    "usage_report": str(article_dir / "usage-report.md")
                },
                "fact_check": fact_check_result,
                "token_usage": self.token_usage,
                "estimated_cost": self.total_cost
            }
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "output_dir": str(article_dir)
            }
    
    async def _gather_knowledge_base(self, topic: str) -> str:
        """Gather knowledge base insights asynchronously"""
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.search_knowledge_base(topic, max_results=10)
        )
        return result
    
    async def _gather_web_research(self, topic: str) -> str:
        """Gather web research asynchronously"""
        prompt = f"""Research current information about: {topic}
Focus on:
- 2024-2025 statistics and trends
- Institutional investor perspectives
- Market data and analysis
- Recent developments

Provide specific data points with source citations."""
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.create_response(
                prompt,
                model=DEFAULT_MODELS["web_researcher"],
                reasoning_effort="medium",
                verbosity="high"
            )
        )
        
        return result
    
    async def _generate_main_article(
        self, topic: str, word_count: int, kb_insights: str, web_results: str
    ) -> str:
        """Generate the main article content"""
        prompt = f"""Write a comprehensive article about: {topic}

Knowledge Base Insights:
{kb_insights}

Current Research:
{web_results}

Requirements:
- Exactly {word_count} words
- Professional tone for institutional investors
- Include 10+ inline citations
- Data-driven insights
- Clear structure with sections
- Actionable recommendations"""
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.create_response(
                prompt,
                model=DEFAULT_MODELS["writer"],
                reasoning_effort="medium",
                verbosity="high",
                max_tokens=4000
            )
        )
        
        return result
    
    async def _generate_summary_async(self, article_content: str, date_str: str) -> str:
        """Generate summary asynchronously"""
        prompt = f"""Create an executive summary:

{article_content[:3000]}...

Requirements:
- Key statistics and findings
- Actionable insights
- Under 300 words
- Bullet points for clarity"""
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.create_response(
                prompt,
                model=DEFAULT_MODELS["summary"],
                reasoning_effort="low",
                verbosity="medium"
            )
        )
        
        return f"""---
title: Executive Summary
date: {date_str}
---

{result}"""
    
    async def _generate_social_async(self, article_content: str, topic: str, date_str: str) -> str:
        """Generate social content asynchronously"""
        prompt = f"""Create social media content for: {topic}

Article excerpt:
{article_content[:2000]}...

Generate:
1. LinkedIn post (300 words)
2. Twitter thread (5-7 tweets)
3. Email snippet (150 words)

Include specific data points."""
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.create_response(
                prompt,
                model=DEFAULT_MODELS["social"],
                reasoning_effort="minimal",
                verbosity="medium"
            )
        )
        
        return f"""---
title: Social Media Content
date: {date_str}
topic: {topic}
---

{result}"""
    
    async def _generate_metadata_async(self, article_content: str, topic: str, date_str: str) -> str:
        """Generate metadata asynchronously"""
        prompt = f"""Generate metadata for: {topic}

Article excerpt:
{article_content[:1500]}...

Create JSON with:
- title
- description (150-160 chars)
- keywords (5-8)
- reading_time
- target_audience"""
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.create_response(
                prompt,
                model=DEFAULT_MODELS["metrics"],
                reasoning_effort="minimal",
                verbosity="low"
            )
        )
        
        metadata = self.parse_json_response(result)
        
        return f"""---
title: Article Metadata
date: {date_str}
---

{json.dumps(metadata, indent=2)}"""
    
    async def _fact_check_async(self, article_content: str) -> Dict[str, Any]:
        """Fact check asynchronously"""
        prompt = f"""Fact-check this article:

{article_content}

Analyze:
1. Data accuracy
2. Citation quality
3. Logical consistency

Return JSON with:
- fact_check_passed: bool
- issues: list
- citation_count: number"""
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self.create_response(
                prompt,
                model=DEFAULT_MODELS["fact_checker"],
                reasoning_effort="medium",
                verbosity="low"
            )
        )
        
        return self.parse_json_response(result)
    
    def _generate_usage_report(self) -> str:
        """Generate token usage report"""
        return f"""---
title: Usage Report
generated_at: {datetime.now().isoformat()}
---

## Token Usage
Total tokens used: {sum(v.get('total', 0) for v in self.token_usage.values())}

## Estimated Cost
Total: ${self.total_cost:.4f}

## Details
{json.dumps(self.token_usage, indent=2)}"""
    
    def generate_article(self, topic: str, word_count: int = 1500) -> Dict[str, Any]:
        """Synchronous wrapper for async generation"""
        return asyncio.run(self.generate_article_async(topic, word_count))
    
    async def generate_article_async(self, topic: str, word_count: int = 1500) -> Dict[str, Any]:
        """Async article generation"""
        return await self.generate_article(topic, word_count)

