from openai import OpenAI
from typing import Optional, Dict, Any, List
import os
from pathlib import Path

class ResearcherAgent:
    """Consolidated researcher agent that combines KB research, web research, and synthesis"""
    
    def __init__(self, client: OpenAI, model: str = "gpt-4"):
        self.client = client
        self.model = model
        self.name = "researcher_agent"
        
        # Load prompts
        prompts_dir = Path(__file__).parent.parent / "prompts"
        self.kb_prompt = self._load_prompt(prompts_dir / "dakota-kb-researcher.md")
        self.web_prompt = self._load_prompt(prompts_dir / "dakota-web-researcher.md")
        self.synthesizer_prompt = self._load_prompt(prompts_dir / "dakota-research-synthesizer.md")
        
    def _load_prompt(self, path: Path) -> str:
        """Load prompt from file"""
        if path.exists():
            with open(path, 'r') as f:
                return f.read()
        return ""
    
    def research_knowledge_base(self, topic: str, vector_store_id: Optional[str] = None) -> Dict[str, Any]:
        """Research topic in Dakota's knowledge base"""
        tools = []
        if vector_store_id:
            tools = [{"type": "file_search", "file_search": {"max_num_results": 6}}]
        
        messages = [
            {"role": "system", "content": self.kb_prompt},
            {"role": "user", "content": f"Research the following topic in Dakota's knowledge base: {topic}"}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )
            
            return {
                "source": "knowledge_base",
                "content": response.choices[0].message.content,
                "topic": topic
            }
        except Exception as e:
            return {"error": str(e), "source": "knowledge_base"}
    
    def research_web(self, topic: str) -> Dict[str, Any]:
        """Research topic on the web"""
        messages = [
            {"role": "system", "content": self.web_prompt},
            {"role": "user", "content": f"Research the following topic on the web: {topic}"}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            
            return {
                "source": "web",
                "content": response.choices[0].message.content,
                "topic": topic
            }
        except Exception as e:
            return {"error": str(e), "source": "web"}
    
    def synthesize_research(self, research_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synthesize research from multiple sources"""
        combined_research = "\n\n".join([
            f"Source: {r['source']}\n{r.get('content', 'No content')}" 
            for r in research_results
        ])
        
        messages = [
            {"role": "system", "content": self.synthesizer_prompt},
            {"role": "user", "content": f"Synthesize the following research:\n\n{combined_research}"}
        ]
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            
            return {
                "synthesis": response.choices[0].message.content,
                "sources": [r['source'] for r in research_results]
            }
        except Exception as e:
            return {"error": str(e)}
    
    def research(self, topic: str, use_kb: bool = True, use_web: bool = True, 
                vector_store_id: Optional[str] = None) -> Dict[str, Any]:
        """Main research method that combines all research capabilities"""
        research_results = []
        
        # Knowledge base research
        if use_kb:
            kb_result = self.research_knowledge_base(topic, vector_store_id)
            if not kb_result.get("error"):
                research_results.append(kb_result)
        
        # Web research
        if use_web:
            web_result = self.research_web(topic)
            if not web_result.get("error"):
                research_results.append(web_result)
        
        # Synthesize results
        if research_results:
            synthesis = self.synthesize_research(research_results)
            return {
                "topic": topic,
                "research_results": research_results,
                "synthesis": synthesis
            }
        else:
            return {
                "topic": topic,
                "error": "No research results obtained"
            }