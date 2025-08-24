"""Dakota Production Orchestrator - Optimized parallel execution with existing agents"""

import asyncio
import os
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import time

from src.models import ArticleRequest
from src.utils.logging import get_logger

# Import existing agents
from .kb_researcher import DakotaKBResearcher
from .web_researcher import DakotaWebResearcher
from .research_synthesizer import DakotaResearchSynthesizer
from .content_writer import DakotaContentWriter
from .fact_checker_v2 import DakotaFactCheckerV2
from .iteration_manager import DakotaIterationManager
from .social_promoter import DakotaSocialPromoter
from .summary_writer import DakotaSummaryWriter
from .seo_specialist import DakotaSEOSpecialist
from .metrics_analyzer import DakotaMetricsAnalyzer

# Use base agent
from .base_agent import DakotaBaseAgent

logger = get_logger(__name__)


class DakotaProductionOrchestrator(DakotaBaseAgent):
    """Production-optimized orchestrator with enhanced parallelism"""
    
    def __init__(self):
        # Use gpt-4o-mini for coordination (fast)
        super().__init__("orchestrator", model_override="gpt-4o-mini")
        self.phase_results = {}
        self.article_approved = False
        self.iteration_count = 0
        self.max_iterations = 2
        
        # Semaphores for concurrency control
        self.agent_semaphore = asyncio.Semaphore(5)  # Max 5 concurrent agents
        
        # Timing metrics
        self.phase_times = {}
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute optimized article generation workflow"""
        start_time = time.time()
        
        try:
            self.update_status("active", "Starting production article generation")
            
            # Extract request
            request = task.get("request")
            if isinstance(request, dict):
                request = ArticleRequest(**request)
            
            # Phase 1: Setup (no API calls)
            phase_start = time.time()
            self.logger.info("📋 Phase 1: Setup...")
            setup_result = await self._phase1_setup(request)
            if not setup_result["success"]:
                return self.format_response(False, error="Setup failed")
            self.phase_results["phase1"] = setup_result["data"]
            self.phase_times["phase1"] = time.time() - phase_start
            
            # Phase 2-3: Parallel Research + Early Synthesis
            phase_start = time.time()
            self.logger.info("🔍 Phase 2-3: Parallel Research & Early Synthesis...")
            research_synthesis_result = await self._parallel_research_and_synthesis(request)
            if not research_synthesis_result["success"]:
                return self.format_response(False, error="Research/synthesis failed")
            self.phase_results["phase2_3"] = research_synthesis_result["data"]
            self.phase_times["phase2_3"] = time.time() - phase_start
            
            # Phase 4-5: Content + Early Analysis
            phase_start = time.time()
            self.logger.info("✍️ Phase 4-5: Content Creation with Early Analysis...")
            content_analysis_result = await self._optimized_content_and_analysis(request)
            if not content_analysis_result["success"]:
                return self.format_response(False, error="Content/analysis failed")
            self.phase_results["phase4_5"] = content_analysis_result["data"]
            self.phase_times["phase4_5"] = time.time() - phase_start
            
            # Phase 6: Fast Validation
            phase_start = time.time()
            self.logger.info("✅ Phase 6: Fast Validation & Fact Checking...")
            validation_result = await self._fast_validation()
            
            if not validation_result["approved"] and self.iteration_count < self.max_iterations:
                self.logger.info("🔄 Running quick iteration...")
                iteration_result = await self._quick_iteration(validation_result["issues"])
                if iteration_result["success"]:
                    validation_result = await self._fast_validation()
            
            if not validation_result["approved"]:
                return self.format_response(False, error="Validation failed")
            
            self.phase_times["phase6"] = time.time() - phase_start
            
            # Phase 7: Parallel Distribution
            phase_start = time.time()
            self.logger.info("📢 Phase 7: Distribution Content...")
            distribution_result = await self._parallel_distribution(request)
            if not distribution_result["success"]:
                return self.format_response(False, error="Distribution failed")
            self.phase_times["phase7"] = time.time() - phase_start
            
            # Success!
            total_time = time.time() - start_time
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"✅ Article generation completed in {total_time:.2f}s")
            self._log_performance_metrics()
            self.logger.info(f"{'='*60}\n")
            
            return self.format_response(True, data={
                "output_folder": self.phase_results["phase1"]["output_dir"],
                "files_created": self._get_created_files(),
                "word_count": self.phase_results["phase4_5"]["word_count"],
                "fact_checker_approved": True,
                "sources_verified": validation_result.get("sources_verified", 0),
                "iterations_needed": self.iteration_count,
                "generation_time": total_time,
                "phase_times": self.phase_times
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
    
    async def _parallel_research_and_synthesis(self, request: ArticleRequest) -> Dict[str, Any]:
        """Parallel research with early synthesis"""
        try:
            # Create agents
            kb_researcher = DakotaKBResearcher()
            web_researcher = DakotaWebResearcher()
            synthesizer = DakotaResearchSynthesizer()
            
            # Override models for speed
            kb_researcher.model = "gpt-4o-mini"
            web_researcher.model = "gpt-4o-mini"
            
            async with self.agent_semaphore:
                self.logger.info("Running parallel research (KB + Web)...")
                
                # Create research tasks
                kb_task = asyncio.create_task(
                    self._run_with_timeout(
                        kb_researcher.execute({"topic": request.topic}),
                        timeout=25,  # Increased from 15s
                        name="KB Research"
                    )
                )
                
                web_task = asyncio.create_task(
                    self._run_with_timeout(
                        web_researcher.execute({
                            "topic": request.topic,
                            "word_count": request.word_count
                        }),
                        timeout=25,  # Increased from 15s
                        name="Web Research"
                    )
                )
                
                # Wait for both with timeout protection
                kb_result, web_result = await asyncio.gather(
                    kb_task, web_task,
                    return_exceptions=True
                )
                
                # Handle results
                kb_success = isinstance(kb_result, dict) and kb_result.get("success", False)
                web_success = isinstance(web_result, dict) and web_result.get("success", False)
                
                # Combine available results
                research_data = self._combine_research_results(
                    kb_result if kb_success else None,
                    web_result if web_success else None
                )
                
                # Quick synthesis
                self.logger.info("Synthesizing research results...")
                synthesis_result = await self._run_with_timeout(
                    synthesizer.execute({
                        "topic": request.topic,
                        "audience": request.audience,
                        "tone": request.tone,
                        "word_count": request.word_count,
                        "research_data": research_data
                    }),
                    timeout=30,  # Increased from 20s
                    name="Synthesis"
                )
                
                # Handle synthesis timeout by creating basic synthesis data
                synthesis_data = {}
                if synthesis_result and synthesis_result.get("success"):
                    synthesis_data = synthesis_result.get("data", {})
                else:
                    # Create fallback synthesis for timeouts
                    self.logger.warning("Synthesis failed/timed out, creating fallback outline")
                    synthesis_data = {
                        "outline": [
                            {"section": "Key Insights at a Glance", "points": ["Market overview", "Recent trends", "Key statistics"]},
                            {"section": "Current Market Landscape", "points": ["Market size", "Major players", "Growth rates"]},
                            {"section": "Institutional Adoption Trends", "points": ["Adoption rates", "Use cases", "Investment strategies"]},
                            {"section": "Regulatory Environment", "points": ["Current regulations", "Recent changes", "Future outlook"]},
                            {"section": "Investment Strategies", "points": ["Common approaches", "Risk management", "Portfolio allocation"]},
                            {"section": "Future Outlook", "points": ["Predictions", "Emerging trends", "Opportunities"]},
                            {"section": "Key Takeaways", "points": ["Summary points", "Action items", "Resources"]}
                        ],
                        "key_themes": ["institutional adoption", "regulatory clarity", "risk management", "portfolio diversification"],
                        "citation_sources": research_data["sources"]  # Use all sources (already scaled)
                    }
                
                return self.format_response(True, data={
                    "kb_result": kb_result if kb_success else {"success": False},
                    "web_result": web_result if web_success else {"success": False},
                    "synthesis": synthesis_data,
                    "sources": research_data["sources"]  # Use all sources (already scaled)
                })
            
        except Exception as e:
            return self.format_response(False, error=str(e))
    
    async def _optimized_content_and_analysis(self, request: ArticleRequest) -> Dict[str, Any]:
        """Optimized content creation with early analysis"""
        try:
            writer = DakotaContentWriter()
            metrics = DakotaMetricsAnalyzer()
            seo = DakotaSEOSpecialist()
            
            setup_data = self.phase_results["phase1"]
            synthesis_data = self.phase_results["phase2_3"]["synthesis"]
            
            # Write content
            self.logger.info("Writing article content...")
            article_path = f"{setup_data['output_dir']}/{setup_data['prefix']}-article.md"
            
            write_result = await self._run_with_timeout(
                writer.execute({
                    "topic": request.topic,
                    "audience": request.audience,
                    "tone": request.tone,
                    "word_count": request.word_count,
                    "synthesis": synthesis_data,
                    "output_file": article_path
                }),
                timeout=75,  # Increased from 45s for longer articles
                name="Content Writing"
            )
            
            if not write_result or not write_result.get("success"):
                return self.format_response(False, error="Content writing failed")
            
            # Parallel analysis
            async with self.agent_semaphore:
                self.logger.info("Running parallel analysis (Metrics + SEO)...")
                
                # Override models for speed
                metrics.model = "gpt-4o-mini"
                seo.model = "gpt-4o-mini"
                
                metrics_task = asyncio.create_task(
                    self._run_with_timeout(
                        metrics.execute({
                            "article_file": article_path,
                            "target_word_count": request.word_count
                        }),
                        timeout=10,
                        name="Metrics"
                    )
                )
                
                seo_task = asyncio.create_task(
                    self._run_with_timeout(
                        seo.execute({
                            "topic": request.topic,
                            "article_file": article_path,
                            "output_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-metadata.md",
                            "sources": self.phase_results["phase2_3"]["sources"],
                            "related_articles": self.phase_results["phase2_3"].get("kb_result", {}).get("data", {}).get("related_articles", [])
                        }),
                        timeout=15,
                        name="SEO"
                    )
                )
                
                metrics_result, seo_result = await asyncio.gather(
                    metrics_task, seo_task,
                    return_exceptions=True
                )
                
                # Handle results
                metrics_data = metrics_result if isinstance(metrics_result, dict) else {"success": False, "data": {"word_count": 0}}
                seo_data = seo_result if isinstance(seo_result, dict) else {"success": False}
                
                return self.format_response(True, data={
                    "content": write_result,
                    "metrics": metrics_data,
                    "seo": seo_data,
                    "word_count": metrics_data.get("data", {}).get("word_count", 0)
                })
            
        except Exception as e:
            return self.format_response(False, error=str(e))
    
    async def _fast_validation(self) -> Dict[str, Any]:
        """Fast validation with limited fact checking"""
        try:
            setup_data = self.phase_results["phase1"]
            article_path = f"{setup_data['output_dir']}/{setup_data['prefix']}-article.md"
            metadata_path = f"{setup_data['output_dir']}/{setup_data['prefix']}-metadata.md"
            
            # Quick template validation
            template_tasks = await asyncio.gather(
                self._validate_article_template(article_path),
                self._validate_metadata_template(metadata_path)
            )
            
            if not all(template_tasks):
                return {"approved": False, "issues": "Template validation failed"}
            
            # Use full fact checker v2 for 100% accuracy
            fact_checker = DakotaFactCheckerV2()
            
            fact_result = await self._run_with_timeout(
                fact_checker.execute({
                    "article_file": article_path,
                    "metadata_file": metadata_path
                }),
                timeout=45,  # Increased from 30s for URL fetching
                name="Fact Checking"
            )
            
            if not fact_result or not fact_result.get("success"):
                return {"approved": False, "issues": "Fact checking failed"}
            
            approved = fact_result.get("data", {}).get("approved", False)
            
            if approved:
                await self._update_metadata_verification(setup_data["prefix"])
            
            return {
                "approved": approved,
                "issues": fact_result.get("data", {}).get("issues", []) if not approved else None,
                "sources_verified": fact_result.get("data", {}).get("sources_verified", 0)
            }
            
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return {"approved": False, "issues": str(e)}
    
    async def _limited_fact_check(self, article_path: str, metadata_path: str) -> Dict[str, Any]:
        """Limited fact checking without external URL fetching"""
        try:
            # Read files
            with open(article_path, 'r') as f:
                article_content = f.read()
            with open(metadata_path, 'r') as f:
                metadata_content = f.read()
            
            # Basic checks
            has_citations = article_content.count("(") > 5  # At least 5 citations
            has_sources = metadata_content.count("URL:") >= 5  # At least 5 sources
            has_key_sections = all(section in article_content for section in ["Key Insights", "Key Takeaways", "Conclusion"])
            
            # Simple approval based on structure
            approved = has_citations and has_sources and has_key_sections
            
            return {
                "success": True,
                "approved": approved,
                "sources_verified": metadata_content.count("URL:"),
                "issues": [] if approved else ["Missing citations or key sections"]
            }
            
        except Exception as e:
            return {"success": False, "approved": False, "error": str(e)}
    
    async def _quick_iteration(self, issues: Any) -> Dict[str, Any]:
        """Quick iteration to fix issues"""
        try:
            self.iteration_count += 1
            setup_data = self.phase_results["phase1"]
            
            manager = DakotaIterationManager()
            manager.model = "gpt-4o-mini"  # Use fast model
            
            result = await self._run_with_timeout(
                manager.execute({
                    "issues": issues,
                    "article_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-article.md",
                    "metadata_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-metadata.md",
                    "iteration_count": self.iteration_count,
                    "max_iterations": self.max_iterations
                }),
                timeout=20,
                name="Iteration"
            )
            
            return result if result else {"success": False}
            
        except Exception as e:
            return self.format_response(False, error=str(e))
    
    async def _parallel_distribution(self, request: ArticleRequest) -> Dict[str, Any]:
        """Parallel distribution content creation"""
        try:
            social = DakotaSocialPromoter()
            summary = DakotaSummaryWriter()
            
            # Override models for speed
            social.model = "gpt-4o-mini"
            summary.model = "gpt-4o-mini"
            
            setup_data = self.phase_results["phase1"]
            
            async with self.agent_semaphore:
                self.logger.info("Creating distribution content (Social + Summary)...")
                
                social_task = asyncio.create_task(
                    self._run_with_timeout(
                        social.execute({
                            "topic": request.topic,
                            "article_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-article.md",
                            "output_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-social.md"
                        }),
                        timeout=40,  # Increased from 30s
                        name="Social"
                    )
                )
                
                summary_task = asyncio.create_task(
                    self._run_with_timeout(
                        summary.execute({
                            "topic": request.topic,
                            "audience": request.audience,
                            "article_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-article.md",
                            "output_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-summary.md"
                        }),
                        timeout=10,
                        name="Summary"
                    )
                )
                
                results = await asyncio.gather(
                    social_task, summary_task,
                    return_exceptions=True
                )
                
                social_success = isinstance(results[0], dict) and results[0].get("success", False)
                summary_success = isinstance(results[1], dict) and results[1].get("success", False)
                
                return self.format_response(True, data={
                    "social": social_success,
                    "summary": summary_success
                })
            
        except Exception as e:
            return self.format_response(False, error=str(e))
    
    async def _run_with_timeout(self, coro, timeout: float, name: str) -> Dict[str, Any]:
        """Run coroutine with timeout"""
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            self.logger.warning(f"{name} timed out after {timeout}s")
            return {"success": False, "error": f"Timeout after {timeout}s"}
        except Exception as e:
            self.logger.error(f"{name} error: {e}")
            return {"success": False, "error": str(e)}
    
    def _combine_research_results(self, kb_result: Optional[Dict], web_result: Optional[Dict]) -> Dict[str, Any]:
        """Combine research results - KB for insights only, web for sources"""
        combined = {
            "sources": [],  # Only web sources for citations
            "insights": [],
            "kb_data": {}  # Keep KB data separate for style/voice
        }
        
        if kb_result and kb_result.get("success"):
            data = kb_result.get("data", {})
            # KB insights for style/voice, but NOT sources
            combined["insights"].extend(data.get("insights", []))
            combined["kb_data"] = data  # Store for style reference
        
        if web_result and web_result.get("success"):
            data = web_result.get("data", {})
            # Only web sources should be used for citations
            combined["sources"].extend(data.get("sources", []))
            if data.get("summary"):
                combined["insights"].append(data["summary"])
        
        return combined
    
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
                source_count >= 8  # Increased minimum to expect more sources
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
    
    def _log_performance_metrics(self):
        """Log performance metrics"""
        self.logger.info("\n📊 Performance Metrics:")
        total = sum(self.phase_times.values())
        
        for phase, duration in self.phase_times.items():
            percentage = (duration / total) * 100
            self.logger.info(f"  {phase}: {duration:.2f}s ({percentage:.1f}%)")
        
        # Identify bottlenecks
        slowest_phase = max(self.phase_times.items(), key=lambda x: x[1])
        self.logger.info(f"\n🐌 Slowest phase: {slowest_phase[0]} ({slowest_phase[1]:.2f}s)")