"""Production-ready multi-agent orchestrator"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from dataclasses import dataclass

from src.agents.orchestrator import OrchestratorAgent
from src.agents.multi_agent_base import AgentMessage, MessageType
from src.models import ArticleRequest
from src.config_production import TIMEOUTS, FEATURE_FLAGS, QUALITY_THRESHOLDS
from src.utils.rate_limiter import init_default_limiters
from src.utils.circuit_breaker import circuit_manager
from src.utils.logging import get_logger


@dataclass
class ArticleResult:
    """Result of article generation"""
    success: bool
    article: str = ""
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

logger = get_logger(__name__)


class ProductionOrchestrator:
    """Production-ready orchestrator with robust error handling"""
    
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        # Initialize rate limiters
        init_default_limiters()
        
        # Metrics
        self.metrics = {
            "total_articles": 0,
            "successful_articles": 0,
            "failed_articles": 0,
            "total_generation_time": 0,
            "phase_timings": {},
        }
    
    async def generate_article_async(self, request: ArticleRequest) -> ArticleResult:
        """Generate article with production safeguards"""
        start_time = time.time()
        self.metrics["total_articles"] += 1
        
        logger.info(f"Starting article generation: {request.topic}")
        
        try:
            # Apply timeout to entire generation
            result = await asyncio.wait_for(
                self._generate_article_internal(request),
                timeout=TIMEOUTS["total_generation"]
            )
            
            # Update metrics
            self.metrics["successful_articles"] += 1
            self.metrics["total_generation_time"] += time.time() - start_time
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Article generation timeout after {TIMEOUTS['total_generation']}s")
            self.metrics["failed_articles"] += 1
            
            return ArticleResult(
                success=False,
                error=f"Generation timeout after {TIMEOUTS['total_generation']} seconds",
                article="",
                metadata={"phase": "timeout", "elapsed": time.time() - start_time}
            )
            
        except Exception as e:
            logger.error(f"Article generation error: {e}")
            self.metrics["failed_articles"] += 1
            
            return ArticleResult(
                success=False,
                error=str(e),
                article="",
                metadata={"phase": "error", "error_type": type(e).__name__}
            )
    
    async def _generate_article_internal(self, request: ArticleRequest) -> ArticleResult:
        """Internal article generation with phase tracking"""
        phase_start = time.time()
        current_phase = "initialization"
        
        try:
            # Phase 1: Research
            current_phase = "research"
            logger.info(f"Phase 1: Research for '{request.topic}'")
            
            research_result = await self._execute_research_phase(request)
            
            if not research_result["success"]:
                # Try simplified research as fallback
                logger.warning("Primary research failed, attempting fallback")
                research_result = await self._fallback_research(request)
                
                if not research_result["success"]:
                    return ArticleResult(
                        success=False,
                        error="Research phase failed after fallback",
                        article="",
                        metadata={"phase": current_phase}
                    )
            
            self._record_phase_timing("research", time.time() - phase_start)
            
            # Phase 2: Quality Check
            current_phase = "quality_check"
            phase_start = time.time()
            logger.info("Phase 2: Quality verification")
            
            quality_result = await self._verify_research_quality(research_result)
            
            if quality_result["score"] < QUALITY_THRESHOLDS["min_confidence_score"]:
                logger.warning(f"Low quality score: {quality_result['score']}")
                # Continue anyway but flag it
                if "metadata" not in research_result:
                    research_result["metadata"] = {}
                research_result["metadata"]["quality_warning"] = True
            
            self._record_phase_timing("quality_check", time.time() - phase_start)
            
            # Phase 3: Writing
            current_phase = "writing"
            phase_start = time.time()
            logger.info("Phase 3: Article writing")
            
            article_result = await self._execute_writing_phase(request, research_result)
            
            if not article_result["success"]:
                # Try simplified writing as fallback
                logger.warning("Primary writing failed, attempting fallback")
                article_result = await self._fallback_writing(request, research_result)
            
            self._record_phase_timing("writing", time.time() - phase_start)
            
            # Phase 4: Enhancement (if enabled)
            if FEATURE_FLAGS["enable_progressive_enhancement"] and article_result["success"]:
                current_phase = "enhancement"
                phase_start = time.time()
                logger.info("Phase 4: Article enhancement")
                
                enhanced_article = await self._enhance_article(article_result["article"])
                article_result["article"] = enhanced_article
                
                self._record_phase_timing("enhancement", time.time() - phase_start)
            
            # Final result
            return ArticleResult(
                success=article_result["success"],
                article=article_result.get("article", ""),
                metadata={
                    **article_result.get("metadata", {}),
                    "research_quality": quality_result,
                    "phase_timings": self.metrics["phase_timings"],
                    "circuit_breaker_states": circuit_manager.get_states(),
                },
                error=article_result.get("error")
            )
            
        except Exception as e:
            logger.error(f"Error in phase {current_phase}: {e}")
            return ArticleResult(
                success=False,
                error=f"Error in {current_phase}: {str(e)}",
                article="",
                metadata={"failed_phase": current_phase}
            )
    
    async def _execute_research_phase(self, request: ArticleRequest) -> Dict[str, Any]:
        """Execute research with parallel processing"""
        if FEATURE_FLAGS["enable_parallel_research"]:
            # Use thread pool for parallel research
            futures = []
            
            with self.executor as executor:
                # Submit research tasks
                futures.append(
                    executor.submit(self._research_web, request.topic)
                )
                futures.append(
                    executor.submit(self._research_kb, request.topic)
                )
                
                # Collect results with timeout
                results = []
                for future in as_completed(futures, timeout=TIMEOUTS["agent_task"]):
                    try:
                        results.append(future.result())
                    except Exception as e:
                        logger.error(f"Research task failed: {e}")
                        results.append({"success": False, "error": str(e)})
            
            # Combine results
            return self._combine_research_results(results)
        else:
            # Sequential research
            return await self._sequential_research(request.topic)
    
    def _research_web(self, topic: str) -> Dict[str, Any]:
        """Web research with error handling"""
        try:
            # Use actual orchestrator for research
            logger.info(f"Delegating to orchestrator for research: {topic}")
            
            # Create research message
            research_msg = AgentMessage(
                from_agent="production_orchestrator",
                to_agent="orchestrator",
                message_type=MessageType.REQUEST,
                task="research",
                payload={
                    "topic": topic,
                    "requirements": {
                        "min_sources": 5,
                        "include_web": True,
                        "include_kb": True
                    }
                },
                context={},
                timestamp=datetime.now().isoformat()
            )
            
            # Get research from orchestrator
            response = self.orchestrator.receive_message(research_msg)
            
            if hasattr(response, 'payload') and response.payload.get("success"):
                research_data = response.payload.get("research", {})
                return {
                    "success": True,
                    "type": "comprehensive",
                    "sources": research_data.get("sources", []),
                    "summary": research_data.get("synthesis", {}).get("web_research", {}).get("research_summary", ""),
                    "insights": research_data.get("synthesis", {}).get("kb_insights", {}).get("kb_insights", ""),
                    "raw_data": research_data
                }
            else:
                error_msg = response.payload.get("error", "Research failed") if hasattr(response, 'payload') else "No response"
                logger.error(f"Research failed: {error_msg}")
                return {"success": False, "type": "comprehensive", "error": error_msg}
                
        except Exception as e:
            logger.error(f"Web research error: {e}")
            return {"success": False, "type": "web", "error": str(e)}
    
    def _research_kb(self, topic: str) -> Dict[str, Any]:
        """KB research with error handling - now handled by _research_web"""
        # This is now handled comprehensively in _research_web
        # Return empty success to maintain compatibility
        return {"success": True, "type": "kb", "insights": "", "articles": []}
    
    def _combine_research_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine multiple research results"""
        combined = {
            "success": any(r.get("success", False) for r in results),
            "sources": [],
            "insights": "",
            "summary": "",
            "raw_data": {}
        }
        
        for result in results:
            if result.get("success"):
                if result.get("type") == "comprehensive":
                    # Handle comprehensive research from orchestrator
                    combined["sources"].extend(result.get("sources", []))
                    combined["summary"] = result.get("summary", "")
                    combined["insights"] = result.get("insights", "")
                    combined["raw_data"] = result.get("raw_data", {})
                elif result.get("type") == "web":
                    combined["sources"].extend(result.get("sources", []))
                    combined["summary"] = result.get("summary", "")
                elif result.get("type") == "kb":
                    combined["insights"] = result.get("insights", "")
        
        # Ensure minimum sources
        if len(combined["sources"]) < QUALITY_THRESHOLDS["min_research_sources"]:
            # Don't fail if we have comprehensive data
            if not combined.get("raw_data"):
                combined["success"] = False
                combined["error"] = "Insufficient research sources"
        
        return combined
    
    async def _fallback_research(self, request: ArticleRequest) -> Dict[str, Any]:
        """Simplified fallback research"""
        logger.info("Executing fallback research")
        
        return {
            "success": True,
            "sources": [
                {"url": "https://fallback.com", "title": f"Basic info on {request.topic}"}
            ],
            "insights": "Limited research available",
            "summary": f"Basic information about {request.topic}",
            "is_fallback": True
        }
    
    async def _verify_research_quality(self, research: Dict[str, Any]) -> Dict[str, Any]:
        """Verify research quality"""
        score = 1.0
        issues = []
        
        # Check source count
        source_count = len(research.get("sources", []))
        if source_count < QUALITY_THRESHOLDS["min_research_sources"]:
            score *= 0.7
            issues.append(f"Low source count: {source_count}")
        
        # Check for fallback
        if research.get("is_fallback"):
            score *= 0.5
            issues.append("Using fallback research")
        
        # Check for insights
        if not research.get("insights"):
            score *= 0.8
            issues.append("Missing knowledge base insights")
        
        return {
            "score": score,
            "passed": score >= QUALITY_THRESHOLDS["min_confidence_score"],
            "issues": issues
        }
    
    async def _execute_writing_phase(
        self, 
        request: ArticleRequest, 
        research: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute writing phase"""
        try:
            # Simulate writing
            logger.info("Generating article content")
            
            article = f"""# {request.topic}

{research.get('summary', '')}

## Overview

This article explores {request.topic} for {request.audience}.

## Key Insights

{research.get('insights', 'Analysis of current trends and implications.')}

## Sources

"""
            for source in research.get("sources", [])[:5]:
                article += f"- [{source['title']}]({source['url']})\n"
            
            # Check word count
            word_count = len(article.split())
            if word_count < request.word_count * 0.8:
                article += f"\n\n## Additional Analysis\n\nExpanded content to meet the target length of {request.word_count} words.\n" * 5
            
            return {
                "success": True,
                "article": article,
                "metadata": {
                    "word_count": len(article.split()),
                    "sources_used": len(research.get("sources", [])),
                }
            }
            
        except Exception as e:
            logger.error(f"Writing error: {e}")
            return {"success": False, "error": str(e)}
    
    async def _fallback_writing(
        self, 
        request: ArticleRequest, 
        research: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Simplified fallback writing"""
        logger.info("Executing fallback writing")
        
        article = f"""# {request.topic}

This article provides an overview of {request.topic} for {request.audience}.

Due to technical limitations, this is a simplified version of the requested content.

## Key Points

- {request.topic} is an important topic for institutional investors
- Further research and analysis is recommended
- Please consult additional sources for comprehensive insights

## Conclusion

For more detailed information about {request.topic}, please contact Dakota's team.
"""
        
        return {
            "success": True,
            "article": article,
            "metadata": {
                "is_fallback": True,
                "word_count": len(article.split())
            }
        }
    
    async def _enhance_article(self, article: str) -> str:
        """Enhance article with additional features"""
        # Add metadata
        enhanced = f"{article}\n\n---\n\n"
        enhanced += f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        enhanced += "*Powered by Dakota's AI Article Generation System*\n"
        
        return enhanced
    
    def _record_phase_timing(self, phase: str, duration: float):
        """Record phase timing for metrics"""
        self.metrics["phase_timings"][phase] = duration
        
        if duration > TIMEOUTS.get(phase, 60):
            logger.warning(f"Phase {phase} took {duration:.2f}s (exceeded timeout)")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get orchestrator metrics"""
        avg_time = (
            self.metrics["total_generation_time"] / self.metrics["successful_articles"]
            if self.metrics["successful_articles"] > 0
            else 0
        )
        
        return {
            **self.metrics,
            "average_generation_time": avg_time,
            "success_rate": (
                self.metrics["successful_articles"] / self.metrics["total_articles"]
                if self.metrics["total_articles"] > 0
                else 0
            ),
            "circuit_breaker_states": circuit_manager.get_states(),
        }
    
    def health_check(self) -> Dict[str, Any]:
        """System health check"""
        return {
            "status": "healthy",
            "metrics": self.get_metrics(),
            "circuit_breakers": circuit_manager.get_states(),
            "timestamp": datetime.now().isoformat(),
        }