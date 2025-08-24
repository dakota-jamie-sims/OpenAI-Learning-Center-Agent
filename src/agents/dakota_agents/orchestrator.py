"""Dakota Orchestrator Agent - Coordinates all phases with mandatory validation"""

import asyncio
import os
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .base_agent import DakotaBaseAgent
from src.models import ArticleRequest
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DakotaOrchestrator(DakotaBaseAgent):
    """Main orchestrator that coordinates all Dakota agents with phase tracking"""
    
    def __init__(self):
        super().__init__("orchestrator")
        self.current_phase = 0
        self.phase_results = {}
        self.article_approved = False
        self.iteration_count = 0
        self.max_iterations = 2
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute complete article generation workflow"""
        try:
            self.update_status("active", "Starting article generation workflow")
            
            # Extract article request
            request = task.get("request")
            if isinstance(request, dict):
                request = ArticleRequest(**request)
            
            # Phase 1: Setup
            self.logger.info("✅ Starting Phase 1: Topic Analysis & Setup...")
            setup_result = await self._phase1_setup(request)
            if not setup_result["success"]:
                return self.format_response(False, error="Phase 1 failed")
            self.phase_results["phase1"] = setup_result["data"]  # Store phase results
            self.logger.info("✅ Phase 1 completed. Moving to Phase 2...")
            
            # Phase 2: Parallel Research
            self.logger.info("✅ Starting Phase 2: Parallel Research...")
            research_result = await self._phase2_research(request.topic)
            if not research_result["success"]:
                return self.format_response(False, error="Phase 2 failed")
            self.phase_results["phase2"] = research_result["data"]  # Store phase results
            self.logger.info("✅ Phase 2 completed. Moving to Phase 3...")
            
            # Phase 3: Research Synthesis
            self.logger.info("✅ Starting Phase 3: Research Synthesis...")
            synthesis_result = await self._phase3_synthesis(request, research_result["data"])
            if not synthesis_result["success"]:
                return self.format_response(False, error="Phase 3 failed")
            self.logger.info("✅ Phase 3 completed. Moving to Phase 4...")
            
            # Phase 4: Content Creation
            self.logger.info("✅ Starting Phase 4: Content Creation...")
            content_result = await self._phase4_content_creation(request, synthesis_result["data"])
            if not content_result["success"]:
                return self.format_response(False, error="Phase 4 failed")
            self.logger.info("✅ Phase 4 completed. Moving to Phase 5...")
            
            # Phase 5: Parallel Analysis
            self.logger.info("✅ Starting Phase 5: Parallel Analysis...")
            analysis_result = await self._phase5_analysis(request, content_result["data"])
            if not analysis_result["success"]:
                return self.format_response(False, error="Phase 5 failed")
            self.logger.info("✅ Phase 5 completed. ENTERING MANDATORY VALIDATION (Phase 6)...")
            
            # Phase 6: MANDATORY Validation & Fact Checking
            self.logger.info("🛑 Starting Phase 6: MANDATORY Template Validation + Fact Checking...")
            validation_result = await self._phase6_validation(setup_result["data"])
            
            # Check if iteration is needed
            if not validation_result["approved"] and self.iteration_count < self.max_iterations:
                self.logger.info("❌ Fact-checker REJECTED. Initiating iteration...")
                iteration_result = await self._phase6_5_iteration(
                    validation_result["issues"],
                    setup_result["data"]
                )
                if iteration_result["success"]:
                    # Re-run validation after iteration
                    validation_result = await self._phase6_validation(setup_result["data"])
            
            if not validation_result["approved"]:
                self.logger.error("❌ Article REJECTED after all attempts")
                return self.format_response(False, error="Fact-checker rejected article")
            
            self.logger.info("✅ Fact-checker APPROVED. Updating metadata verification status...")
            await self._update_metadata_verification(setup_result["data"]["prefix"])
            self.logger.info("✅ Phase 6 completed. Moving to Phase 7...")
            
            # Phase 7: Distribution Content (ONLY if approved)
            self.logger.info("✅ Starting Phase 7: Distribution Content Creation...")
            distribution_result = await self._phase7_distribution(request, setup_result["data"])
            if not distribution_result["success"]:
                return self.format_response(False, error="Phase 7 failed")
            self.logger.info("✅ Phase 7 completed. Article generation SUCCESSFUL with fact-checker approval.")
            
            # Compile final results
            return self.format_response(True, data={
                "output_folder": setup_result["data"]["output_dir"],
                "files_created": [
                    f"{setup_result['data']['prefix']}-article.md",
                    f"{setup_result['data']['prefix']}-metadata.md",
                    f"{setup_result['data']['prefix']}-social.md",
                    f"{setup_result['data']['prefix']}-summary.md"
                ],
                "word_count": analysis_result["data"].get("word_count", 0),
                "fact_checker_approved": True,
                "sources_verified": validation_result.get("sources_verified", 0),
                "iterations_needed": self.iteration_count
            })
            
        except Exception as e:
            self.logger.error(f"Orchestrator error: {e}")
            return self.format_response(False, error=str(e))
    
    async def _phase1_setup(self, request: ArticleRequest) -> Dict[str, Any]:
        """Phase 1: Topic Analysis & Setup"""
        try:
            # Extract word count from request
            word_count = request.word_count
            
            # Create topic slug
            topic_slug = re.sub(r'[^\w\s-]', '', request.topic.lower())
            topic_slug = re.sub(r'[-\s]+', '-', topic_slug)[:50]
            
            # Create file prefix (under 15 chars for shorter names)
            prefix = topic_slug[:15].rstrip('-')
            
            # Create output directory
            date_str = datetime.now().strftime("%Y-%m-%d")
            output_dir = f"output/{date_str}-{topic_slug}"
            os.makedirs(output_dir, exist_ok=True)
            
            return self.format_response(True, data={
                "topic": request.topic,
                "word_count": word_count,
                "prefix": prefix,
                "output_dir": output_dir,
                "date": date_str
            })
            
        except Exception as e:
            return self.format_response(False, error=str(e))
    
    async def _phase2_research(self, topic: str) -> Dict[str, Any]:
        """Phase 2: Parallel Research"""
        try:
            # Import agents here to avoid circular imports
            from .kb_researcher import DakotaKBResearcher
            from .web_researcher import DakotaWebResearcher
            
            # Create research agents
            kb_researcher = DakotaKBResearcher()
            web_researcher = DakotaWebResearcher()
            
            # Run research in parallel
            self.logger.info(f"Deploying 2 subagents in parallel to research {topic}")
            
            kb_task = asyncio.create_task(
                kb_researcher.execute({"topic": topic})
            )
            web_task = asyncio.create_task(
                web_researcher.execute({"topic": topic})
            )
            
            # Wait for both to complete
            kb_result, web_result = await asyncio.gather(kb_task, web_task)
            
            # Combine results
            all_sources = []
            insights = []
            
            if kb_result["success"]:
                all_sources.extend(kb_result["data"].get("sources", []))
                insights.extend(kb_result["data"].get("insights", []))
            
            if web_result["success"]:
                all_sources.extend(web_result["data"].get("sources", []))
                insights.append(web_result["data"].get("summary", ""))
            
            return self.format_response(True, data={
                "sources": all_sources,
                "insights": insights,
                "kb_result": kb_result,
                "web_result": web_result
            })
            
        except Exception as e:
            return self.format_response(False, error=str(e))
    
    async def _phase3_synthesis(self, request: ArticleRequest, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3: Research Synthesis"""
        try:
            from .research_synthesizer import DakotaResearchSynthesizer
            
            synthesizer = DakotaResearchSynthesizer()
            result = await synthesizer.execute({
                "topic": request.topic,
                "audience": request.audience,
                "tone": request.tone,
                "word_count": request.word_count,
                "research_data": research_data
            })
            
            return result
            
        except Exception as e:
            return self.format_response(False, error=str(e))
    
    async def _phase4_content_creation(self, request: ArticleRequest, synthesis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 4: Content Creation"""
        try:
            from .content_writer import DakotaContentWriter
            
            writer = DakotaContentWriter()
            
            # Get setup data from phase 1
            setup_data = self.phase_results.get("phase1", {})
            
            result = await writer.execute({
                "topic": request.topic,
                "audience": request.audience,
                "tone": request.tone,
                "word_count": request.word_count,
                "synthesis": synthesis_data,
                "output_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-article.md"
            })
            
            # Store phase results
            self.phase_results["phase4"] = result
            
            return result
            
        except Exception as e:
            return self.format_response(False, error=str(e))
    
    async def _phase5_analysis(self, request: ArticleRequest, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 5: Parallel Analysis"""
        try:
            from .metrics_analyzer import DakotaMetricsAnalyzer
            from .seo_specialist import DakotaSEOSpecialist
            
            # Get setup data
            setup_data = self.phase_results.get("phase1", {})
            
            # Create analysis agents
            metrics_analyzer = DakotaMetricsAnalyzer()
            seo_specialist = DakotaSEOSpecialist()
            
            self.logger.info("Deploying 2 subagents in parallel for analysis")
            
            # Run analysis in parallel
            metrics_task = asyncio.create_task(
                metrics_analyzer.execute({
                    "article_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-article.md",
                    "target_word_count": request.word_count
                })
            )
            
            # Extract related articles from KB research
            related_articles = []
            kb_result = self.phase_results.get("phase2", {}).get("kb_result", {})
            if kb_result.get("success") and kb_result.get("data", {}).get("related_articles"):
                related_articles = kb_result["data"]["related_articles"]
            
            seo_task = asyncio.create_task(
                seo_specialist.execute({
                    "topic": request.topic,
                    "article_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-article.md",
                    "output_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-metadata.md",
                    "sources": self.phase_results.get("phase2", {}).get("sources", []),
                    "related_articles": related_articles
                })
            )
            
            # Wait for both
            metrics_result, seo_result = await asyncio.gather(metrics_task, seo_task)
            
            return self.format_response(True, data={
                "metrics": metrics_result["data"] if metrics_result["success"] else {},
                "seo": seo_result["data"] if seo_result["success"] else {},
                "word_count": metrics_result["data"].get("word_count", 0) if metrics_result["success"] else 0
            })
            
        except Exception as e:
            return self.format_response(False, error=str(e))
    
    async def _phase6_validation(self, setup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 6: MANDATORY Template Validation + Fact Checking"""
        try:
            # Step 6A: Template Validation
            self.logger.info("Now executing mandatory template validation...")
            
            article_path = f"{setup_data['output_dir']}/{setup_data['prefix']}-article.md"
            metadata_path = f"{setup_data['output_dir']}/{setup_data['prefix']}-metadata.md"
            
            # Validate article structure
            article_valid = await self._validate_article_template(article_path)
            metadata_valid = await self._validate_metadata_template(metadata_path)
            
            if not article_valid or not metadata_valid:
                return {
                    "approved": False,
                    "issues": "Template validation failed"
                }
            
            self.logger.info("Template validation passed. Now executing MANDATORY fact-checking...")
            
            # Step 6B: Fact Checking with true source verification
            from .fact_checker_v2 import DakotaFactCheckerV2
            
            fact_checker = DakotaFactCheckerV2()
            fact_result = await fact_checker.execute({
                "article_file": article_path,
                "metadata_file": metadata_path
            })
            
            if not fact_result["success"]:
                return {
                    "approved": False,
                    "issues": fact_result.get("error", "Fact checking failed")
                }
            
            # Check approval status
            approved = fact_result["data"].get("approved", False)
            
            return {
                "approved": approved,
                "issues": fact_result["data"].get("issues", []) if not approved else None,
                "sources_verified": fact_result["data"].get("sources_verified", 0)
            }
            
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return {
                "approved": False,
                "issues": str(e)
            }
    
    async def _validate_article_template(self, article_path: str) -> bool:
        """Validate article follows template structure"""
        try:
            with open(article_path, 'r') as f:
                content = f.read()
            
            # Check for required sections
            has_frontmatter = content.startswith("---")
            has_key_insights = "Key Insights at a Glance" in content
            has_takeaways = "Key Takeaways" in content
            has_conclusion = "Conclusion" in content or "## Conclusion" in content
            no_intro = "Introduction" not in content and "Executive Summary" not in content
            
            return all([has_frontmatter, has_key_insights, has_takeaways, 
                       has_conclusion, no_intro])
            
        except Exception as e:
            self.logger.error(f"Article validation error: {e}")
            return False
    
    async def _validate_metadata_template(self, metadata_path: str) -> bool:
        """Validate metadata follows template structure"""
        try:
            with open(metadata_path, 'r') as f:
                content = f.read()
            
            # Check for required sections
            has_fact_checker = "Fact-checker approved" in content
            has_sources = "Sources and Citations" in content or "Sources & Citations" in content
            
            # Count sources
            source_count = content.count("**URL:**") or content.count("- URL:")
            has_min_sources = source_count >= 5  # Require at least 5 sources
            
            return all([has_fact_checker, has_sources, has_min_sources])
            
        except Exception as e:
            self.logger.error(f"Metadata validation error: {e}")
            return False
    
    async def _phase6_5_iteration(self, issues: Any, setup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 6.5: Iteration (If Rejected)"""
        try:
            from .iteration_manager import DakotaIterationManager
            
            self.iteration_count += 1
            
            manager = DakotaIterationManager()
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
    
    async def _update_metadata_verification(self, prefix: str) -> None:
        """Update metadata verification checkboxes after approval"""
        try:
            setup_data = self.phase_results.get("phase1", {})
            metadata_path = f"{setup_data['output_dir']}/{prefix}-metadata.md"
            
            with open(metadata_path, 'r') as f:
                content = f.read()
            
            # Update verification checkboxes
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
    
    async def _phase7_distribution(self, request: ArticleRequest, setup_data: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 7: Distribution Content (ONLY if approved)"""
        try:
            from .social_promoter import DakotaSocialPromoter
            from .summary_writer import DakotaSummaryWriter
            
            self.logger.info("Fact-checker has APPROVED the article. Now creating distribution content...")
            
            # Create distribution agents
            social_promoter = DakotaSocialPromoter()
            summary_writer = DakotaSummaryWriter()
            
            self.logger.info("Deploying 2 subagents in parallel to create distribution content")
            
            # Run in parallel
            social_task = asyncio.create_task(
                social_promoter.execute({
                    "topic": request.topic,
                    "article_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-article.md",
                    "output_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-social.md"
                })
            )
            
            summary_task = asyncio.create_task(
                summary_writer.execute({
                    "topic": request.topic,
                    "audience": request.audience,
                    "article_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-article.md",
                    "output_file": f"{setup_data['output_dir']}/{setup_data['prefix']}-summary.md"
                })
            )
            
            # Wait for both
            social_result, summary_result = await asyncio.gather(social_task, summary_task)
            
            return self.format_response(True, data={
                "social": social_result["success"],
                "summary": summary_result["success"]
            })
            
        except Exception as e:
            return self.format_response(False, error=str(e))