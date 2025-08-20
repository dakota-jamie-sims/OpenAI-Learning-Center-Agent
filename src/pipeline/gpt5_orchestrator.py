"""
GPT-5 Orchestrator using Responses API
Simplified implementation focusing on core functionality
"""
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.services.openai_responses_client import ResponsesClient
from src.config import DEFAULT_MODELS, OUTPUT_BASE_DIR

load_dotenv()


class GPT5Orchestrator:
    """Orchestrator using GPT-5 with Responses API"""
    
    def __init__(self):
        self.client = ResponsesClient()
        self.output_dir = Path(OUTPUT_BASE_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_article(self, topic: str, word_count: int = 1500) -> dict:
        """Generate article using GPT-5 with responses API"""
        
        print(f"\n🚀 Starting article generation for: {topic}")
        print(f"📊 Target word count: {word_count}")
        
        # Create output directory
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        safe_topic = "".join(c for c in topic if c.isalnum() or c in " -_").strip()
        article_dir = self.output_dir / f"{timestamp}-{safe_topic[:50]}"
        article_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Generate the main article content
            print("\n📝 Generating article content...")
            article_prompt = f"""Write a comprehensive article about: {topic}

Requirements:
- Target length: {word_count} words
- Written for institutional investors and financial professionals
- Include specific data, statistics, and market insights
- Professional tone suitable for Dakota's Learning Center
- Include actionable insights and strategic recommendations
- Structure with clear sections and subheadings
- Focus on practical value for investment decision-making

Format the article with proper markdown formatting including:
- A compelling title
- Clear section headers
- Bullet points where appropriate
- Emphasis on key statistics and insights"""

            # Use GPT-5 with medium reasoning for quality content
            response = self.client.create_response(
                model=DEFAULT_MODELS["writer"],
                input_text=article_prompt,
                reasoning_effort="medium",
                verbosity="high",  # High verbosity for comprehensive articles
                temperature=0.7,
                max_tokens=4000
            )
            
            # Extract the article content
            article_content = self._extract_text_from_response(response)
            
            # Save the article
            article_path = article_dir / "article.md"
            article_path.write_text(article_content)
            print("✅ Article generated and saved")
            
            # Generate metadata
            print("\n📊 Generating metadata...")
            metadata = self._generate_metadata(topic, article_content)
            
            # Generate SEO content
            print("\n🔍 Generating SEO content...")
            seo_content = self._generate_seo(topic, article_content)
            seo_path = article_dir / "seo-metadata.md"
            seo_path.write_text(seo_content)
            print("✅ SEO content saved")
            
            # Generate summary
            print("\n📋 Generating executive summary...")
            summary = self._generate_summary(article_content)
            summary_path = article_dir / "summary.md"
            summary_path.write_text(summary)
            print("✅ Summary saved")
            
            return {
                "status": "success",
                "output_dir": str(article_dir),
                "files": {
                    "article": str(article_path),
                    "seo": str(seo_path),
                    "summary": str(summary_path)
                },
                "metadata": metadata,
                "message": f"Article generated successfully in {article_dir.name}"
            }
            
        except Exception as e:
            print(f"\n❌ Error generating article: {e}")
            return {
                "status": "error",
                "error": str(e),
                "output_dir": str(article_dir)
            }
    
    def _extract_text_from_response(self, response) -> str:
        """Extract text content from responses API response"""
        if hasattr(response, 'content') and response.content:
            if isinstance(response.content, list) and len(response.content) > 0:
                # Handle list of content items
                texts = []
                for item in response.content:
                    if hasattr(item, 'text'):
                        texts.append(item.text)
                return "\n\n".join(texts)
            elif hasattr(response.content, 'text'):
                return response.content.text
        
        # Fallback to string representation
        return str(response)
    
    def _generate_metadata(self, topic: str, article_content: str) -> dict:
        """Generate metadata for the article"""
        metadata_prompt = f"""Analyze this article and generate metadata:

Topic: {topic}
Article: {article_content[:2000]}...

Generate JSON metadata with:
- title: compelling article title
- description: 150-160 character description
- keywords: list of 5-8 relevant keywords
- category: most appropriate category
- reading_time: estimated minutes to read
- target_audience: primary audience description
"""
        
        response = self.client.create_response(
            model=DEFAULT_MODELS["metrics"],
            input_text=metadata_prompt,
            reasoning_effort="minimal",
            verbosity="low",
            temperature=0.3
        )
        
        # Parse the response
        import json
        try:
            metadata_text = self._extract_text_from_response(response)
            # Find JSON in the response
            import re
            json_match = re.search(r'\{[^}]+\}', metadata_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except:
            pass
        
        # Fallback metadata
        return {
            "title": topic,
            "description": f"Comprehensive guide on {topic} for institutional investors",
            "keywords": [topic.lower(), "investment", "institutional", "dakota"],
            "category": "Investment Strategy",
            "reading_time": 5,
            "target_audience": "Institutional investors and financial professionals"
        }
    
    def _generate_seo(self, topic: str, article_content: str) -> str:
        """Generate SEO-optimized content"""
        seo_prompt = f"""Create SEO metadata for this article:

Topic: {topic}
Article excerpt: {article_content[:1500]}...

Generate:
1. SEO-optimized title (50-60 characters)
2. Meta description (150-160 characters)
3. 5-8 relevant keywords
4. 3 social media descriptions (Twitter, LinkedIn, Email)
5. URL slug suggestion

Format as markdown with clear sections."""
        
        response = self.client.create_response(
            model=DEFAULT_MODELS["seo"],
            input_text=seo_prompt,
            reasoning_effort="minimal",
            verbosity="medium",
            temperature=0.5
        )
        
        return self._extract_text_from_response(response)
    
    def _generate_summary(self, article_content: str) -> str:
        """Generate executive summary"""
        summary_prompt = f"""Create an executive summary of this article:

{article_content[:3000]}...

Generate a concise summary that includes:
1. Key findings (3-5 bullet points)
2. Main statistics and data points
3. Strategic recommendations
4. One-paragraph synthesis

Keep it under 300 words, focused on actionable insights for institutional investors."""
        
        response = self.client.create_response(
            model=DEFAULT_MODELS["summary"],
            input_text=summary_prompt,
            reasoning_effort="low",
            verbosity="medium",
            temperature=0.5
        )
        
        return self._extract_text_from_response(response)