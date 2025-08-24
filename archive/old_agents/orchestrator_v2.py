"""Dakota Orchestrator V2 - Production-optimized with parallel execution"""

import asyncio
import os
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor

from src.models import ArticleRequest
from src.utils.logging import get_logger
from src.services.openai_connection_pool import acquire_openai_client
from src.services.kb_search_production_v2 import search_kb_production_v2, batch_search_kb_production_v2
from prometheus_client import Counter, Histogram, Gauge

from .base_agent_v2 import DakotaBaseAgentV2

logger = get_logger(__name__)

# Metrics
orchestrator_phases = Histogram('orchestrator_phase_duration_seconds', 'Phase execution time', ['phase'])
orchestrator_total = Histogram('orchestrator_total_duration_seconds', 'Total article generation time')
concurrent_agents = Gauge('orchestrator_concurrent_agents', 'Number of agents running concurrently')
phase_errors = Counter('orchestrator_phase_errors_total', 'Phase execution errors', ['phase'])


class DakotaOrchestratorV2(DakotaBaseAgentV2):
    """Production-optimized orchestrator with enhanced parallelism"""
    
    def __init__(self):
        super().__init__("orchestrator", model_override="gpt-5-nano")  # Light model for coordination
        self.phase_results = {}
        self.article_approved = False
        self.iteration_count = 0
        self.max_iterations = 2
        
        # Thread pool for CPU-bound operations
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        # Semaphores for concurrency control
        self.agent_semaphore = asyncio.Semaphore(5)  # Max 5 concurrent agents
        self.api_semaphore = asyncio.Semaphore(10)   # Max 10 concurrent API calls
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute optimized article generation workflow"""
        start_time = time.time()
        
        try:
            with orchestrator_total.time():
                self.update_status("active", "Starting optimized article generation")
                
                # Extract request
                request = task.get("request")
                if isinstance(request, dict):
                    request = ArticleRequest(**request)
                
                # Phase 1: Setup (quick, no API calls)
                with orchestrator_phases.labels(phase="setup").time():
                    setup_result = await self._phase1_setup(request)
                    if not setup_result["success"]:
                        phase_errors.labels(phase="setup").inc()
                        return self.format_response(False, error="Setup failed")
                    self.phase_results["phase1"] = setup_result["data"]
                
                # Phase 2-3: Parallel Research + Synthesis Planning
                with orchestrator_phases.labels(phase="research_synthesis").time():
                    research_synthesis_result = await self._parallel_research_and_synthesis_planning(request)
                    if not research_synthesis_result["success"]:
                        phase_errors.labels(phase="research_synthesis").inc()
                        return self.format_response(False, error="Research/synthesis failed")
                    self.phase_results["phase2_3"] = research_synthesis_result["data"]
                
                # Phase 4-5: Parallel Content Creation + Initial Analysis
                with orchestrator_phases.labels(phase="content_analysis").time():
                    content_analysis_result = await self._parallel_content_and_analysis(request)
                    if not content_analysis_result["success"]:
                        phase_errors.labels(phase="content_analysis").inc()
                        return self.format_response(False, error="Content/analysis failed")
                    self.phase_results["phase4_5"] = content_analysis_result["data"]
                
                # Phase 6: Validation (mandatory, but optimized)
                with orchestrator_phases.labels(phase="validation").time():
                    validation_result = await self._optimized_validation()
                    
                    if not validation_result["approved"] and self.iteration_count < self.max_iterations:
                        # Quick iteration
                        iteration_result = await self._fast_iteration(validation_result["issues"])
                        if iteration_result["success"]:
                            validation_result = await self._optimized_validation()
                    
                    if not validation_result["approved"]:
                        phase_errors.labels(phase="validation").inc()
                        return self.format_response(False, error="Validation failed")
                
                # Phase 7: Distribution (parallel)
                with orchestrator_phases.labels(phase="distribution").time():
                    distribution_result = await self._parallel_distribution(request)
                    if not distribution_result["success"]:
                        phase_errors.labels(phase="distribution").inc()
                        return self.format_response(False, error="Distribution failed")
                
                # Success!
                total_time = time.time() - start_time
                self.logger.info(f"✅ Article generation completed in {total_time:.2f}s")
                
                return self.format_response(True, data={
                    "output_folder": self.phase_results["phase1"]["output_dir"],
                    "files_created": self._get_created_files(),
                    "word_count": self.phase_results["phase4_5"]["word_count"],
                    "fact_checker_approved": True,
                    "sources_verified": validation_result.get("sources_verified", 0),
                    "iterations_needed": self.iteration_count,
                    "generation_time": total_time
                })
                
        except Exception as e:
            self.logger.error(f"Orchestrator error: {e}")
            phase_errors.labels(phase="unknown").inc()
            return self.format_response(False, error=str(e))
    
    async def _phase1_setup(self, request: ArticleRequest) -> Dict[str, Any]:
        """Phase 1: Quick setup without API calls"""
        try:
            topic_slug = re.sub(r'[^\w\s-]', '', request.topic.lower())
            topic_slug = re.sub(r'[-\s]+', '-', topic_slug)[:50]
            prefix = topic_slug[:15].rstrip('-')
            
            date_str = datetime.now().strftime("%Y-%m-%d")
            output_dir = f"output/{date_str}-{topic_slug}"
            os.makedirs(output_dir, exist_ok=True)
            
            return self.format_response(True, data={
                "topic": request.topic,
                "word_count": request.word_count,
                "prefix": prefix,
                "output_dir": output_dir,
                "date": date_str
            })
        except Exception as e:
            return self.format_response(False, error=str(e))
    
    async def _parallel_research_and_synthesis_planning(self, request: ArticleRequest) -> Dict[str, Any]:
        """Combined Phase 2-3: Parallel research with synthesis planning"""
        try:
            from .kb_researcher_v2 import DakotaKBResearcherV2
            from .web_researcher_v2 import DakotaWebResearcherV2
            from .research_synthesizer_v2 import DakotaResearchSynthesizerV2
            
            # Create agents
            kb_researcher = DakotaKBResearcherV2()
            web_researcher = DakotaWebResearcherV2()
            synthesizer = DakotaResearchSynthesizerV2()
            
            concurrent_agents.inc(3)
            
            # Execute all three in parallel
            async def research_and_plan():
                async with self.agent_semaphore:
                    # KB research with enhanced search
                    kb_task = kb_researcher.execute({
                        "topic": request.topic,
                        "use_batch_search": True
                    })
                    
                    # Web research
                    web_task = web_researcher.execute({
                        "topic": request.topic,
                        "max_searches": 3  # Limit for speed
                    })
                    
                    # Start synthesis planning (lightweight)
                    synthesis_plan_task = synthesizer.plan_synthesis({
                        "topic": request.topic,
                        "audience": request.audience,
                        "tone": request.tone,
                        "word_count": request.word_count
                    })
                    
                    # Wait for all
                    kb_result, web_result, synthesis_plan = await asyncio.gather(
                        kb_task, web_task, synthesis_plan_task,
                        return_exceptions=True
                    )
                    
                    # Handle exceptions
                    if isinstance(kb_result, Exception):
                        self.logger.error(f"KB research error: {kb_result}")
                        kb_result = {"success": False, "data": {"sources": []}}
                    
                    if isinstance(web_result, Exception):
                        self.logger.error(f"Web research error: {web_result}")
                        web_result = {"success": False, "data": {"sources": []}}
                    
                    # Execute synthesis with research results
                    synthesis_result = await synthesizer.execute({
                        "plan": synthesis_plan,
                        "kb_results": kb_result.get("data", {}),
                        "web_results": web_result.get("data", {})
                    })
                    
                    return {
                        "kb_result": kb_result,
                        "web_result": web_result,
                        "synthesis": synthesis_result,
                        "sources": self._combine_sources(kb_result, web_result)
                    }
            
            result = await research_and_plan()
            concurrent_agents.dec(3)
            
            return self.format_response(True, data=result)
            
        except Exception as e:
            concurrent_agents.dec(3)
            return self.format_response(False, error=str(e))
    
    async def _parallel_content_and_analysis(self, request: ArticleRequest) -> Dict[str, Any]:
        """Combined Phase 4-5: Content creation with parallel analysis"""
        try:
            from .content_writer_v2 import DakotaContentWriterV2
            from .metrics_analyzer import DakotaMetricsAnalyzer
            from .seo_specialist_v2 import DakotaSEOSpecialistV2
            
            writer = DakotaContentWriterV2()
            metrics = DakotaMetricsAnalyzer()
            seo = DakotaSEOSpecialistV2()
            
            setup_data = self.phase_results["phase1"]
            synthesis_data = self.phase_results["phase2_3"]["synthesis"]
            
            concurrent_agents.inc(3)
            
            async def create_and_analyze():
                async with self.agent_semaphore:
                    # Start content writing
                    article_path = f"{setup_data['output_dir']}/{setup_data['prefix']}-article.md"
                    
                    write_task = writer.execute({
                        "topic": request.topic,
                        "audience": request.audience,
                        "tone": request.tone,
                        "word_count": request.word_count,
                        "synthesis": synthesis_data,
                        "output_file": article_path
                    })
                    
                    # Wait for initial content
                    write_result = await write_task
                    
                    if not write_result["success"]:
                        return write_result
                    
                    # Now run analysis in parallel
                    metrics_task = metrics.execute({
                        "article_file": article_path,
                        "target_word_count": request.word_count
                    })
                    
                    seo_task = seo.execute({
                        "topic": request.topic,
                        "article_file": article_path,
                        "output_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-metadata.md",
                        "sources": self.phase_results["phase2_3"]["sources"],
                        "related_articles": self.phase_results["phase2_3"].get("kb_result", {}).get("data", {}).get("related_articles", [])
                    })
                    
                    metrics_result, seo_result = await asyncio.gather(
                        metrics_task, seo_task,
                        return_exceptions=True
                    )
                    
                    # Handle exceptions
                    if isinstance(metrics_result, Exception):
                        metrics_result = {"success": False, "data": {"word_count": 0}}
                    if isinstance(seo_result, Exception):
                        seo_result = {"success": False, "data": {}}
                    
                    return {
                        "content": write_result,
                        "metrics": metrics_result,
                        "seo": seo_result,
                        "word_count": metrics_result.get("data", {}).get("word_count", 0)
                    }
            
            result = await create_and_analyze()
            concurrent_agents.dec(3)
            
            return self.format_response(True, data=result)
            
        except Exception as e:
            concurrent_agents.dec(3)
            return self.format_response(False, error=str(e))
    
    async def _optimized_validation(self) -> Dict[str, Any]:
        """Optimized validation with parallel checks"""
        try:
            from .fact_checker_v3 import DakotaFactCheckerV3
            
            setup_data = self.phase_results["phase1"]
            article_path = f"{setup_data['output_dir']}/{setup_data['prefix']}-article.md"
            metadata_path = f"{setup_data['output_dir']}/{setup_data['prefix']}-metadata.md"
            
            # Quick template validation (no API calls)
            template_valid = await asyncio.gather(
                self._validate_article_template(article_path),
                self._validate_metadata_template(metadata_path)
            )
            
            if not all(template_valid):
                return {"approved": False, "issues": "Template validation failed"}
            
            # Fact checking with caching
            fact_checker = DakotaFactCheckerV3()  # Uses cached KB searches
            fact_result = await fact_checker.execute({
                "article_file": article_path,
                "metadata_file": metadata_path,
                "use_cache": True
            })
            
            if not fact_result["success"]:
                return {"approved": False, "issues": fact_result.get("error", "Fact checking failed")}
            
            approved = fact_result["data"].get("approved", False)
            
            if approved:
                # Update metadata checkboxes
                await self._update_metadata_verification(setup_data["prefix"])
            
            return {
                "approved": approved,
                "issues": fact_result["data"].get("issues", []) if not approved else None,
                "sources_verified": fact_result["data"].get("sources_verified", 0)
            }
            
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return {"approved": False, "issues": str(e)}
    
    async def _fast_iteration(self, issues: Any) -> Dict[str, Any]:
        """Fast iteration with minimal API calls"""
        try:
            from .iteration_manager_v2 import DakotaIterationManagerV2
            
            self.iteration_count += 1
            setup_data = self.phase_results["phase1"]
            
            manager = DakotaIterationManagerV2()
            result = await manager.execute({
                "issues": issues,
                "article_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-article.md",
                "metadata_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-metadata.md",
                "iteration_count": self.iteration_count,
                "max_iterations": self.max_iterations,
                "use_cache": True
            })
            
            return result
            
        except Exception as e:
            return self.format_response(False, error=str(e))
    
    async def _parallel_distribution(self, request: ArticleRequest) -> Dict[str, Any]:
        """Parallel distribution content creation"""
        try:
            from .social_promoter_v2 import DakotaSocialPromoterV2
            from .summary_writer_v2 import DakotaSummaryWriterV2
            
            social = DakotaSocialPromoterV2()
            summary = DakotaSummaryWriterV2()
            
            setup_data = self.phase_results["phase1"]
            
            concurrent_agents.inc(2)
            
            async def create_distribution():
                async with self.agent_semaphore:
                    social_task = social.execute({
                        "topic": request.topic,
                        "article_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-article.md",
                        "output_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-social.md"
                    })
                    
                    summary_task = summary.execute({
                        "topic": request.topic,
                        "audience": request.audience,
                        "article_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-article.md",
                        "output_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-summary.md"
                    })
                    
                    results = await asyncio.gather(
                        social_task, summary_task,
                        return_exceptions=True
                    )
                    
                    # Handle exceptions gracefully
                    social_success = not isinstance(results[0], Exception) and results[0].get("success", False)
                    summary_success = not isinstance(results[1], Exception) and results[1].get("success", False)
                    
                    return {
                        "social": social_success,
                        "summary": summary_success
                    }
            
            result = await create_distribution()
            concurrent_agents.dec(2)
            
            return self.format_response(True, data=result)
            
        except Exception as e:
            concurrent_agents.dec(2)
            return self.format_response(False, error=str(e))
    
    def _combine_sources(self, kb_result: Dict, web_result: Dict) -> List[Dict]:
        """Combine and deduplicate sources"""
        sources = []
        seen_urls = set()
        
        # Add KB sources
        if kb_result.get("success"):
            for source in kb_result.get("data", {}).get("sources", []):
                url = source.get("url", "")
                if url and url not in seen_urls:
                    sources.append(source)
                    seen_urls.add(url)
        
        # Add web sources
        if web_result.get("success"):
            for source in web_result.get("data", {}).get("sources", []):
                url = source.get("url", "")
                if url and url not in seen_urls:
                    sources.append(source)
                    seen_urls.add(url)
        
        return sources[:10]  # Limit to top 10
    
    def _get_created_files(self) -> List[str]:
        """Get list of created files"""
        setup_data = self.phase_results.get("phase1", {})
        prefix = setup_data.get("prefix", "")
        
        return [
            f"{prefix}-article.md",
            f"{prefix}-metadata.md",
            f"{prefix}-social.md",
            f"{prefix}-summary.md"
        ]
    
    async def _validate_article_template(self, article_path: str) -> bool:
        """Fast template validation"""
        try:
            with open(article_path, 'r') as f:
                content = f.read()
            
            return all([
                content.startswith("---"),
                "Key Insights at a Glance" in content,
                "Key Takeaways" in content,
                ("Conclusion" in content or "## Conclusion" in content),
                "Introduction" not in content and "Executive Summary" not in content
            ])
        except:
            return False
    
    async def _validate_metadata_template(self, metadata_path: str) -> bool:
        """Fast metadata validation"""
        try:
            with open(metadata_path, 'r') as f:
                content = f.read()
            
            source_count = content.count("**URL:**") or content.count("- URL:")
            
            return all([
                "Fact-checker approved" in content,
                "Sources and Citations" in content or "Sources & Citations" in content,
                source_count >= 5
            ])
        except:
            return False
    
    async def _update_metadata_verification(self, prefix: str) -> None:
        """Update metadata verification checkboxes"""
        try:
            setup_data = self.phase_results.get("phase1", {})
            metadata_path = f"{setup_data['output_dir']}/{prefix}-metadata.md"
            
            with open(metadata_path, 'r') as f:
                content = f.read()
            
            replacements = [
                ("[ ] All statistics verified with sources", "[x] All statistics verified with sources"),
                ("[ ] All URLs tested and working", "[x] All URLs tested and working"),
                ("[ ] All data within 12 months", "[x] All data within 12 months"),
                ("[ ] All sources authoritative", "[x] All sources authoritative"),
                ("[ ] Fact-checker approved", "[x] Fact-checker approved")
            ]
            
            for old, new in replacements:
                content = content.replace(old, new)
            
            with open(metadata_path, 'w') as f:
                f.write(content)
                
        except Exception as e:
            self.logger.error(f"Error updating metadata: {e}")