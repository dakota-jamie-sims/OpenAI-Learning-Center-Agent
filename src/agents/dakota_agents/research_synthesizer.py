"""Dakota Research Synthesizer Agent - Combines KB and web research into strategy"""

import json
from typing import Dict, Any, List

from .base_agent import DakotaBaseAgent
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DakotaResearchSynthesizer(DakotaBaseAgent):
    """Synthesizes research from multiple sources into comprehensive content strategy"""
    
    def __init__(self):
        super().__init__("research_synthesizer")
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize research into article outline and strategy"""
        try:
            self.update_status("active", "Synthesizing research findings")
            
            topic = task.get("topic", "")
            audience = task.get("audience", "institutional investors")
            tone = task.get("tone", "professional")
            word_count = task.get("word_count", 1750)
            research_data = task.get("research_data", {})
            
            # Extract sources and insights
            all_sources = research_data.get("sources", [])
            all_insights = research_data.get("insights", [])
            kb_result = research_data.get("kb_result", {})
            web_result = research_data.get("web_result", {})
            
            # Create synthesis prompt
            synthesis_prompt = await self._create_synthesis_prompt(
                topic, audience, tone, word_count,
                all_sources, all_insights
            )
            
            # Generate comprehensive outline
            outline = await self.query_llm(synthesis_prompt, max_tokens=1000)
            
            # Extract key themes
            key_themes = await self._extract_key_themes(topic, all_insights)
            
            # Identify best sources for citations
            citation_sources = self._select_citation_sources(all_sources)
            
            # Create content strategy
            strategy = {
                "outline": outline,
                "key_themes": key_themes,
                "citation_sources": citation_sources,
                "dakota_angles": self._identify_dakota_angles(topic, kb_result),
                "current_trends": self._extract_current_trends(web_result),
                "target_sections": self._define_sections(word_count)
            }
            
            return self.format_response(True, data=strategy)
            
        except Exception as e:
            self.logger.error(f"Synthesis error: {e}")
            return self.format_response(False, error=str(e))
    
    async def _create_synthesis_prompt(self, topic: str, audience: str, tone: str,
                                     word_count: int, sources: List[Dict], 
                                     insights: List[str]) -> str:
        """Create detailed synthesis prompt"""
        
        # Format sources
        source_list = []
        for i, source in enumerate(sources[:10], 1):
            source_list.append(f"{i}. {source.get('title', 'Unknown')}: {source.get('snippet', '')[:100]}...")
        
        # Format insights
        insight_list = "\n".join([f"- {insight}" for insight in insights[:5]])
        
        prompt = f"""Create a detailed article outline for: {topic}

Target audience: {audience}
Tone: {tone}
Word count: {word_count}

Research insights:
{insight_list}

Key sources available:
{chr(10).join(source_list)}

Create a comprehensive outline that includes:

1. **Title** - Compelling and SEO-friendly

2. **Introduction** (hook and thesis) - NO "Introduction" heading

3. **Key Insights at a Glance** - 4 data-driven bullet points with specific statistics

4. **Main Sections** (3-4 sections):
   - Clear, descriptive headings
   - 3-4 key points per section
   - Specific data points to include
   - Examples or case studies to reference

5. **Key Takeaways** - 3-5 actionable insights

6. **Conclusion** - Forward-looking perspective with call to action

Requirements:
- Focus on institutional investor needs
- Include specific numbers and data points
- Suggest where to place inline citations
- Maintain {tone} tone throughout
- Structure for {word_count} words total

Provide the complete outline with specific content points for each section."""

        return prompt
    
    async def _extract_key_themes(self, topic: str, insights: List[str]) -> List[str]:
        """Extract key themes from research"""
        if not insights:
            return [
                "Market evolution and current trends",
                "Best practices for institutional investors",
                "Data-driven decision making",
                "Future outlook and opportunities"
            ]
        
        prompt = f"""Based on these research insights about {topic}, identify 4 key themes:

{chr(10).join(insights)}

List 4 concise themes that should be woven throughout the article:"""

        try:
            themes_text = await self.query_llm(prompt, max_tokens=200)
            
            # Parse themes
            themes = []
            for line in themes_text.split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-')):
                    theme = line.lstrip('0123456789.-').strip()
                    if theme:
                        themes.append(theme)
            
            return themes[:4] if themes else [
                f"Current state of {topic}",
                "Institutional best practices",
                "Market opportunities",
                "Strategic considerations"
            ]
            
        except:
            return [
                f"Evolution of {topic}",
                "Institutional perspectives",
                "Market dynamics",
                "Future trends"
            ]
    
    def _select_citation_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Select best sources for citations"""
        # Prioritize by authority and recency
        scored_sources = []
        
        for source in sources:
            score = 0
            
            # Authority score
            if source.get("authority", 0) > 0:
                score += source["authority"] * 2
            
            # Recency bonus
            if "2024" in str(source.get("date", "")) or "2025" in str(source.get("date", "")):
                score += 2
            
            # Type bonus
            if source.get("type") == "dakota_kb":
                score += 1
                
            scored_sources.append({**source, "citation_score": score})
        
        # Sort by score and return top 10
        scored_sources.sort(key=lambda x: x["citation_score"], reverse=True)
        return scored_sources[:10]
    
    def _identify_dakota_angles(self, topic: str, kb_result: Dict[str, Any]) -> List[str]:
        """Identify Dakota-specific angles from KB research"""
        angles = []
        
        if kb_result.get("success") and kb_result.get("data", {}).get("related_articles"):
            angles.append("Dakota's extensive coverage of this topic")
            angles.append("Proven frameworks from Dakota's research")
            
        angles.extend([
            "Institutional investor focus",
            "Data-driven insights",
            "Practical implementation strategies"
        ])
        
        return angles[:3]
    
    def _extract_current_trends(self, web_result: Dict[str, Any]) -> List[str]:
        """Extract current trends from web research"""
        trends = []
        
        if web_result.get("success") and web_result.get("data", {}).get("summary"):
            # Web researcher already provided a summary
            trends.append(web_result["data"]["summary"])
        
        # Add default trends
        trends.extend([
            "Increased institutional adoption",
            "Focus on data and analytics",
            "Regulatory evolution"
        ])
        
        return trends[:3]
    
    def _define_sections(self, word_count: int) -> Dict[str, int]:
        """Define section word counts based on total target"""
        if word_count <= 1000:
            return {
                "introduction": 150,
                "main_content": 600,
                "conclusion": 150,
                "key_insights": 100
            }
        elif word_count <= 1500:
            return {
                "introduction": 200,
                "main_content": 1000,
                "conclusion": 200,
                "key_insights": 100
            }
        else:  # 1750+
            return {
                "introduction": 250,
                "main_content": 1300,
                "conclusion": 200,
                "key_insights": 150
            }