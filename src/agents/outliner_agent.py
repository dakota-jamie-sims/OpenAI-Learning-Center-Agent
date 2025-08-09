from openai import OpenAI
from typing import Optional, Dict, Any, List
import json
from pathlib import Path

class OutlinerAgent:
    """Agent responsible for creating article outlines based on research"""
    
    def __init__(self, client: OpenAI, model: str = "gpt-4"):
        self.client = client
        self.model = model
        self.name = "outliner_agent"
        
        # Load prompt
        prompts_dir = Path(__file__).parent.parent / "prompts"
        self.prompt = self._load_prompt(prompts_dir / "dakota-outliner.md")
        if not self.prompt:
            # Default prompt if file doesn't exist
            self.prompt = """You are an expert article outliner for Dakota's Learning Center.
            Create comprehensive, well-structured outlines that align with Dakota's educational philosophy.
            Focus on practical application, real-world examples, and progressive skill building."""
    
    def _load_prompt(self, path: Path) -> str:
        """Load prompt from file"""
        if path.exists():
            with open(path, 'r') as f:
                return f.read()
        return ""
    
    def create_outline(self, topic: str, research_data: Dict[str, Any], 
                      target_audience: str = "general", article_type: str = "educational") -> Dict[str, Any]:
        """Create an article outline based on topic and research"""
        
        # Prepare research summary
        research_summary = research_data.get('synthesis', {}).get('synthesis', '')
        if not research_summary and 'research_results' in research_data:
            research_summary = "\n\n".join([
                r.get('content', '') for r in research_data['research_results']
            ])
        
        prompt = f"""Create a detailed article outline for the following topic:
        
Topic: {topic}
Target Audience: {target_audience}
Article Type: {article_type}

Research Summary:
{research_summary}

Please provide:
1. A compelling title
2. An executive summary (2-3 sentences)
3. Key learning objectives (3-5 bullet points)
4. Detailed section outline with subsections
5. Suggested examples or case studies for each section
6. A conclusion framework
7. Recommended call-to-action

Format the outline in a clear, hierarchical structure."""

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
            
            outline_content = response.choices[0].message.content
            
            # Parse the outline into structured format
            outline_structure = self._parse_outline(outline_content)
            
            return {
                "topic": topic,
                "target_audience": target_audience,
                "article_type": article_type,
                "outline_raw": outline_content,
                "outline_structure": outline_structure,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "topic": topic,
                "error": str(e),
                "status": "error"
            }
    
    def _parse_outline(self, outline_text: str) -> Dict[str, Any]:
        """Parse outline text into structured format"""
        # This is a simplified parser - you might want to enhance it
        lines = outline_text.strip().split('\n')
        structure = {
            "title": "",
            "summary": "",
            "objectives": [],
            "sections": [],
            "conclusion": "",
            "cta": ""
        }
        
        current_section = None
        current_subsection = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Simple parsing logic - enhance as needed
            if line.lower().startswith("title:") or line.startswith("#"):
                structure["title"] = line.replace("Title:", "").replace("#", "").strip()
            elif "summary" in line.lower() and ":" in line:
                structure["summary"] = line.split(":", 1)[1].strip()
            elif line.startswith("##"):
                current_section = {
                    "title": line.replace("##", "").strip(),
                    "subsections": []
                }
                structure["sections"].append(current_section)
            elif line.startswith("###") and current_section:
                current_subsection = {
                    "title": line.replace("###", "").strip(),
                    "content": []
                }
                current_section["subsections"].append(current_subsection)
            elif line.startswith("-") or line.startswith("•"):
                content = line[1:].strip()
                if current_subsection:
                    current_subsection["content"].append(content)
                elif "objective" in outline_text[:outline_text.index(line)].lower():
                    structure["objectives"].append(content)
        
        return structure
    
    def refine_outline(self, outline: Dict[str, Any], feedback: str) -> Dict[str, Any]:
        """Refine an existing outline based on feedback"""
        messages = [
            {"role": "system", "content": self.prompt},
            {"role": "user", "content": f"""Refine the following outline based on this feedback:
            
Current Outline:
{json.dumps(outline['outline_structure'], indent=2)}

Feedback:
{feedback}

Please provide an improved outline addressing the feedback."""}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7
            )
            
            refined_content = response.choices[0].message.content
            refined_structure = self._parse_outline(refined_content)
            
            return {
                **outline,
                "outline_raw": refined_content,
                "outline_structure": refined_structure,
                "refined": True,
                "feedback_applied": feedback
            }
            
        except Exception as e:
            return {
                **outline,
                "refinement_error": str(e)
            }