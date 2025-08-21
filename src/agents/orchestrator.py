"""
Main orchestrator agent that coordinates all teams
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import asyncio

from src.agents.multi_agent_base import BaseAgent, AgentMessage, AgentStatus, MessageType
from src.agents.team_leads import ResearchTeamLead, WritingTeamLead, QualityTeamLead, PublishingTeamLead
from src.agents.communication_broker import create_communication_broker
from src.config import DEFAULT_MODELS, RESEARCH_CONFIG
from src.models import ArticleRequest, ArticleResponse, MetadataGeneration
from src.utils.logging import get_logger

logger = get_logger(__name__)


class OrchestratorAgent(BaseAgent):
    """Main orchestrator that coordinates all team leads"""
    
    def __init__(self):
        super().__init__(
            agent_id="orchestrator_001",
            agent_type="orchestrator",
            team=None  # Orchestrator doesn't belong to a team
        )
        self.capabilities = [
            "article_generation",
            "team_coordination",
            "pipeline_management",
            "quality_assurance",
            "publication_management"
        ]
        self.model = DEFAULT_MODELS.get("orchestrator", "gpt-5")
        
        # Initialize communication broker
        self.broker = create_communication_broker(async_mode=True)
        
        # Initialize team leads
        self.research_lead = ResearchTeamLead()
        self.writing_lead = WritingTeamLead()
        self.quality_lead = QualityTeamLead()
        self.publishing_lead = PublishingTeamLead()
        
        # Register all agents with broker
        self._register_agents()
        
        # Pipeline state
        self.current_pipeline: Optional[Dict[str, Any]] = None
        self.pipeline_history: List[Dict[str, Any]] = []
    
    def _register_agents(self) -> None:
        """Register all agents with communication broker"""
        # Register orchestrator
        self.broker.register_agent(self)
        
        # Register team leads
        self.broker.register_agent(self.research_lead)
        self.broker.register_agent(self.writing_lead)
        self.broker.register_agent(self.quality_lead)
        self.broker.register_agent(self.publishing_lead)
        
        # Register sub-agents from each team
        for lead in [self.research_lead, self.writing_lead, self.quality_lead, self.publishing_lead]:
            if hasattr(lead, 'sub_agents') and isinstance(lead.sub_agents, dict):
                for agent in lead.sub_agents.values():
                    self.broker.register_agent(agent)
    
    def validate_task(self, task: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate orchestrator tasks"""
        valid_tasks = [
            "generate_article",
            "review_pipeline",
            "get_status",
            "handle_escalation",
            "emergency_stop"
        ]
        
        if task not in valid_tasks:
            return False, f"Task '{task}' not supported by Orchestrator"
        
        if task == "generate_article" and "request" not in payload:
            return False, "Missing 'request' in payload"
        
        return True, "Valid task"
    
    def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process orchestrator request"""
        task = message.task
        payload = message.payload
        
        if task == "generate_article":
            # Use nest_asyncio to handle nested event loops
            import nest_asyncio
            nest_asyncio.apply()
            result = asyncio.run(self._orchestrate_article_generation(payload["request"]))
        elif task == "review_pipeline":
            result = self._review_current_pipeline()
        elif task == "get_status":
            result = self._get_system_status()
        elif task == "handle_escalation":
            result = self._handle_escalation(payload)
        else:
            result = self._emergency_stop()
        
        return self._create_response(message, result)
    
    async def _orchestrate_article_generation(self, request: ArticleRequest) -> Dict[str, Any]:
        """Orchestrate the entire article generation pipeline"""
        self.update_status(AgentStatus.WORKING, "Starting article generation pipeline")
        
        # Initialize pipeline tracking
        pipeline_id = f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_pipeline = {
            "id": pipeline_id,
            "request": request.model_dump() if hasattr(request, 'model_dump') else request,
            "status": "in_progress",
            "phases": {},
            "start_time": datetime.now().isoformat()
        }
        
        try:
            # Start the communication broker
            broker_task = asyncio.create_task(self.broker.start())
            
            # Phase 1: Research
            research_result = await self._phase_research(request)
            self.current_pipeline["phases"]["research"] = research_result
            
            if not research_result.get("success", False):
                return self._pipeline_failed("Research phase failed", research_result)
            
            # Phase 2: Writing
            writing_result = await self._phase_writing(request, research_result)
            self.current_pipeline["phases"]["writing"] = writing_result
            
            if not writing_result.get("success", False):
                return self._pipeline_failed("Writing phase failed", writing_result)
            
            # Phase 3: Quality Check
            quality_result = await self._phase_quality_check(writing_result["article"])
            self.current_pipeline["phases"]["quality"] = quality_result
            
            if not quality_result.get("ready_for_publication", False):
                # Revision needed
                revision_result = await self._phase_revision(
                    writing_result["article"],
                    quality_result["issues_found"]
                )
                self.current_pipeline["phases"]["revision"] = revision_result
                
                # Re-check quality
                quality_result = await self._phase_quality_check(revision_result["revised_article"])
                self.current_pipeline["phases"]["quality_recheck"] = quality_result
            
            # Phase 4: Publishing Preparation
            publishing_result = await self._phase_publishing(
                quality_result.get("approved_article", writing_result["article"]),
                request
            )
            self.current_pipeline["phases"]["publishing"] = publishing_result
            
            # Stop broker
            self.broker.stop()
            
            # Complete pipeline
            self.current_pipeline["status"] = "completed"
            self.current_pipeline["end_time"] = datetime.now().isoformat()
            self.pipeline_history.append(self.current_pipeline)
            
            self.update_status(AgentStatus.COMPLETED, "Article generation complete")
            
            return {
                "success": True,
                "pipeline_id": pipeline_id,
                "article": publishing_result["final_article"],
                "metadata": publishing_result["metadata"],
                "quality_score": quality_result.get("overall_quality_score", 0),
                "phases_completed": list(self.current_pipeline["phases"].keys()),
                "total_time": self._calculate_pipeline_duration()
            }
            
        except Exception as e:
            self.broker.stop()
            return self._pipeline_failed(f"Pipeline error: {str(e)}", {"error": str(e)})
    
    async def _phase_research(self, request: ArticleRequest) -> Dict[str, Any]:
        """Research phase coordination"""
        self.update_status(AgentStatus.WORKING, "Coordinating research phase")
        
        # Send research request to research team lead
        research_msg = self.send_message(
            to_agent=self.research_lead.agent_id,
            task="comprehensive_research",
            payload={
                "topic": request.topic,
                "audience": request.audience,
                "tone": request.tone,
                "requirements": {
                    "min_sources": RESEARCH_CONFIG["min_sources"],
                    "data_freshness": RESEARCH_CONFIG.get("max_data_age_days", 180)
                }
            }
        )
        
        # Queue message
        self.broker.send_message(research_msg)
        
        # Wait for response (in real implementation would be async)
        await asyncio.sleep(0.5)  # Simulate processing time
        
        # Process response
        response = self.research_lead.receive_message(research_msg)
        
        if response:
            if not isinstance(response.payload, dict):
                raise TypeError(
                    "Research team response payload must be a dictionary, "
                    f"got {type(response.payload).__name__}"
                )
            logger.info(f"Research response received: {response.payload.get('success', False)}")
            if not response.payload.get('success', False):
                logger.error(f"Research error: {response.payload.get('error', 'Unknown error')}")
            return response.payload
        else:
            logger.warning("No response from research team")
            return {"success": False, "error": "No response from research team"}
    
    async def _phase_writing(self, request: ArticleRequest, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Writing phase coordination"""
        self.update_status(AgentStatus.WORKING, "Coordinating writing phase")
        
        # Prepare writing context
        writing_context = {
            "topic": request.topic,
            "audience": request.audience,
            "tone": request.tone,
            "word_count": request.word_count,
            "research_data": research_data,
            "style_guide": "dakota_institutional",
            "key_points": research_data.get("key_findings", []),
            "sources": research_data.get("all_sources", [])
        }
        
        # Send to writing team lead
        writing_msg = self.send_message(
            to_agent=self.writing_lead.agent_id,
            task="create_article",
            payload=writing_context
        )
        
        self.broker.send_message(writing_msg)
        await asyncio.sleep(0.5)
        
        response = self.writing_lead.receive_message(writing_msg)
        
        return response.payload if response else {"success": False, "error": "No response from writing team"}
    
    async def _phase_quality_check(self, article: str) -> Dict[str, Any]:
        """Quality check phase coordination"""
        self.update_status(AgentStatus.WORKING, "Coordinating quality check phase")
        
        # Send to quality team lead
        quality_msg = self.send_message(
            to_agent=self.quality_lead.agent_id,
            task="full_quality_check",
            payload={
                "content": article,
                "requirements": {
                    "min_quality_score": 85,
                    "fact_accuracy": 95,
                    "readability_target": 80
                }
            }
        )
        
        self.broker.send_message(quality_msg)
        await asyncio.sleep(0.5)
        
        response = self.quality_lead.receive_message(quality_msg)
        result = response.payload if response else {"success": False}
        
        # Determine if ready for publication
        result["ready_for_publication"] = (
            result.get("overall_quality_score", 0) >= 85 and
            len(result.get("issues_found", [])) == 0
        )
        
        if result["ready_for_publication"]:
            result["approved_article"] = article
        
        return result
    
    async def _phase_revision(self, article: str, issues: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Revision phase coordination"""
        self.update_status(AgentStatus.WORKING, "Coordinating revision phase")
        
        # Send back to writing team for revisions
        revision_msg = self.send_message(
            to_agent=self.writing_lead.agent_id,
            task="revise_article",
            payload={
                "article": article,
                "issues": issues,
                "revision_instructions": self._generate_revision_instructions(issues)
            }
        )
        
        self.broker.send_message(revision_msg)
        await asyncio.sleep(0.5)
        
        response = self.writing_lead.receive_message(revision_msg)
        
        return response.payload if response else {"success": False, "error": "No response from writing team"}
    
    async def _phase_publishing(self, article: str, request: ArticleRequest) -> Dict[str, Any]:
        """Publishing preparation phase"""
        self.update_status(AgentStatus.WORKING, "Coordinating publishing phase")
        
        # Send to publishing team lead
        publishing_msg = self.send_message(
            to_agent=self.publishing_lead.agent_id,
            task="prepare_for_publication",
            payload={
                "article": article,
                "metadata": {
                    "title": self._extract_title(article),
                    "topic": request.topic,
                    "audience": request.audience,
                    "author": "Dakota Team",
                    "publication_date": datetime.now().isoformat()
                },
                "distribution_channels": ["website", "email", "social_media"]
            }
        )
        
        self.broker.send_message(publishing_msg)
        await asyncio.sleep(0.5)
        
        response = self.publishing_lead.receive_message(publishing_msg)
        
        return response.payload if response else {"success": False, "error": "No response from publishing team"}
    
    def _review_current_pipeline(self) -> Dict[str, Any]:
        """Review current pipeline status"""
        if not self.current_pipeline:
            return {
                "success": True,
                "status": "No active pipeline",
                "history_count": len(self.pipeline_history)
            }
        
        return {
            "success": True,
            "pipeline": self.current_pipeline,
            "agent_statuses": self.broker.get_all_agent_statuses(),
            "message_queue_size": len(self.broker.message_queue)
        }
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            "success": True,
            "orchestrator_status": self.status.value,
            "agent_statuses": self.broker.get_all_agent_statuses(),
            "active_pipeline": self.current_pipeline is not None,
            "pipelines_completed": len(self.pipeline_history),
            "last_activity": datetime.now().isoformat()
        }
    
    def _handle_escalation(self, escalation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle escalated issues"""
        issue = escalation_data.get("issue", "Unknown issue")
        from_agent = escalation_data.get("details", {}).get("from_agent", "Unknown")
        
        # Log escalation
        logger.warning(f"Escalation from {from_agent}: {issue}")
        
        # Determine action based on issue type
        if "timeout" in issue.lower():
            action = "extending_timeout"
            resolution = "Extended timeout for agent operation"
        elif "error" in issue.lower():
            action = "error_recovery"
            resolution = "Initiated error recovery procedure"
        else:
            action = "manual_review"
            resolution = "Flagged for manual review"
        
        return {
            "success": True,
            "escalation_handled": True,
            "action_taken": action,
            "resolution": resolution,
            "timestamp": datetime.now().isoformat()
        }
    
    def _emergency_stop(self) -> Dict[str, Any]:
        """Emergency stop of all operations"""
        self.update_status(AgentStatus.ERROR, "Emergency stop initiated")
        
        # Stop broker
        self.broker.stop()
        
        # Mark pipeline as failed
        if self.current_pipeline:
            self.current_pipeline["status"] = "emergency_stopped"
            self.current_pipeline["end_time"] = datetime.now().isoformat()
            self.pipeline_history.append(self.current_pipeline)
            self.current_pipeline = None
        
        return {
            "success": True,
            "action": "emergency_stop",
            "all_operations_halted": True,
            "timestamp": datetime.now().isoformat()
        }
    
    def _pipeline_failed(self, reason: str, details: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pipeline failure"""
        self.update_status(AgentStatus.ERROR, reason)
        
        if self.current_pipeline:
            self.current_pipeline["status"] = "failed"
            self.current_pipeline["failure_reason"] = reason
            self.current_pipeline["failure_details"] = details
            self.current_pipeline["end_time"] = datetime.now().isoformat()
            self.pipeline_history.append(self.current_pipeline)
        
        return {
            "success": False,
            "error": reason,
            "details": details,
            "pipeline_id": self.current_pipeline.get("id") if self.current_pipeline else None
        }
    
    def _generate_revision_instructions(self, issues: List[Dict[str, Any]]) -> str:
        """Generate specific revision instructions from issues"""
        instructions = []
        
        for issue in issues:
            issue_type = issue.get("type", "general")
            description = issue.get("description", "")
            
            if issue_type == "accuracy":
                instructions.append(f"Correct factual error: {description}")
            elif issue_type == "readability":
                instructions.append(f"Improve readability: {description}")
            elif issue_type == "compliance":
                instructions.append(f"Address compliance issue: {description}")
            else:
                instructions.append(f"Fix: {description}")
        
        return "\n".join(instructions)
    
    def _extract_title(self, article: str) -> str:
        """Extract title from article"""
        lines = article.strip().split('\n')
        for line in lines:
            if line.strip().startswith('#') and not line.strip().startswith('##'):
                return line.strip().replace('#', '').strip()
        return "Untitled Article"
    
    def _calculate_pipeline_duration(self) -> str:
        """Calculate pipeline duration"""
        if not self.current_pipeline:
            return "Unknown"
        
        start = datetime.fromisoformat(self.current_pipeline["start_time"])
        end = datetime.fromisoformat(self.current_pipeline.get("end_time", datetime.now().isoformat()))
        duration = end - start
        
        return f"{duration.total_seconds():.2f} seconds"


def create_article_with_multi_agent_system(request: ArticleRequest) -> ArticleResponse:
    """Main entry point for multi-agent article generation"""
    orchestrator = OrchestratorAgent()
    
    # Create initial message
    message = AgentMessage(
        from_agent="system",
        to_agent=orchestrator.agent_id,
        message_type=MessageType.REQUEST,
        task="generate_article",
        payload={"request": request},
        context={},
        timestamp=datetime.now().isoformat()
    )
    
    # Process request
    response = orchestrator.process_message(message)
    
    if response.payload.get("success", False):
        # Map fields that might have different names
        metadata_dict = response.payload["metadata"].copy()
        
        # Handle field name variations
        if "target_keywords" in metadata_dict and "keywords" not in metadata_dict:
            metadata_dict["keywords"] = metadata_dict.pop("target_keywords")
        if "meta_description" in metadata_dict and "seo_description" not in metadata_dict:
            metadata_dict["seo_description"] = metadata_dict.pop("meta_description")
        
        # Ensure required fields have defaults
        metadata_dict.setdefault("description", metadata_dict.get("seo_description", ""))
        metadata_dict.setdefault("category", "Investment Insights")
        metadata_dict.setdefault("target_audience", "institutional investors")
        metadata_dict.setdefault("read_time_minutes", 7)
        metadata_dict.setdefault("key_takeaways", [])
        metadata_dict.setdefault("related_topics", [])
        metadata_dict.setdefault("seo_title", metadata_dict.get("title", ""))
        metadata_dict.setdefault("publication_date", datetime.now().strftime("%Y-%m-%d"))
        
        return ArticleResponse(
            success=True,
            article=response.payload["article"],
            metadata=MetadataGeneration(**metadata_dict),
            quality_metrics={
                "quality_score": response.payload.get("quality_score", 0),
                "phases_completed": response.payload.get("phases_completed", []),
                "generation_time": response.payload.get("total_time", "Unknown")
            }
        )
    else:
        return ArticleResponse(
            success=False,
            article="",
            metadata=MetadataGeneration(
                title="Generation Failed",
                description="Article generation failed",
                keywords=[],
                category="Error",
                target_audience="N/A",
                read_time_minutes=0,
                key_takeaways=[],
                related_topics=[],
                seo_title="Generation Failed",
                seo_description="Article generation failed",
                publication_date=datetime.now().strftime("%Y-%m-%d")
            ),
            error=response.payload.get("error", "Unknown error")
        )