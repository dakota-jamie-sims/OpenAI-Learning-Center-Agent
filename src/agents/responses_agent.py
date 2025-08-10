"""
OpenAI Responses API Agent Implementation
Supports web search and other built-in tools
"""
import os
import json
from typing import Dict, Any, List, Optional
from openai import OpenAI


class ResponsesAgent:
    """Agent that uses OpenAI Responses API with built-in tools"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key)
        
    def run_with_web_search(
        self, 
        prompt: str, 
        model: str = "gpt-4.1",
        search_context_size: str = "medium",
        user_location: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Run agent with web search capability using Responses API"""
        
        # Build tools configuration
        tools = [{
            "type": "web_search_preview",
            "search_context_size": search_context_size
        }]
        
        # Add user location if provided
        if user_location:
            tools[0]["user_location"] = user_location
            
        try:
            # Create response with web search
            response = self.client.responses.create(
                model=model,
                tools=tools,
                input=prompt,
                store=True  # Store by default for reference
            )
            
            # Extract results
            result = {
                "status": "success",
                "output_text": response.output_text if hasattr(response, 'output_text') else "",
                "outputs": [],
                "web_search_results": [],
                "citations": []
            }
            
            # Process outputs
            if hasattr(response, 'outputs'):
                for output in response.outputs:
                    if output.type == "web_search_call":
                        result["web_search_results"].append({
                            "id": output.id,
                            "status": output.status,
                            "action": getattr(output, 'action', 'search'),
                            "query": getattr(output, 'query', None)
                        })
                    elif output.type == "message":
                        # Extract text and citations
                        if hasattr(output, 'content'):
                            for content in output.content:
                                if content.type == "output_text":
                                    if not result["output_text"]:  # Use first text output
                                        result["output_text"] = content.text
                                    
                                    # Extract citations from annotations
                                    if hasattr(content, 'annotations'):
                                        for annotation in content.annotations:
                                            if annotation.type == "url_citation":
                                                result["citations"].append({
                                                    "url": annotation.url,
                                                    "title": annotation.title,
                                                    "start": annotation.start_index,
                                                    "end": annotation.end_index
                                                })
                    
                    result["outputs"].append(output)
            
            # Add usage if available
            if hasattr(response, 'usage'):
                result["usage"] = response.usage
                
            return result
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "output_text": ""
            }
    
    async def run_web_researcher(self, topic: str) -> str:
        """Run web research for a topic and return formatted results"""
        
        prompt = f"""Research the following topic using web search:
Topic: {topic}

Requirements:
- Find current, authoritative sources (within last 3 months preferred)
- Focus on data from institutional investors, financial institutions, and industry reports
- Include specific statistics, allocation amounts, and market trends
- Provide full URLs for all sources cited
- Organize findings by relevance and credibility

Structure your response as:
## Key Findings
[List 5-7 major findings with inline citations]

## Market Data & Statistics
[Specific numbers, percentages, amounts with sources]

## Expert Perspectives
[Quotes or insights from industry leaders]

## Source Library
### Tier 1 Sources (Government/Academic)
[List with full URLs]

### Tier 2 Sources (Major Financial Media)
[List with full URLs]

### Tier 3 Sources (Industry Reports)
[List with full URLs]"""

        result = await self.run_with_web_search(
            prompt=prompt,
            search_context_size="high"  # Maximum context for research
        )
        
        if result["status"] == "success":
            # Format output with real citations
            output = result["output_text"]
            
            # Ensure we have actual URLs in citations
            if result["citations"]:
                output += "\n\n## Verified Web Sources\n"
                for citation in result["citations"]:
                    output += f"- [{citation['title']}]({citation['url']})\n"
                    
            return output
        else:
            return f"Web research failed: {result.get('error', 'Unknown error')}"


class ResponsesAgentManager:
    """Manages multiple Responses API agents"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.agents = {}
        
    def create_web_researcher(self, name: str = "web_researcher"):
        """Create a web research agent"""
        self.agents[name] = ResponsesAgent(self.api_key)
        return self.agents[name]
        
    async def run_web_research(self, topic: str) -> str:
        """Run web research using Responses API"""
        if "web_researcher" not in self.agents:
            self.create_web_researcher()
            
        agent = self.agents["web_researcher"]
        return await agent.run_web_researcher(topic)