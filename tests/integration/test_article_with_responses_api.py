#!/usr/bin/env python3
"""
Test article generation with proper API usage
"""
import os
import sys
from datetime import datetime
import asyncio

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from openai import OpenAI
from services.web_search import search_web
from services.kb_search_optimized import search_knowledge_base
from utils.logging import get_logger

logger = get_logger(__name__)

class SimpleArticleGenerator:
    """Simple article generator using proper APIs"""
    
    def __init__(self):
        self.client = OpenAI()
    
    async def generate_article(self, topic: str, word_count: int = 1000):
        """Generate article with parallel research"""
        logger.info(f"Generating article on: {topic}")
        
        # Phase 1: Parallel research
        logger.info("Phase 1: Conducting parallel research...")
        research_data = await self._parallel_research(topic)
        
        # Phase 2: Generate article
        logger.info("Phase 2: Generating article...")
        article = self._generate_content(topic, research_data, word_count)
        
        # Phase 3: Quality check
        logger.info("Phase 3: Quality check...")
        quality_score = self._check_quality(article)
        
        return {
            "success": True,
            "article": article,
            "word_count": len(article.split()),
            "quality_score": quality_score,
            "research_sources": len(research_data.get("web_results", [])),
        }
    
    async def _parallel_research(self, topic: str):
        """Conduct parallel research"""
        async def search_web_async():
            return search_web(f"{topic} 2024 trends analysis", max_results=3)
        
        async def search_kb_async():
            return search_knowledge_base(topic, max_results=3)
        
        # Run searches in parallel
        web_task = asyncio.create_task(search_web_async())
        kb_task = asyncio.create_task(search_kb_async())
        
        web_results, kb_results = await asyncio.gather(web_task, kb_task)
        
        return {
            "web_results": web_results,
            "kb_results": kb_results
        }
    
    def _generate_content(self, topic: str, research_data: dict, word_count: int) -> str:
        """Generate article content using GPT-5"""
        
        # Format research findings
        web_findings = "\n".join([
            f"- {r.get('title', 'Unknown')}: {r.get('snippet', '')[:100]}..."
            for r in research_data.get("web_results", [])[:3]
        ])
        
        prompt = f"""Write a comprehensive article about "{topic}" for institutional investors.

Target length: approximately {word_count} words.

Use these research findings:
{web_findings}

Requirements:
1. Professional yet conversational tone
2. Include specific data points and trends
3. Focus on practical insights for investors
4. Structure with clear sections and headers
5. End with actionable recommendations

Write the complete article now:"""

        try:
            # Use Responses API for GPT-5
            response = self.client.responses.create(
                model="gpt-5",
                input=prompt,
                reasoning={
                    "effort": "medium"
                },
                text={
                    "verbosity": "high"
                }
            )
            
            # Extract text from response
            if hasattr(response, 'output_text'):
                return response.output_text
            elif hasattr(response, 'output') and response.output:
                for item in response.output:
                    if hasattr(item, 'content'):
                        for content in item.content:
                            if hasattr(content, 'text'):
                                return content.text
            
            return "Error: Could not extract article text"
            
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            # Fallback to chat completions with gpt-4o
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You are an expert financial writer."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=word_count * 2,  # Rough estimate
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e2:
                logger.error(f"Fallback also failed: {e2}")
                return f"Error generating article: {str(e)}"
    
    def _check_quality(self, article: str) -> float:
        """Simple quality check"""
        score = 85.0  # Base score
        
        # Check word count
        word_count = len(article.split())
        if word_count > 800:
            score += 5
        
        # Check for headers
        if "#" in article:
            score += 5
        
        # Check for data/numbers
        import re
        if re.search(r'\d+%|\$\d+|\d{4}', article):
            score += 5
        
        return min(score, 100.0)


async def main():
    """Test the simple article generator"""
    generator = SimpleArticleGenerator()
    
    topic = "AI Investment Opportunities in Q4 2024"
    
    logger.info("="*60)
    logger.info("Testing Simple Article Generation with GPT-5")
    logger.info("="*60)
    
    start_time = datetime.now()
    
    result = await generator.generate_article(topic, word_count=1000)
    
    duration = (datetime.now() - start_time).total_seconds()
    
    if result["success"]:
        logger.info(f"\n✅ Article generated successfully in {duration:.1f} seconds!")
        logger.info(f"📊 Word count: {result['word_count']}")
        logger.info(f"⭐ Quality score: {result['quality_score']}/100")
        logger.info(f"🔍 Research sources: {result['research_sources']}")
        
        # Show preview
        logger.info("\n" + "="*60)
        logger.info("Article Preview:")
        logger.info("="*60)
        preview = result["article"][:500] + "..." if len(result["article"]) > 500 else result["article"]
        logger.info(preview)
        
        # Save to file
        filename = f"output/test_article_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        os.makedirs("output", exist_ok=True)
        with open(filename, "w") as f:
            f.write(result["article"])
        logger.info(f"\n📄 Full article saved to: {filename}")
        
    else:
        logger.error(f"❌ Article generation failed: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(main())