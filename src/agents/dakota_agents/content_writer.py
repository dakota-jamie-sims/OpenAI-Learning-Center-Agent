"""Dakota Content Writer Agent - Creates high-quality investment articles"""

import os
from typing import Dict, Any, List
from datetime import datetime

from .base_agent import DakotaBaseAgent
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DakotaContentWriter(DakotaBaseAgent):
    """Content writer that creates Dakota-quality investment articles"""
    
    def __init__(self):
        super().__init__("content_writer")
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Write complete article based on synthesis"""
        try:
            self.update_status("active", "Writing article")
            
            topic = task.get("topic", "")
            audience = task.get("audience", "institutional investors")
            tone = task.get("tone", "professional")
            word_count = task.get("word_count", 1750)
            synthesis = task.get("synthesis", {})
            output_file = task.get("output_file", "")
            
            # Extract synthesis components
            outline_raw = synthesis.get("outline", "")
            # Handle outline as either string or list of dicts
            if isinstance(outline_raw, list):
                # Convert list of dicts to string format
                outline_parts = []
                for section in outline_raw:
                    outline_parts.append(f"## {section['section']}")
                    for point in section.get('points', []):
                        outline_parts.append(f"- {point}")
                outline = "\n".join(outline_parts)
            else:
                outline = outline_raw
            
            key_themes = synthesis.get("key_themes", [])
            citation_sources = synthesis.get("citation_sources", [])
            
            # Create writing prompt
            writing_prompt = await self._create_writing_prompt(
                topic, audience, tone, word_count,
                outline, key_themes, citation_sources
            )
            
            # Generate article with more tokens to ensure completion
            article_content = await self.query_llm(writing_prompt, max_tokens=6000)
            
            # Add frontmatter
            frontmatter = self._create_frontmatter(topic, word_count)
            full_article = frontmatter + "\n" + article_content
            
            # Add sources section
            if citation_sources:
                sources_section = self._create_sources_section(citation_sources[:5])
                full_article += "\n\n" + sources_section
            
            # Add footer
            full_article += "\n\n---\n\n**Note:** For additional insights on related topics, visit the Dakota Learning Center."
            
            # Save article
            if output_file:
                os.makedirs(os.path.dirname(output_file), exist_ok=True)
                with open(output_file, 'w') as f:
                    f.write(full_article)
                self.logger.info(f"Article saved to: {output_file}")
            
            # Calculate actual word count
            actual_word_count = len(article_content.split())
            
            return self.format_response(True, data={
                "article": full_article,
                "word_count": actual_word_count,
                "output_file": output_file,
                "themes_included": key_themes,
                "sources_cited": len(citation_sources)
            })
            
        except Exception as e:
            self.logger.error(f"Writing error: {e}")
            return self.format_response(False, error=str(e))
    
    async def _create_writing_prompt(self, topic: str, audience: str, tone: str,
                                   word_count: int, outline: str, key_themes: List[str],
                                   citation_sources: List[Dict]) -> str:
        """Create comprehensive writing prompt"""
        
        # Format sources for citation
        source_list = []
        for i, source in enumerate(citation_sources[:10], 1):
            source_list.append(
                f"{i}. {source.get('title', 'Source')} - {source.get('snippet', '')[:100]}..."
            )
        
        # Format themes
        themes_text = "\n".join([f"- {theme}" for theme in key_themes])
        
        prompt = f"""Write a {word_count}-word article on: {topic}

Audience: {audience}
Tone: {tone}

OUTLINE TO FOLLOW:
{outline}

KEY THEMES TO WEAVE THROUGHOUT:
{themes_text}

SOURCES FOR CITATION (use inline citations like "According to [Source, Date]"):
{chr(10).join(source_list)}

CRITICAL REQUIREMENTS:
1. Start with # [Article Title] (no "Introduction" heading)
2. Include "## Key Insights at a Glance" section with 4 bullet points containing specific data
3. Write comprehensive main sections as outlined
4. Include at least 10 inline citations using format: (Source Name, Date)
5. MUST include "## Key Takeaways" section near the end with 3-5 actionable points
6. MUST end with "## Conclusion" section (final section before sources)
7. Use specific numbers, percentages, and data points throughout
8. Maintain {tone} tone while being informative
9. Focus on value for {audience}
10. NO "Introduction" or "Executive Summary" sections

VERIFICATION REQUIREMENT - 100% ACCURACY:
- ONLY make claims that are DIRECTLY stated in the provided sources
- Every statistic, percentage, or specific claim MUST come from the sources
- Do NOT extrapolate, infer, or create any data points
- If you cannot find specific data in sources, use general language instead
- Better to be general and accurate than specific and unverifiable

IMPORTANT: The article MUST have both "## Key Takeaways" and "## Conclusion" sections or it will be rejected.

Write the complete article now (excluding frontmatter):"""

        return prompt
    
    def _create_frontmatter(self, topic: str, word_count: int) -> str:
        """Create YAML frontmatter"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        reading_time = max(1, round(word_count / 200))
        
        return f"""---
title: {topic}
date: {date_str}
word_count: {word_count}
reading_time: {reading_time} minutes
---
"""
    
    def _create_sources_section(self, sources: List[Dict[str, Any]]) -> str:
        """Create sources section"""
        sources_text = "## Sources\n\n"
        
        for source in sources:
            title = source.get("title", "Unknown Source")
            url = source.get("url", "#")
            sources_text += f"- [{title}]({url})\n"
        
        return sources_text