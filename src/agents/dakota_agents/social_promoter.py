"""Dakota Social Promoter Agent - Creates multi-platform social content"""

import os
import re
from typing import Dict, Any, List

from .base_agent import DakotaBaseAgent
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DakotaSocialPromoter(DakotaBaseAgent):
    """Creates engaging social media content for multiple platforms"""
    
    def __init__(self):
        super().__init__("social_promoter")
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create social media content"""
        try:
            self.update_status("active", "Creating social media content")
            
            topic = task.get("topic", "")
            article_file = task.get("article_file", "")
            output_file = task.get("output_file", "")
            
            # Read article
            with open(article_file, 'r') as f:
                article_content = f.read()
            
            # Extract key information
            key_points = self._extract_key_points(article_content)
            statistics = self._extract_statistics(article_content)
            
            # Generate social content
            social_content = await self._generate_all_social_content(
                topic, key_points, statistics
            )
            
            # Save social content
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(social_content)
                self.logger.info(f"Social content saved to: {output_file}")
            
            return self.format_response(True, data={
                "platforms_created": ["LinkedIn", "Twitter/X", "Email", "Instagram", "Facebook"],
                "output_file": output_file
            })
            
        except Exception as e:
            self.logger.error(f"Social content error: {e}")
            return self.format_response(False, error=str(e))
    
    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from article"""
        key_points = []
        
        # Look for Key Insights and Key Takeaways
        sections = ["Key Insights", "Key Takeaways"]
        
        for section in sections:
            match = re.search(
                rf'##\s*{section}.*?\n((?:[-•*]\s*.+\n?)+)',
                content,
                re.IGNORECASE
            )
            
            if match:
                points = match.group(1).strip().split('\n')
                for point in points:
                    cleaned = point.strip().lstrip('-•*').strip()
                    if cleaned:
                        key_points.append(cleaned)
        
        return key_points[:8]  # Limit to 8 total
    
    def _extract_statistics(self, content: str) -> List[str]:
        """Extract key statistics from article"""
        statistics = []
        
        # Find sentences with statistics
        sentences = re.split(r'[.!?]+', content)
        
        for sentence in sentences:
            # Look for percentages or dollar amounts
            if re.search(r'\d+(?:\.\d+)?%|\$[\d,]+(?:\.\d+)?', sentence):
                statistics.append(sentence.strip())
        
        return statistics[:5]  # Top 5 statistics
    
    async def _generate_all_social_content(self, topic: str, key_points: List[str], 
                                         statistics: List[str]) -> str:
        """Generate content for all platforms"""
        
        # Create comprehensive prompt
        prompt = f"""Create social media content for an article about: {topic}

Key points from the article:
{chr(10).join(key_points[:4])}

Key statistics:
{chr(10).join(statistics[:3])}

Generate the following:

1. **Three LinkedIn posts** (professional, conversational, data-driven tones)
   - Each 150-200 words
   - Include relevant emojis
   - End with link placeholder and hashtags

2. **Twitter/X Thread (10 posts)**
   - Hook in first tweet
   - One key point per tweet
   - Use relevant emojis
   - End with CTA

3. **Email Newsletter Snippet**
   - Subject line with emoji
   - 150-word summary
   - Clear CTA

4. **Three Instagram posts**
   - Visual descriptions with emojis
   - Focus on different angles
   - Relevant hashtags

5. **Facebook post**
   - Professional but accessible tone
   - 100-150 words
   - Engagement question

Use professional emojis strategically. Make each platform-specific and engaging."""

        social_content = await self.query_llm(prompt, max_tokens=2500)
        
        # Format with template structure
        formatted_content = f"""# Social Media Content

{social_content}

---

**Note:** All social media posts should link to the full article on the Dakota Learning Center."""
        
        return formatted_content