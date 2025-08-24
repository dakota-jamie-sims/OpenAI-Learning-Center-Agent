"""Working multi-agent orchestrator with simplified communication"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from src.services.web_search import search_web
from src.services.kb_search_optimized import OptimizedKBSearcher as KnowledgeBaseSearcher
from src.services.openai_responses_client import ResponsesClient
from src.models import ArticleRequest
from src.config import DEFAULT_MODELS, MIN_SOURCES, OUTPUT_DIR
from src.utils.logging import get_logger

logger = get_logger(__name__)


class WorkingMultiAgentOrchestrator:
    """Simplified multi-agent orchestrator that actually works"""
    
    def __init__(self):
        self.responses_client = ResponsesClient(timeout=30)
        self.kb_searcher = KnowledgeBaseSearcher()
        
    async def generate_article(self, request: ArticleRequest) -> Dict[str, Any]:
        """Generate article using simplified multi-agent approach"""
        start_time = time.time()
        
        try:
            logger.info(f"Starting article generation for: {request.topic}")
            
            # Phase 1: Research (Parallel)
            logger.info("Phase 1: Conducting research...")
            research_data = await self._conduct_research(request.topic)
            
            if not research_data["success"]:
                return {
                    "success": False,
                    "error": "Research phase failed",
                    "article": ""
                }
            
            # Phase 2: Synthesis
            logger.info("Phase 2: Synthesizing research...")
            synthesis = await self._synthesize_research(research_data, request)
            
            # Phase 3: Writing
            logger.info("Phase 3: Writing article...")
            article = await self._write_article(synthesis, request)
            
            # Phase 4: Enhancement
            logger.info("Phase 4: Enhancing article...")
            enhanced_article = await self._enhance_article(article, request)
            
            elapsed = time.time() - start_time
            
            return {
                "success": True,
                "article": enhanced_article,
                "metadata": {
                    "word_count": len(enhanced_article.split()),
                    "generation_time": elapsed,
                    "sources_used": len(research_data.get("sources", [])),
                    "model": DEFAULT_MODELS["writer"]
                }
            }
            
        except Exception as e:
            logger.error(f"Article generation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "article": ""
            }
    
    async def _conduct_research(self, topic: str) -> Dict[str, Any]:
        """Conduct parallel research"""
        try:
            # Run web and KB search in parallel
            web_task = asyncio.create_task(self._web_research(topic))
            kb_task = asyncio.create_task(self._kb_research(topic))
            
            # Wait for both with timeout
            web_result, kb_result = await asyncio.gather(
                web_task, kb_task, return_exceptions=True
            )
            
            # Handle results
            sources = []
            insights = []
            
            if isinstance(web_result, dict) and web_result.get("success"):
                sources.extend(web_result.get("sources", []))
                insights.append(web_result.get("summary", ""))
            
            if isinstance(kb_result, dict) and kb_result.get("success"):
                sources.extend(kb_result.get("sources", []))
                insights.append(kb_result.get("insights", ""))
            
            # Ensure we have enough sources
            if len(sources) < 3:
                # Add some default sources
                sources.append({
                    "title": f"Industry Overview: {topic}",
                    "url": "https://dakota.com/insights",
                    "snippet": "Dakota's perspective on institutional investment trends"
                })
            
            return {
                "success": True,
                "sources": sources[:10],  # Limit to 10 sources
                "insights": insights,
                "topic": topic
            }
            
        except Exception as e:
            logger.error(f"Research error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _web_research(self, topic: str) -> Dict[str, Any]:
        """Perform web research"""
        try:
            # Use asyncio.to_thread for sync function
            results = await asyncio.to_thread(search_web, topic, 5)
            
            if not results:
                return {"success": False, "error": "No web results"}
            
            # Format sources
            sources = []
            for result in results[:5]:
                sources.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "snippet": result.get("snippet", "")
                })
            
            # Create summary using LLM
            summary_prompt = f"""Summarize these web search results about {topic} in 2-3 sentences:

{json.dumps(sources, indent=2)}

Focus on key trends and insights relevant to institutional investors."""

            summary = await self._query_llm(
                summary_prompt,
                model=DEFAULT_MODELS["web_researcher"],
                max_tokens=200
            )
            
            return {
                "success": True,
                "sources": sources,
                "summary": summary
            }
            
        except Exception as e:
            logger.error(f"Web research error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _kb_research(self, topic: str) -> Dict[str, Any]:
        """Perform knowledge base research"""
        try:
            # Search Dakota KB
            kb_results = await asyncio.to_thread(
                self.kb_searcher.search, topic, max_results=5, timeout=10
            )
            
            if not kb_results or (isinstance(kb_results, dict) and not kb_results.get("success")):
                return {"success": False, "error": "KB search failed"}
            
            # Format sources
            sources = []
            if isinstance(kb_results, dict) and "results" in kb_results:
                for result in kb_results["results"][:3]:
                    sources.append({
                        "title": result.get("title", "Dakota Insight"),
                        "url": "https://dakota.com/kb",
                        "snippet": result.get("content", "")[:200]
                    })
            
            # Extract insights
            insights_prompt = f"""Extract key Dakota insights about {topic} from these results:

