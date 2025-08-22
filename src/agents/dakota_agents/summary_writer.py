"""Dakota Summary Writer Agent - Creates executive summaries"""

import os
import re
from typing import Dict, Any, List

from .base_agent import DakotaBaseAgent
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DakotaSummaryWriter(DakotaBaseAgent):
    """Creates concise executive summaries"""
    
    def __init__(self):
        super().__init__("summary_writer", model_override="gpt-5-mini")
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Create executive summary"""
        try:
            self.update_status("active", "Creating executive summary")
            
            topic = task.get("topic", "")
            audience = task.get("audience", "institutional investors")
            article_file = task.get("article_file", "")
            output_file = task.get("output_file", "")
            
            # Read article
            with open(article_file, 'r') as f:
                article_content = f.read()
            
            # Extract key components
            key_takeaways = self._extract_key_takeaways(article_content)
            main_value = await self._identify_main_value(topic, article_content)
            
            # Generate overview
            overview = await self._generate_overview(topic, article_content, audience)
            
            # Create summary content
            summary_content = self._create_summary_content(
                topic, audience, main_value, overview, key_takeaways
            )
            
            # Save summary
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(summary_content)
                self.logger.info(f"Summary saved to: {output_file}")
            
            return self.format_response(True, data={
                "main_value": main_value,
                "takeaways_count": len(key_takeaways),
                "output_file": output_file
            })
            
        except Exception as e:
            self.logger.error(f"Summary error: {e}")
            return self.format_response(False, error=str(e))
    
    def _extract_key_takeaways(self, content: str) -> List[str]:
        """Extract key takeaways from article"""
        takeaways = []
        
        # Look for Key Takeaways section
        match = re.search(
            r'##\s*Key\s+Takeaways.*?\n((?:[-•*]\s*.+\n?)+)',
            content,
            re.IGNORECASE
        )
        
        if match:
            points = match.group(1).strip().split('\n')
            for point in points:
                cleaned = point.strip().lstrip('-•*').strip()
                if cleaned:
                    takeaways.append(cleaned)
        
        # If no takeaways found, extract from Key Insights
        if not takeaways:
            insights_match = re.search(
                r'##\s*Key\s+Insights.*?\n((?:[-•*]\s*.+\n?)+)',
                content,
                re.IGNORECASE
            )
            
            if insights_match:
                points = insights_match.group(1).strip().split('\n')
                for point in points[:4]:
                    cleaned = point.strip().lstrip('-•*').strip()
                    if cleaned:
                        takeaways.append(cleaned)
        
        return takeaways[:4]  # Limit to 4
    
    async def _identify_main_value(self, topic: str, content: str) -> str:
        """Identify the main value proposition"""
        # Extract first few paragraphs
        body = self._extract_body(content)
        first_section = body[:1000]
        
        prompt = f"""Based on this article introduction about {topic}, write ONE sentence describing the main value for institutional investors:

{first_section}

Provide just the value statement (one sentence):"""

        value = await self.query_llm(prompt, max_tokens=50)
        return value.strip()
    
    async def _generate_overview(self, topic: str, content: str, audience: str) -> str:
        """Generate article overview"""
        # Get article structure
        sections = re.findall(r'^##\s+([^#\n]+)', content, re.MULTILINE)
        
        prompt = f"""Write a 2-3 sentence overview of this article about {topic} for {audience}.

The article covers these main sections:
{chr(10).join(sections[:5])}

Explain what the article covers and why it matters. Be concise and specific:"""

        overview = await self.query_llm(prompt, max_tokens=100)
        return overview.strip()
    
    def _extract_body(self, content: str) -> str:
        """Extract article body without frontmatter"""
        if content.startswith("---"):
            end_index = content.find("---", 3)
            if end_index > 0:
                return content[end_index + 3:].strip()
        return content
    
    def _create_summary_content(self, topic: str, audience: str, main_value: str,
                              overview: str, takeaways: List[str]) -> str:
        """Create complete summary content"""
        
        # Format audience
        audience_formatted = audience.title()
        
        # Format takeaways
        takeaways_text = "\n".join([f"- {t}" for t in takeaways])
        
        content = f"""# Executive Summary

**Topic:** {topic}
**Target Audience:** {audience_formatted}
**Key Value:** {main_value}

## Article Overview
{overview}

## Key Takeaways
{takeaways_text}

## Call to Action
Investment professionals should review these insights to inform their {topic.lower()} strategies. For detailed analysis and implementation guidance, read the full article and explore related resources in the Dakota Learning Center."""
        
        return content