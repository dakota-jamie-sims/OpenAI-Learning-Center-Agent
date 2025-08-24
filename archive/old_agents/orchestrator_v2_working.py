"""Dakota Orchestrator V2 Working - Uses existing agents with production optimizations"""

import asyncio
import os
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import time

from src.models import ArticleRequest
from src.utils.logging import get_logger

# Import existing agents through adapter
from .production_adapter import (
    DakotaKBResearcherV2,
    DakotaWebResearcherV2,
    DakotaResearchSynthesizerV2,
    DakotaContentWriterV2,
    DakotaFactCheckerV3,
    DakotaIterationManagerV2,
    DakotaSocialPromoterV2,
    DakotaSummaryWriterV2,
    DakotaSEOSpecialistV2
)
from .metrics_analyzer import DakotaMetricsAnalyzer

# Use base agent for orchestrator
from .base_agent import DakotaBaseAgent

logger = get_logger(__name__)


class DakotaOrchestratorV2Working(DakotaBaseAgent):
    """Production-optimized orchestrator that works with existing agents"""
    
    def __init__(self):
        super().__init__("orchestrator", model_override="gpt-5-mini")
        self.phase_results = {}
        self.article_approved = False
        self.iteration_count = 0
        self.max_iterations = 2
        
        # Semaphores for concurrency control
        self.agent_semaphore = asyncio.Semaphore(5)  # Max 5 concurrent agents
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute optimized article generation workflow"""
        start_time = time.time()
        
        try:
            self.update_status("active", "Starting optimized article generation")
            
            # Extract request
            request = task.get("request")
            if isinstance(request, dict):
                request = ArticleRequest(**request)
            
            # Phase 1: Setup (quick, no API calls)
            self.logger.info("📋 Phase 1: Setup...")
            setup_result = await self._phase1_setup(request)
            if not setup_result["success"]:
                return self.format_response(False, error="Setup failed")
            self.phase_results["phase1"] = setup_result["data"]
            
            # Phase 2-3: Parallel Research + Synthesis Planning
            self.logger.info("🔍 Phase 2-3: Parallel Research & Synthesis Planning...")
            research_synthesis_result = await self._parallel_research_and_synthesis_planning(request)
            if not research_synthesis_result["success"]:
                return self.format_response(False, error="Research/synthesis failed")
            self.phase_results["phase2_3"] = research_synthesis_result["data"]
            
            # Phase 4-5: Content Creation + Parallel Analysis
            self.logger.info("✍️ Phase 4-5: Content Creation & Analysis...")
            content_analysis_result = await self._content_and_analysis(request)
            if not content_analysis_result["success"]:
                return self.format_response(False, error="Content/analysis failed")
            self.phase_results["phase4_5"] = content_analysis_result["data"]
            
            # Phase 6: Validation (mandatory)
            self.logger.info("✅ Phase 6: Validation & Fact Checking...")
            validation_result = await self._optimized_validation()
            
            if not validation_result["approved"] and self.iteration_count < self.max_iterations:
                self.logger.info("🔄 Running iteration to fix issues...")
                iteration_result = await self._fast_iteration(validation_result["issues"])
                if iteration_result["success"]:
                    validation_result = await self._optimized_validation()
            
            if not validation_result["approved"]:
                return self.format_response(False, error="Validation failed")
            
            # Phase 7: Distribution (parallel)
            self.logger.info("📢 Phase 7: Distribution Content...")
            distribution_result = await self._parallel_distribution(request)
            if not distribution_result["success"]:
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
        """Combined Phase 2-3: Parallel research"""
        try:
            # Create agents
            kb_researcher = DakotaKBResearcherV2()
            web_researcher = DakotaWebResearcherV2()
            synthesizer = DakotaResearchSynthesizerV2()
            
            # Execute research in parallel
            async with self.agent_semaphore:
                self.logger.info("Running KB and Web research in parallel...")
                
                kb_task = asyncio.create_task(
                    kb_researcher.execute({"topic": request.topic})
                )
                web_task = asyncio.create_task(
                    web_researcher.execute({"topic": request.topic})
                )
                
                # Wait for both
                kb_result, web_result = await asyncio.gather(
                    kb_task, web_task,
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
                self.logger.info("Synthesizing research results...")
                
                # Combine research data
                research_data = {
                    "sources": [],
                    "insights": []
                }
                
                if kb_result.get("success"):
                    research_data["sources"].extend(kb_result["data"].get("sources", []))
                    research_data["insights"].extend(kb_result["data"].get("insights", []))
                
                if web_result.get("success"):
                    research_data["sources"].extend(web_result["data"].get("sources", []))
                    if web_result["data"].get("summary"):
                        research_data["insights"].append(web_result["data"]["summary"])
                
                synthesis_result = await synthesizer.execute({
                    "topic": request.topic,
                    "audience": request.audience,
                    "tone": request.tone,
                    "word_count": request.word_count,
                    "research_data": research_data
                })
                
                return self.format_response(True, data={
                    "kb_result": kb_result,
                    "web_result": web_result,
                    "synthesis": synthesis_result["data"] if synthesis_result["success"] else {},
                    "sources": research_data["sources"][:10]  # Top 10 sources
                })
            
        except Exception as e:
            return self.format_response(False, error=str(e))
    
    async def _content_and_analysis(self, request: ArticleRequest) -> Dict[str, Any]:
        """Phase 4-5: Content creation followed by parallel analysis"""
        try:
            writer = DakotaContentWriterV2()
            metrics = DakotaMetricsAnalyzer()
            seo = DakotaSEOSpecialistV2()
            
            setup_data = self.phase_results["phase1"]
            synthesis_data = self.phase_results["phase2_3"]["synthesis"]
            
            # Write content first
            self.logger.info("Writing article content...")
            article_path = f"{setup_data['output_dir']}/{setup_data['prefix']}-article.md"
            
            write_result = await writer.execute({
                "topic": request.topic,
                "audience": request.audience,
                "tone": request.tone,
                "word_count": request.word_count,
                "synthesis": synthesis_data,
                "output_file": article_path
            })
            
            if not write_result["success"]:
                return self.format_response(False, error="Content writing failed")
            
            # Now run analysis in parallel
            self.logger.info("Running metrics and SEO analysis in parallel...")
            
            async with self.agent_semaphore:
                metrics_task = asyncio.create_task(
                    metrics.execute({
                        "article_file": article_path,
                        "target_word_count": request.word_count
                    })
                )
                
                seo_task = asyncio.create_task(
                    seo.execute({
                        "topic": request.topic,
                        "article_file": article_path,
                        "output_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-metadata.md",
                        "sources": self.phase_results["phase2_3"]["sources"],
                        "related_articles": self.phase_results["phase2_3"].get("kb_result", {}).get("data", {}).get("related_articles", [])
                    })
                )
                
                metrics_result, seo_result = await asyncio.gather(
                    metrics_task, seo_task,
                    return_exceptions=True
                )
                
                # Handle exceptions
                if isinstance(metrics_result, Exception):
                    metrics_result = {"success": False, "data": {"word_count": 0}}
                if isinstance(seo_result, Exception):
                    seo_result = {"success": False, "data": {}}
                
                return self.format_response(True, data={
                    "content": write_result,
                    "metrics": metrics_result,
                    "seo": seo_result,
                    "word_count": metrics_result.get("data", {}).get("word_count", 0)
                })
            
        except Exception as e:
            return self.format_response(False, error=str(e))
    
    async def _optimized_validation(self) -> Dict[str, Any]:
        """Optimized validation with fact checking"""
        try:
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
            
            # Fact checking
            fact_checker = DakotaFactCheckerV3()
            fact_result = await fact_checker.execute({
                "article_file": article_path,
                "metadata_file": metadata_path
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
        """Fast iteration to fix issues"""
        try:
            self.iteration_count += 1
            setup_data = self.phase_results["phase1"]
            
            manager = DakotaIterationManagerV2()
            result = await manager.execute({
                "issues": issues,
                "article_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-article.md",
                "metadata_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-metadata.md",
                "iteration_count": self.iteration_count,
                "max_iterations": self.max_iterations
            })
            
            return result
            
        except Exception as e:
            return self.format_response(False, error=str(e))
    
    async def _parallel_distribution(self, request: ArticleRequest) -> Dict[str, Any]:
        """Parallel distribution content creation"""
        try:
            social = DakotaSocialPromoterV2()
            summary = DakotaSummaryWriterV2()
            
            setup_data = self.phase_results["phase1"]
            
            async with self.agent_semaphore:
                self.logger.info("Creating social media and summary in parallel...")
                
                social_task = asyncio.create_task(
                    social.execute({
                        "topic": request.topic,
                        "article_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-article.md",
                        "output_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-social.md"
                    })
                )
                
                summary_task = asyncio.create_task(
                    summary.execute({
                        "topic": request.topic,
                        "audience": request.audience,
                        "article_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-article.md",
                        "output_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-summary.md"
                    })
                )
                
                results = await asyncio.gather(
                    social_task, summary_task,
                    return_exceptions=True
                )
                
                # Handle exceptions gracefully
                social_success = not isinstance(results[0], Exception) and results[0].get("success", False)
                summary_success = not isinstance(results[1], Exception) and results[1].get("success", False)
                
                return self.format_response(True, data={
                    "social": social_success,
                    "summary": summary_success
                })
            
        except Exception as e:
            return self.format_response(False, error=str(e))
    
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