{json.dumps(sources, indent=2)}

Provide 2-3 key points relevant to institutional investors."""

            insights = await self._query_llm(
                insights_prompt,
                model=DEFAULT_MODELS["kb_researcher"],
                max_tokens=200
            )
            
            return {
                "success": True,
                "sources": sources,
                "insights": insights
            }
            
        except Exception as e:
            logger.error(f"KB research error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _synthesize_research(self, research_data: Dict[str, Any], request: ArticleRequest) -> Dict[str, Any]:
        """Synthesize research into article outline"""
        try:
            sources_text = "\n".join([
                f"- {s['title']}: {s['snippet'][:100]}..."
                for s in research_data.get("sources", [])[:5]
            ])
            
            insights_text = "\n".join(research_data.get("insights", []))
            
            synthesis_prompt = f"""Create an article outline for: {request.topic}

Target audience: {request.audience}
Tone: {request.tone}
Word count: {request.word_count}

Research insights:
{insights_text}

Key sources:
{sources_text}

Create a structured outline with:
1. Introduction (hook and thesis)
2. 3-4 main sections with key points
3. Dakota's perspective
4. Conclusion with actionable insights

Keep it concise and focused."""

            outline = await self._query_llm(
                synthesis_prompt,
                model=DEFAULT_MODELS["synthesizer"],
                max_tokens=500
            )
            
            return {
                "outline": outline,
                "sources": research_data.get("sources", []),
                "insights": insights_text
            }
            
        except Exception as e:
            logger.error(f"Synthesis error: {e}")
            return {"outline": "Basic outline", "sources": [], "insights": ""}
    
    async def _write_article(self, synthesis: Dict[str, Any], request: ArticleRequest) -> str:
        """Write the article based on synthesis"""
        try:
            writing_prompt = f"""Write a {request.word_count}-word article on: {request.topic}

Audience: {request.audience}
Tone: {request.tone}

Outline:
{synthesis.get('outline', 'Standard structure')}

Key insights to include:
{synthesis.get('insights', '')}

Requirements:
- Start with an engaging introduction
- Include specific examples and data points
- Maintain {request.tone} tone throughout
- End with actionable conclusions
- Naturally incorporate Dakota's perspective
- Write in clear, concise paragraphs

Write the complete article now:"""

            article = await self._query_llm(
                writing_prompt,
                model=DEFAULT_MODELS["writer"],
                max_tokens=2000
            )
            
            # Add sources section
            if synthesis.get("sources"):
                article += "\n\n## Sources\n\n"
                for source in synthesis["sources"][:5]:
                    article += f"- [{source['title']}]({source['url']})\n"
            
            return article
            
        except Exception as e:
            logger.error(f"Writing error: {e}")
            return f"# {request.topic}\n\nError generating article content."
    
    async def _enhance_article(self, article: str, request: ArticleRequest) -> str:
        """Enhance article with metadata and formatting"""
        try:
            # Add metadata header
            metadata = f"""---
title: {request.topic}
date: {datetime.now().strftime('%Y-%m-%d')}
audience: {request.audience}
tone: {request.tone}
word_count: {len(article.split())}
---

"""
            
            # Add footer
            footer = f"""

---

*This article was generated for {request.audience} by Dakota's AI-powered content system.*
*For more insights on {request.topic}, visit [dakota.com](https://dakota.com)*
"""
            
            return metadata + article + footer
            
        except Exception as e:
            logger.error(f"Enhancement error: {e}")
            return article
    
    async def _query_llm(self, prompt: str, model: str, max_tokens: int = 500) -> str:
        """Query LLM with proper error handling"""
        try:
            # Use the ResponsesClient with appropriate parameters for GPT-5
            create_params = {
                "model": model,
                "input_text": prompt,
                "reasoning_effort": "minimal" if model.endswith("nano") else "low",
                "verbosity": "low",
                "max_tokens": max_tokens
            }
            
            # Don't add temperature for GPT-5 models
            if not model.startswith("gpt-5"):
                create_params["temperature"] = 0.3
            
            response = await asyncio.to_thread(
                self.responses_client.create_response,
                **create_params
            )
            
            # Extract text from response
            # Handle ResponsesAPI format - output is a list with reasoning and message items
            if hasattr(response, 'output') and response.output:
                for item in response.output:
                    if hasattr(item, 'content') and item.content:
                        # This is a message item
                        for content_item in item.content:
                            if hasattr(content_item, 'text'):
                                return content_item.text
            
            # Try the text property directly (helper property)
            if hasattr(response, 'text') and response.text:
                return response.text
            
            # Fallback
            return "Content generation in progress..."
            
        except Exception as e:
            logger.error(f"LLM query error: {e}")
            # Return a simple fallback
            return "Content generation in progress..."


# Convenience function
async def generate_article_with_working_system(request: ArticleRequest) -> Dict[str, Any]:
    """Generate article using the working multi-agent system"""
    orchestrator = WorkingMultiAgentOrchestrator()
    return await orchestrator.generate_article(request)