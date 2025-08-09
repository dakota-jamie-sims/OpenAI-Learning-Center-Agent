from openai import OpenAI
from typing import Optional, Dict, Any, List
import re
from datetime import datetime
from pathlib import Path

class ContentWriterAgent:
    """Agent responsible for writing comprehensive articles based on outlines and research"""
    
    def __init__(self, client: OpenAI, model: str = "gpt-4"):
        self.client = client
        self.model = model
        self.name = "contentWriter_agent"
        
        # Load prompt
        prompts_dir = Path(__file__).parent.parent / "prompts"
        self.prompt = self._load_prompt(prompts_dir / "dakota-content-writer.md")
    
    def _load_prompt(self, path: Path) -> str:
        """Load prompt from file"""
        if path.exists():
            with open(path, 'r') as f:
                return f.read()
        return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """Default prompt if file doesn't exist"""
        return """You are an expert content writer for Dakota's Learning Center.
        Create comprehensive, well-researched articles that provide practical value to institutional investors.
        Maintain a professional yet conversational tone aligned with Dakota's brand voice."""
    
    def write_article(self, topic: str, outline: Dict[str, Any], research: Dict[str, Any],
                     min_words: int = 1750) -> Dict[str, Any]:
        """Write a complete article based on outline and research"""
        
        # Extract research content
        research_content = self._prepare_research_content(research)
        
        # Extract outline structure
        outline_structure = outline.get('outline_structure', outline.get('outline_raw', ''))
        if isinstance(outline_structure, dict):
            outline_text = self._format_outline_for_prompt(outline_structure)
        else:
            outline_text = str(outline_structure)
        
        prompt = f"""Write a comprehensive article on the following topic using the provided outline and research.

Topic: {topic}
Minimum Word Count: {min_words}
Date: {datetime.now().strftime('%Y-%m-%d')}

OUTLINE:
{outline_text}

RESEARCH CONTENT:
{research_content}

Requirements:
- Follow the Dakota Learning Center article template exactly
- Include at least 10 verified sources with inline citations
- Maintain professional yet conversational tone
- Ensure minimum {min_words} words
- Include "Key Insights at a Glance" section
- End with "Key Takeaways" section
- Add internal links to related Dakota Learning Center articles

Write the complete article now:"""

        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=4000
            )
            
            article_content = response.choices[0].message.content
            
            # Process and validate the article
            processed_article = self._process_article(article_content, topic)
            
            return {
                "topic": topic,
                "article": processed_article['content'],
                "word_count": processed_article['word_count'],
                "reading_time": processed_article['reading_time'],
                "sources_count": processed_article['sources_count'],
                "sections": processed_article['sections'],
                "status": "success"
            }
            
        except Exception as e:
            return {
                "topic": topic,
                "error": str(e),
                "status": "error"
            }
    
    def _prepare_research_content(self, research: Dict[str, Any]) -> str:
        """Prepare research content for the prompt"""
        content_parts = []
        
        # Add synthesis if available
        if 'synthesis' in research:
            synthesis = research['synthesis']
            if isinstance(synthesis, dict):
                content_parts.append(synthesis.get('synthesis', ''))
            else:
                content_parts.append(str(synthesis))
        
        # Add individual research results
        if 'research_results' in research:
            for result in research['research_results']:
                source = result.get('source', 'Unknown')
                content = result.get('content', '')
                content_parts.append(f"\n[Source: {source}]\n{content}")
        
        return "\n\n".join(content_parts)
    
    def _format_outline_for_prompt(self, outline: Dict[str, Any]) -> str:
        """Format outline structure for the prompt"""
        formatted = []
        
        if 'title' in outline:
            formatted.append(f"Title: {outline['title']}")
        
        if 'summary' in outline:
            formatted.append(f"\nSummary: {outline['summary']}")
        
        if 'objectives' in outline:
            formatted.append("\nObjectives:")
            for obj in outline['objectives']:
                formatted.append(f"- {obj}")
        
        if 'sections' in outline:
            formatted.append("\nSections:")
            for section in outline['sections']:
                formatted.append(f"\n## {section.get('title', 'Section')}")
                for subsection in section.get('subsections', []):
                    formatted.append(f"### {subsection.get('title', 'Subsection')}")
                    for content in subsection.get('content', []):
                        formatted.append(f"- {content}")
        
        return "\n".join(formatted)
    
    def _process_article(self, content: str, topic: str) -> Dict[str, Any]:
        """Process and validate the article content"""
        # Count words
        word_count = len(content.split())
        
        # Calculate reading time (avg 200 words per minute)
        reading_time = max(1, round(word_count / 200))
        
        # Count sources (look for markdown links)
        sources = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        sources_count = len(sources)
        
        # Extract sections
        sections = re.findall(r'^##\s+(.+)$', content, re.MULTILINE)
        
        # Add metadata if not present
        if not content.startswith('---'):
            metadata = f"""---
title: {topic}
date: {datetime.now().strftime('%Y-%m-%d')}
word_count: {word_count}
reading_time: {reading_time} minutes
---

"""
            content = metadata + content
        
        return {
            'content': content,
            'word_count': word_count,
            'reading_time': f"{reading_time} minutes",
            'sources_count': sources_count,
            'sections': sections
        }
    
    def expand_section(self, article: Dict[str, Any], section_name: str, 
                      additional_research: Optional[str] = None) -> Dict[str, Any]:
        """Expand a specific section of an article"""
        current_content = article.get('article', '')
        
        prompt = f"""Expand the following section of the article with more detail and examples:

Section to expand: {section_name}

Current article:
{current_content}

{"Additional research:" + additional_research if additional_research else ""}

Please provide an expanded version of just that section, maintaining the same style and tone."""

        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7
            )
            
            expanded_section = response.choices[0].message.content
            
            # Replace the section in the article
            # This is a simplified implementation - you might want to enhance it
            pattern = f"## {section_name}.*?(?=##|$)"
            new_content = re.sub(pattern, expanded_section, current_content, flags=re.DOTALL)
            
            processed = self._process_article(new_content, article['topic'])
            
            return {
                **article,
                "article": processed['content'],
                "word_count": processed['word_count'],
                "expanded_sections": article.get('expanded_sections', []) + [section_name]
            }
            
        except Exception as e:
            return {
                **article,
                "expansion_error": str(e)
            }