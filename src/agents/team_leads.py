"""
Team lead agents that coordinate sub-agents
"""
from typing import Dict, Any, List, Tuple, Optional
import asyncio
from datetime import datetime
import json

from src.agents.multi_agent_base import BaseAgent, AgentMessage, AgentStatus, MessageType
from src.agents.research_agents import WebResearchAgent, KnowledgeBaseAgent, DataValidationAgent
from src.agents.writing_agents import ContentWriterAgent, StyleEditorAgent, CitationAgent
from src.agents.quality_agents import FactCheckerAgent, ComplianceAgent, QualityAssuranceAgent
from src.config import DEFAULT_MODELS
from src.utils.logging import get_logger
from src.models import ResearchResult

logger = get_logger(__name__)


def _summarize_research(research_result: Dict[str, Any], max_chars: int = 1500) -> Dict[str, Any]:
    """Create a compact summary of research for writing phase.

    Extracts the synthesis text and the most relevant sources while ensuring
    the returned context stays within character limits to avoid token issues.
    """
    if not isinstance(research_result, dict):
        return {"synthesis": "", "sources": []}

    synthesis = research_result.get("synthesis", "")
    if isinstance(synthesis, dict):
        synthesis_text = json.dumps(synthesis, ensure_ascii=False)
    else:
        synthesis_text = str(synthesis)
    synthesis_text = synthesis_text.strip()
    if len(synthesis_text) > max_chars:
        synthesis_text = synthesis_text[:max_chars]

    sources = research_result.get("sources", [])
    if isinstance(sources, list):
        try:
            sources = sorted(
                sources, key=lambda s: s.get("credibility_score", 0), reverse=True
            )
        except Exception:
            pass
        top_sources = [
            {"title": s.get("title", ""), "url": s.get("url", ""), "date": s.get("date", "")}
            for s in sources[:5]
        ]
    else:
        top_sources = []

    return {"synthesis": synthesis_text, "sources": top_sources}


class ResearchTeamLead(BaseAgent):
    """Lead agent for research team coordination"""
    
    def __init__(self):
        super().__init__(
            agent_id="research_team_lead",
            agent_type="team_lead",
            team="research"
        )
        self.capabilities = [
            "coordinate_research",
            "synthesize_findings",
            "prioritize_sources",
            "manage_researchers",
            "quality_control"
        ]
        self.model = DEFAULT_MODELS.get("orchestrator", "gpt-5")
        
        # Initialize sub-agents
        self.web_researcher = WebResearchAgent()
        self.kb_researcher = KnowledgeBaseAgent()
        self.data_validator = DataValidationAgent()
        
        self.sub_agents = {
            "web_researcher": self.web_researcher,
            "kb_researcher": self.kb_researcher,
            "data_validator": self.data_validator
        }
    
    def validate_task(self, task: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate research team tasks"""
        valid_tasks = [
            "comprehensive_research",
            "validate_article",
            "find_sources",
            "fact_check_content",
            "research_synthesis"
        ]
        
        if task not in valid_tasks:
            return False, f"Task '{task}' not supported by ResearchTeamLead"
        
        return True, "Valid task"
    
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process research coordination request"""
        task = message.task
        payload = message.payload

        if task == "comprehensive_research":
            result_model = await self._coordinate_comprehensive_research_async(payload)
            result = result_model.model_dump()
        elif task == "validate_article":
            result = self._coordinate_article_validation(payload)
        elif task == "find_sources":
            result = self._coordinate_source_finding(payload)
        elif task == "fact_check_content":
            result = self._coordinate_fact_checking(payload)
        else:
            result = self._synthesize_research(payload)

        return self._create_response(message, result)
    
    def _coordinate_comprehensive_research(self, payload: Dict[str, Any]) -> ResearchResult:
        """Backward compatibility wrapper - calls async version"""
        import nest_asyncio
        nest_asyncio.apply()
        return asyncio.run(self._coordinate_comprehensive_research_async(payload))

    async def _coordinate_comprehensive_research_async(self, payload: Dict[str, Any]) -> ResearchResult:
        """Coordinate comprehensive research across all sub-agents in parallel"""
        topic = payload.get("topic", "")
        requirements = payload.get("requirements", {})
        
        logger.info(f"ResearchTeamLead: Starting parallel research for topic: {topic}")
        self.update_status(AgentStatus.WORKING, f"Researching: {topic}")
        
        # Phase 1: Parallel research - ALL THREE SEARCHES RUN SIMULTANEOUSLY!
        # Create messages
        web_msg = self.delegate_task(
            "web_researcher",
            "research_topic",
            {"query": topic}
        )
        kb_msg = self.delegate_task(
            "kb_researcher",  
            "search_kb",
            {"query": topic}
        )
        dakota_msg = self.delegate_task(
            "kb_researcher",
            "find_dakota_insights",
            {"query": topic}
        )
        
        # Execute all searches simultaneously with timeout protection
        web_task = asyncio.wait_for(
            asyncio.to_thread(self.web_researcher.receive_message, web_msg), timeout=15
        )
        kb_task = asyncio.wait_for(
            asyncio.to_thread(self.kb_researcher.receive_message, kb_msg), timeout=10
        )
        dakota_task = asyncio.wait_for(
            asyncio.to_thread(self.kb_researcher.receive_message, dakota_msg), timeout=10
        )

        # Wait for all to complete
        web_response = kb_response = dakota_response = None
        try:
            web_response, kb_response, dakota_response = await asyncio.gather(
                web_task,
                kb_task,
                dakota_task,
                return_exceptions=True,
            )
        except Exception as e:
            logger.error(f"Error in parallel research: {e}")

        def _error_response(agent: str, task: str, error: str) -> AgentMessage:
            """Create a standardized error response message."""
            return AgentMessage(
                from_agent=agent,
                to_agent="research_lead",
                message_type=MessageType.RESPONSE,
                task=task,
                payload={"success": False, "error": error},
                context={},
                timestamp=datetime.now().isoformat(),
            )

        # Create fallback responses for any searches that failed or weren't executed
        if web_response is None or isinstance(web_response, Exception):
            err = str(web_response) if isinstance(web_response, Exception) else "Web search failed"
            web_response = _error_response("web_researcher", "response_search_web", err)
        if kb_response is None or isinstance(kb_response, Exception):
            err = str(kb_response) if isinstance(kb_response, Exception) else "KB search failed"
            kb_response = _error_response("kb_researcher", "response_search_kb", err)
        if dakota_response is None or isinstance(dakota_response, Exception):
            err = (
                str(dakota_response)
                if isinstance(dakota_response, Exception)
                else "Dakota search failed"
            )
            dakota_response = _error_response(
                "kb_researcher", "response_find_dakota_insights", err
            )
        
        # Handle exceptions and check for failures
        for response, name in [(web_response, "web"), (kb_response, "kb"), (dakota_response, "dakota")]:
            if isinstance(response, Exception):
                logger.warning(f"{name} search failed with exception: {response}")
                continue
            if hasattr(response, 'payload') and not response.payload.get("success", True):
                logger.warning(f"{name} search failed: {response.payload.get('error', 'Unknown error')}")
        
        # Phase 2: Validate findings - safely extract payloads
        all_content = {
            "web_research": web_response.payload if hasattr(web_response, 'payload') else {"success": False, "error": "Search failed"},
            "kb_insights": kb_response.payload if hasattr(kb_response, 'payload') else {"success": False, "error": "KB search failed"},
            "dakota_insights": dakota_response.payload if hasattr(dakota_response, 'payload') else {"success": False, "error": "Dakota search failed"}
        }
        
        validation_msg = self.delegate_task(
            "data_validator",
            "validate_facts",
            {"content": json.dumps(all_content)}
        )
        validation_response = self.data_validator.receive_message(validation_msg)
        validation_payload = (
            validation_response.payload
            if hasattr(validation_response, "payload")
            else {"success": False, "error": "No validation response"}
        )
        if not validation_payload.get("success", True):
            return ResearchResult(
                success=False,
                topic=topic,
                synthesis={},
                raw_research=all_content,
                sources=[],
                validation=validation_payload,
                error=validation_payload.get("error", "Validation failed"),
            )
        # Phase 3: Find additional sources if needed
        sources_collected = self._extract_all_sources(all_content)
        
        if len(sources_collected) < requirements.get("min_sources", 10):
            source_msg = self.delegate_task(
                "web_researcher",
                "find_sources",
                {"query": topic}
            )
            source_response = self.web_researcher.receive_message(source_msg)
            if not source_response.payload.get("success", True):
                return ResearchResult(
                    success=False,
                    topic=topic,
                    synthesis={},
                    raw_research=all_content,
                    sources=sources_collected,
                    validation=validation_payload,
                    error=source_response.payload.get("error", "Source finding failed"),
                )
            sources_collected.extend(source_response.payload.get("sources", []))
        
        # Phase 4: Synthesize findings
        synthesis = self._synthesize_findings(
            topic,
            all_content,
            validation_payload,
            sources_collected
        )

        self.update_status(AgentStatus.COMPLETED, "Research complete")

        return ResearchResult(
            success=True,
            topic=topic,
            synthesis=synthesis,
            raw_research=all_content,
            validation=validation_payload,
            sources=sources_collected[:requirements.get("max_sources", 20)],
            research_quality_score=self._calculate_research_quality(
                all_content, validation_payload
            ),
        )
    
    def _coordinate_article_validation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate full article validation"""
        content = payload.get("content", "")
        
        # Parallel validation tasks
        tasks = []
        
        # Validate facts
        fact_msg = self.delegate_task(
            "data_validator",
            "validate_facts",
            {"content": content}
        )
        fact_validation = self.data_validator.receive_message(fact_msg)
        if not fact_validation.payload.get("success", True):
            return fact_validation.payload
        
        # Validate citations
        citation_msg = self.delegate_task(
            "data_validator",
            "validate_citations",
            {"content": content}
        )
        citation_validation = self.data_validator.receive_message(citation_msg)
        if not citation_validation.payload.get("success", True):
            return citation_validation.payload
        
        # Check consistency
        consistency_msg = self.delegate_task(
            "data_validator",
            "check_consistency",
            {"content": content}
        )
        consistency_check = self.data_validator.receive_message(consistency_msg)
        if not consistency_check.payload.get("success", True):
            return consistency_check.payload
        
        # Check data freshness
        freshness_msg = self.delegate_task(
            "data_validator",
            "check_freshness",
            {"content": content}
        )
        freshness_check = self.data_validator.receive_message(freshness_msg)
        if not freshness_check.payload.get("success", True):
            return freshness_check.payload
        
        # Compile validation report
        validation_report = {
            "facts": fact_validation.payload,
            "citations": citation_validation.payload,
            "consistency": consistency_check.payload,
            "freshness": freshness_check.payload
        }
        
        # Calculate overall validation score
        overall_score = self._calculate_validation_score(validation_report)
        
        return {
            "success": True,
            "validation_complete": True,
            "overall_score": overall_score,
            "passed": overall_score >= 70,
            "detailed_report": validation_report,
            "recommendations": self._generate_validation_recommendations(validation_report)
        }
    
    def _coordinate_source_finding(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate finding authoritative sources"""
        query = payload.get("query", "")
        min_sources = payload.get("min_sources", 10)
        
        # Get sources from multiple agents
        sources = []
        
        # Web sources
        web_msg = self.delegate_task(
            "web_researcher",
            "find_sources",
            {"query": query}
        )
        web_response = self.web_researcher.receive_message(web_msg)
        if not web_response.payload.get("success", True):
            return web_response.payload
        sources.extend(web_response.payload.get("sources", []))
        
        # Dakota KB sources
        kb_msg = self.delegate_task(
            "kb_researcher",
            "find_similar_articles",
            {"query": query}
        )
        kb_response = self.kb_researcher.receive_message(kb_msg)
        if not kb_response.payload.get("success", True):
            return kb_response.payload
        
        # Convert KB articles to source format
        for article in kb_response.payload.get("similar_articles", []):
            sources.append({
                "url": article.get("url", ""),
                "title": article.get("title", ""),
                "date": article.get("date", ""),
                "source_type": "dakota_kb",
                "relevance": article.get("relevance", 0)
            })
        
        # Validate sources
        source_validation_msg = self.delegate_task(
            "data_validator",
            "check_sources",
            {"sources": sources}
        )
        validation_response = self.data_validator.receive_message(source_validation_msg)
        if not validation_response.payload.get("success", True):
            return validation_response.payload
        
        # Filter and rank validated sources
        validated_sources = self._filter_validated_sources(
            sources,
            validation_response.payload
        )
        
        return {
            "success": True,
            "query": query,
            "sources_found": len(sources),
            "validated_sources": len(validated_sources),
            "sources": validated_sources[:min_sources * 2],  # Return extra for selection
            "validation_report": validation_response.payload
        }
    
    def _coordinate_fact_checking(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate fact checking of content"""
        content = payload.get("content", "")
        claims = payload.get("claims", [])
        
        # If specific claims provided, verify each
        if claims:
            verification_results = []
            
            for claim in claims:
                verify_msg = self.delegate_task(
                    "web_researcher",
                    "verify_claim",
                    {"claim": claim}
                )
                verify_response = self.web_researcher.receive_message(verify_msg)
                if not verify_response.payload.get("success", True):
                    return verify_response.payload
                verification_results.append({
                    "claim": claim,
                    "verification": verify_response.payload
                })
        else:
            # General fact validation
            fact_msg = self.delegate_task(
                "data_validator",
                "validate_facts",
                {"content": content}
            )
            fact_response = self.data_validator.receive_message(fact_msg)
            if not fact_response.payload.get("success", True):
                return fact_response.payload
            verification_results = fact_response.payload
        
        return {
            "success": True,
            "fact_check_complete": True,
            "results": verification_results,
            "summary": self._summarize_fact_check(verification_results)
        }
    
    def _synthesize_research(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Synthesize research findings"""
        findings = payload.get("findings", {})
        topic = payload.get("topic", "")
        
        synthesis_prompt = f"""Synthesize these research findings for: {topic}

Findings:
{json.dumps(findings, indent=2)}

Create a comprehensive synthesis that:
1. Identifies key themes and insights
2. Highlights Dakota-specific value propositions
3. Notes data gaps or conflicting information
4. Provides actionable recommendations
5. Suggests areas for deeper research

Focus on institutional investor needs."""

        synthesis = self.query_llm(
            synthesis_prompt,
            reasoning_effort="high",
            verbosity="high"
        )
        
        return {
            "success": True,
            "topic": topic,
            "synthesis": synthesis,
            "key_findings": self._extract_key_findings(synthesis),
            "recommendations": self._extract_recommendations(synthesis)
        }
    
    def _extract_all_sources(self, research_content: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract all sources from research content"""
        sources = []
        
        # Extract from web research
        if "web_research" in research_content:
            web_data = research_content["web_research"]
            if isinstance(web_data, dict) and "sources" in web_data:
                sources.extend(web_data["sources"])
        
        # Extract from KB insights
        if "kb_insights" in research_content:
            kb_data = research_content["kb_insights"]
            if isinstance(kb_data, dict) and "raw_results" in kb_data:
                # Convert KB results to source format
                kb_results = kb_data.get("raw_results", {})
                if "articles" in kb_results:
                    for article in kb_results["articles"]:
                        sources.append({
                            "url": f"https://dakota.com/articles/{article.get('id', '')}",
                            "title": article.get("title", ""),
                            "date": article.get("date", ""),
                            "source_type": "dakota_kb"
                        })
        
        # Remove duplicates
        seen_urls = set()
        unique_sources = []
        for source in sources:
            url = source.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(source)
        
        return unique_sources
    
    def _synthesize_findings(self, topic: str, research: Dict[str, Any], 
                           validation: Dict[str, Any], sources: List[Dict]) -> str:
        """Synthesize all research findings"""
        synthesis_data = {
            "topic": topic,
            "web_insights": research.get("web_research", {}).get("research_summary", ""),
            "dakota_insights": research.get("dakota_insights", {}).get("dakota_insights", ""),
            "kb_insights": research.get("kb_insights", {}).get("kb_insights", ""),
            "validation_score": validation.get("overall_credibility", 0),
            "source_count": len(sources),
            "high_quality_sources": len([s for s in sources if s.get("credibility_score", 0) >= 8])
        }
        
        synthesis_prompt = f"""Create a comprehensive research synthesis for: {topic}

Research Data:
{json.dumps(synthesis_data, indent=2)}

Synthesize into:
1. Executive Summary (key findings)
2. Market Analysis (current state and trends)
3. Dakota Perspective (unique insights and value)
4. Data and Evidence (statistics and proof points)
5. Investment Implications
6. Risk Factors
7. Recommendations

Ensure synthesis is coherent, data-driven, and actionable."""

        return self.query_llm(
            synthesis_prompt,
            reasoning_effort="high",
            verbosity="high"
        )
    
    def _calculate_research_quality(self, research: Dict[str, Any], 
                                  validation: Dict[str, Any]) -> float:
        """Calculate overall research quality score"""
        scores = []
        
        # Web research quality
        if "web_research" in research and research["web_research"].get("success"):
            scores.append(80)
        
        # KB research quality
        if "kb_insights" in research and research["kb_insights"].get("success"):
            scores.append(90)  # Dakota KB is high quality
        
        # Validation score
        if "overall_credibility" in validation:
            scores.append(validation["overall_credibility"])
        
        # Source diversity
        sources = self._extract_all_sources(research)
        source_diversity_score = min(100, len(sources) * 10)
        scores.append(source_diversity_score)
        
        return sum(scores) / len(scores) if scores else 0
    
    def _calculate_validation_score(self, report: Dict[str, Any]) -> float:
        """Calculate overall validation score"""
        scores = []
        
        # Fact validation
        if "facts" in report:
            fact_score = report["facts"].get("overall_credibility", 0)
            scores.append(fact_score)
        
        # Citation validation
        if "citations" in report:
            citations = report["citations"]
            if citations.get("total_citations", 0) > 0:
                citation_score = (citations.get("valid_citations", 0) / 
                                citations.get("total_citations", 1)) * 100
                scores.append(citation_score)
        
        # Consistency
        if "consistency" in report:
            consistency_score = 100 if report["consistency"].get("consistent") else 50
            scores.append(consistency_score)
        
        # Freshness
        if "freshness" in report:
            freshness_score = report["freshness"].get("freshness_score", 50)
            scores.append(freshness_score)
        
        return sum(scores) / len(scores) if scores else 0
    
    def _generate_validation_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation report"""
        recommendations = []
        
        # Check fact validation
        if "facts" in report:
            facts = report["facts"]
            if facts.get("issues_found", 0) > 0:
                recommendations.append(f"Address {facts['issues_found']} fact validation issues")
        
        # Check citations
        if "citations" in report:
            citations = report["citations"]
            if not citations.get("meets_minimum"):
                needed = citations.get("required", 10) - citations.get("valid_citations", 0)
                recommendations.append(f"Add {needed} more valid citations")
        
        # Check consistency
        if "consistency" in report:
            if not report["consistency"].get("consistent"):
                count = report["consistency"].get("inconsistencies_found", 0)
                recommendations.append(f"Resolve {count} content inconsistencies")
        
        # Check freshness
        if "freshness" in report:
            if not report["freshness"].get("is_current"):
                recommendations.append("Update outdated data references to 2024-2025")
        
        if not recommendations:
            recommendations.append("Content meets all validation criteria")
        
        return recommendations
    
    def _filter_validated_sources(self, sources: List[Dict], 
                                 validation: Dict[str, Any]) -> List[Dict]:
        """Filter sources based on validation results"""
        validated_sources = []
        validation_results = validation.get("results", [])
        
        # Create lookup for validation results
        validation_lookup = {}
        for result in validation_results:
            source_url = result.get("source", "")
            validation_lookup[source_url] = result
        
        # Filter and enhance sources
        for source in sources:
            url = source.get("url", "")
            if url in validation_lookup:
                val_result = validation_lookup[url]
                if val_result.get("recommended", False):
                    source["credibility_score"] = val_result.get("credibility_score", 0)
                    source["validation_notes"] = val_result.get("credibility_notes", [])
                    validated_sources.append(source)
        
        # Sort by credibility score
        return sorted(validated_sources, 
                     key=lambda x: x.get("credibility_score", 0), 
                     reverse=True)
    
    def _summarize_fact_check(self, results: Any) -> Dict[str, Any]:
        """Summarize fact checking results"""
        if isinstance(results, dict):
            # Single validation result
            return {
                "total_issues": results.get("issues_found", 0),
                "credibility_score": results.get("overall_credibility", 0),
                "status": "passed" if results.get("overall_credibility", 0) >= 70 else "needs_review"
            }
        elif isinstance(results, list):
            # Multiple claim verifications
            verified = sum(1 for r in results 
                         if r.get("verification", {}).get("verification_result", "").startswith("VERIFIED"))
            
            return {
                "claims_checked": len(results),
                "verified": verified,
                "unverified": len(results) - verified,
                "verification_rate": (verified / len(results) * 100) if results else 0
            }
        
        return {"status": "unknown"}
    
    def _extract_key_findings(self, synthesis: str) -> List[str]:
        """Extract key findings from synthesis"""
        # Simple extraction - look for numbered lists or bullet points
        findings = []
        lines = synthesis.split('\n')
        
        for line in lines:
            line = line.strip()
            if (line.startswith(('1.', '2.', '3.', '4.', '5.', '-', '•', '*')) and 
                len(line) > 10):
                # Clean up the finding
                finding = line.lstrip('0123456789.-•* ')
                if finding:
                    findings.append(finding)
        
        return findings[:10]  # Top 10 findings
    
    def _extract_recommendations(self, synthesis: str) -> List[str]:
        """Extract recommendations from synthesis"""
        recommendations = []
        lines = synthesis.split('\n')
        
        in_recommendations = False
        for line in lines:
            if 'recommendation' in line.lower():
                in_recommendations = True
                continue
            
            if in_recommendations:
                line = line.strip()
                if line and (line[0].isupper() or line.startswith(('-', '•', '*', '1'))):
                    rec = line.lstrip('0123456789.-•* ')
                    if rec and len(rec) > 10:
                        recommendations.append(rec)
                elif not line:
                    # Empty line might signal end of recommendations
                    if len(recommendations) >= 3:
                        break
        
        return recommendations[:5]  # Top 5 recommendations


class WritingTeamLead(BaseAgent):
    """Lead agent for writing team coordination"""
    
    def __init__(self):
        super().__init__(
            agent_id="writing_team_lead",
            agent_type="team_lead",
            team="writing"
        )
        self.capabilities = [
            "coordinate_writing",
            "manage_content_flow",
            "ensure_consistency",
            "review_drafts",
            "finalize_content"
        ]
        self.model = DEFAULT_MODELS.get("orchestrator", "gpt-5")
        
        # Initialize sub-agents
        self.content_writer = ContentWriterAgent()
        self.style_editor = StyleEditorAgent()
        self.citation_agent = CitationAgent()
        
        self.sub_agents = {
            "content_writer": self.content_writer,
            "style_editor": self.style_editor,
            "citation_agent": self.citation_agent
        }
    
    def validate_task(self, task: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate writing team tasks"""
        valid_tasks = [
            "write_article",
            "edit_article",
            "review_draft",
            "finalize_article",
            "improve_section"
        ]
        
        if task not in valid_tasks:
            return False, f"Task '{task}' not supported by WritingTeamLead"
        
        return True, "Valid task"
    
    def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process writing coordination request"""
        task = message.task
        payload = message.payload
        
        if task == "write_article":
            result = self._coordinate_article_writing(payload)
        elif task == "edit_article":
            result = self._coordinate_article_editing(payload)
        elif task == "review_draft":
            result = self._review_and_improve_draft(payload)
        elif task == "finalize_article":
            result = self._finalize_article(payload)
        else:
            result = self._improve_section(payload)
        
        return self._create_response(message, result)
    
    def _coordinate_article_writing(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate full article writing process"""
        topic = payload.get("topic", "")
        word_count = payload.get("word_count", 1500)
        research = payload.get("research", {})
        sources = payload.get("sources", [])
        requirements = payload.get("requirements", {})
        
        self.update_status(AgentStatus.WORKING, f"Writing article: {topic}")
        
        # Phase 1: Create outline
        outline_msg = self.delegate_task(
            "content_writer",
            "create_outline",
            {
                "topic": topic,
                "research": research,
                "target_sections": 7
            }
        )
        outline_response = self.content_writer.receive_message(outline_msg)
        if not outline_response.payload.get("success", True):
            return outline_response.payload
        
        # Phase 2: Write article
        write_msg = self.delegate_task(
            "content_writer",
            "write_article",
            {
                "topic": topic,
                "word_count": word_count,
                "research": research,
                "sources": sources,
                "requirements": requirements
            }
        )
        write_response = self.content_writer.receive_message(write_msg)
        if not write_response.payload.get("success", True):
            return write_response.payload
        
        article = write_response.payload.get("article", "")
        
        # Phase 3: Add citations
        citation_msg = self.delegate_task(
            "citation_agent",
            "add_citations",
            {
                "content": article,
                "sources": sources,
                "min_citations": requirements.get("min_citations", 10)
            }
        )
        citation_response = self.citation_agent.receive_message(citation_msg)
        if not citation_response.payload.get("success", True):
            return citation_response.payload
        
        article_with_citations = citation_response.payload.get("cited_content", article)
        
        # Phase 4: Style editing
        style_msg = self.delegate_task(
            "style_editor",
            "edit_style",
            {
                "content": article_with_citations,
                "style_guide": {
                    "tone": "professional-authoritative",
                    "audience": "institutional investors",
                    "voice": "active",
                    "formality": "high"
                }
            }
        )
        style_response = self.style_editor.receive_message(style_msg)
        if not style_response.payload.get("success", True):
            return style_response.payload
        
        final_article = style_response.payload.get("edited_content", article_with_citations)
        
        # Phase 5: Final polish
        polish_msg = self.delegate_task(
            "style_editor",
            "polish_content",
            {
                "content": final_article,
                "priorities": ["flow", "impact", "clarity", "professionalism"]
            }
        )
        polish_response = self.style_editor.receive_message(polish_msg)
        if not polish_response.payload.get("success", True):
            return polish_response.payload
        
        polished_article = polish_response.payload.get("polished_content", final_article)
        
        self.update_status(AgentStatus.COMPLETED, "Article writing complete")
        
        return {
            "success": True,
            "article": polished_article,
            "word_count": len(polished_article.split()),
            "outline": outline_response.payload.get("outline", ""),
            "citations_added": citation_response.payload.get("citations_added", 0),
            "quality_assessment": polish_response.payload.get("quality_assessment", {}),
            "writing_metrics": self._calculate_writing_metrics(polished_article)
        }
    
    def _coordinate_article_editing(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate comprehensive article editing"""
        content = payload.get("content", "")
        edit_requirements = payload.get("requirements", [])
        
        # Phase 1: Grammar and mechanics
        grammar_msg = self.delegate_task(
            "style_editor",
            "check_grammar",
            {"content": content}
        )
        grammar_response = self.style_editor.receive_message(grammar_msg)
        if not grammar_response.payload.get("success", True):
            return grammar_response.payload
        
        content = grammar_response.payload.get("corrected_content", content)
        
        # Phase 2: Clarity improvements
        clarity_msg = self.delegate_task(
            "style_editor",
            "improve_clarity",
            {
                "content": content,
                "focus_areas": ["complex sentences", "technical terms", "transitions"]
            }
        )
        clarity_response = self.style_editor.receive_message(clarity_msg)
        if not clarity_response.payload.get("success", True):
            return clarity_response.payload
        
        content = clarity_response.payload.get("clarified_content", content)
        
        # Phase 3: Consistency check
        consistency_msg = self.delegate_task(
            "style_editor",
            "ensure_consistency",
            {
                "content": content,
                "terminology": {},
                "style_rules": []
            }
        )
        consistency_response = self.style_editor.receive_message(consistency_msg)
        if not consistency_response.payload.get("success", True):
            return consistency_response.payload
        
        content = consistency_response.payload.get("consistent_content", content)
        
        # Phase 4: Citation verification
        citation_verify_msg = self.delegate_task(
            "citation_agent",
            "verify_citations",
            {"content": content}
        )
        citation_verify_response = self.citation_agent.receive_message(citation_verify_msg)
        if not citation_verify_response.payload.get("success", True):
            return citation_verify_response.payload
        
        # Phase 5: Final formatting
        if citation_verify_response.payload.get("needs_correction"):
            format_msg = self.delegate_task(
                "citation_agent",
                "format_citations",
                {"content": content}
            )
            format_response = self.citation_agent.receive_message(format_msg)
            if not format_response.payload.get("success", True):
                return format_response.payload
            content = format_response.payload.get("formatted_content", content)
        
        edit_summary = {
            "grammar_corrections": grammar_response.payload.get("errors_found", 0),
            "clarity_improvements": clarity_response.payload.get("improvements", []),
            "consistency_fixes": consistency_response.payload.get("changes_applied", 0),
            "citation_issues": citation_verify_response.payload.get("invalid_citations", 0)
        }
        
        return {
            "success": True,
            "edited_content": content,
            "edit_summary": edit_summary,
            "total_changes": sum([
                edit_summary["grammar_corrections"],
                edit_summary["consistency_fixes"],
                edit_summary["citation_issues"]
            ]),
            "ready_for_publication": self._assess_publication_readiness(content, edit_summary)
        }
    
    def _review_and_improve_draft(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Review draft and suggest improvements"""
        draft = payload.get("draft", "")
        review_criteria = payload.get("criteria", {})
        
        review_prompt = f"""Review this article draft:

{draft[:2000]}...

Review criteria:
{json.dumps(review_criteria, indent=2)}

Provide:
1. Overall quality assessment
2. Strengths
3. Areas for improvement
4. Specific recommendations
5. Priority fixes needed

Focus on institutional investor needs."""

        review = self.query_llm(
            review_prompt,
            reasoning_effort="high",
            verbosity="high"
        )
        
        # Extract specific improvements needed
        improvements = self._extract_improvement_recommendations(review)
        
        # If improvements needed, coordinate fixes
        if improvements:
            improved_draft = draft
            
            for improvement in improvements[:3]:  # Top 3 improvements
                if "expand" in improvement.lower():
                    expand_msg = self.delegate_task(
                        "content_writer",
                        "expand_content",
                        {
                            "content": improved_draft,
                            "target_expansion": 100,
                            "focus_areas": [improvement]
                        }
                    )
                    expand_response = self.content_writer.receive_message(expand_msg)
                    if not expand_response.payload.get("success", True):
                        return expand_response.payload
                    improved_draft = expand_response.payload.get("expanded_content", improved_draft)
                
                elif "clarify" in improvement.lower() or "simplify" in improvement.lower():
                    clarity_msg = self.delegate_task(
                        "style_editor",
                        "improve_clarity",
                        {
                            "content": improved_draft,
                            "focus_areas": [improvement]
                        }
                    )
                    clarity_response = self.style_editor.receive_message(clarity_msg)
                    if not clarity_response.payload.get("success", True):
                        return clarity_response.payload
                    improved_draft = clarity_response.payload.get("clarified_content", improved_draft)
            
            return {
                "success": True,
                "review": review,
                "improvements_made": improvements[:3],
                "improved_draft": improved_draft,
                "quality_score": self._calculate_draft_quality(improved_draft)
            }
        
        return {
            "success": True,
            "review": review,
            "improvements_made": [],
            "draft": draft,
            "quality_score": self._calculate_draft_quality(draft)
        }
    
    def _finalize_article(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize article for publication"""
        article = payload.get("article", "")
        metadata = payload.get("metadata", {})
        
        # Final checks
        final_checks = {}
        
        # Check word count
        word_count = len(article.split())
        final_checks["word_count"] = {
            "actual": word_count,
            "target": metadata.get("target_word_count", 1500),
            "meets_target": abs(word_count - metadata.get("target_word_count", 1500)) <= 50
        }
        
        # Verify citations
        citation_msg = self.delegate_task(
            "citation_agent",
            "verify_citations",
            {"content": article}
        )
        citation_response = self.citation_agent.receive_message(citation_msg)
        if not citation_response.payload.get("success", True):
            return citation_response.payload
        final_checks["citations"] = {
            "total": citation_response.payload.get("total_citations", 0),
            "valid": citation_response.payload.get("valid_citations", 0),
            "meets_minimum": citation_response.payload.get("valid_citations", 0) >= 10
        }
        
        # Final polish
        polish_msg = self.delegate_task(
            "style_editor",
            "polish_content",
            {
                "content": article,
                "priorities": ["impact", "memorability", "professionalism"]
            }
        )
        polish_response = self.style_editor.receive_message(polish_msg)
        if not polish_response.payload.get("success", True):
            return polish_response.payload
        
        final_article = polish_response.payload.get("polished_content", article)
        
        # Create bibliography
        bib_msg = self.delegate_task(
            "citation_agent",
            "create_bibliography",
            {"content": final_article}
        )
        bib_response = self.citation_agent.receive_message(bib_msg)
        if not bib_response.payload.get("success", True):
            return bib_response.payload
        
        # Generate introduction and conclusion if needed
        if not self._has_strong_introduction(final_article):
            intro_msg = self.delegate_task(
                "content_writer",
                "write_introduction",
                {
                    "topic": metadata.get("topic", ""),
                    "key_points": self._extract_key_points(final_article),
                    "hook": metadata.get("hook", "")
                }
            )
            intro_response = self.content_writer.receive_message(intro_msg)
            if not intro_response.payload.get("success", True):
                return intro_response.payload
            # Would integrate introduction here
        
        return {
            "success": True,
            "final_article": final_article,
            "bibliography": bib_response.payload.get("bibliography", ""),
            "final_checks": final_checks,
            "quality_assessment": polish_response.payload.get("quality_assessment", {}),
            "ready_for_publication": all([
                final_checks["word_count"]["meets_target"],
                final_checks["citations"]["meets_minimum"],
                polish_response.payload.get("ready_for_publication", False)
            ])
        }
    
    def _improve_section(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Improve a specific section"""
        section = payload.get("section", "")
        improvement_type = payload.get("improvement_type", "general")
        context = payload.get("context", "")
        
        if improvement_type == "expand":
            improve_msg = self.delegate_task(
                "content_writer",
                "expand_content",
                {
                    "content": section,
                    "target_expansion": 100,
                    "focus_areas": ["depth", "examples", "data"]
                }
            )
        elif improvement_type == "rewrite":
            improve_msg = self.delegate_task(
                "content_writer",
                "rewrite_content",
                {
                    "content": section,
                    "improvements": ["clarity", "impact", "flow"],
                    "style_guide": {}
                }
            )
        else:
            improve_msg = self.delegate_task(
                "style_editor",
                "improve_clarity",
                {
                    "content": section,
                    "focus_areas": ["all"]
                }
            )
        
        response = self.sub_agents[improve_msg.to_agent].receive_message(improve_msg)
        if not response.payload.get("success", True):
            return response.payload
        
        return {
            "success": True,
            "improved_section": response.payload.get("expanded_content") or 
                              response.payload.get("rewritten_content") or 
                              response.payload.get("clarified_content", section),
            "improvement_type": improvement_type,
            "changes_made": self._summarize_section_changes(section, response.payload)
        }
    
    def _calculate_writing_metrics(self, article: str) -> Dict[str, Any]:
        """Calculate writing quality metrics"""
        words = article.split()
        sentences = article.split('.')
        paragraphs = article.split('\n\n')
        
        return {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "paragraph_count": len(paragraphs),
            "avg_sentence_length": len(words) / max(len(sentences), 1),
            "avg_paragraph_length": len(words) / max(len(paragraphs), 1),
            "citation_density": article.count('[') / max(len(paragraphs), 1),
            "section_headers": len([line for line in article.split('\n') if line.startswith('#')])
        }
    
    def _assess_publication_readiness(self, content: str, edit_summary: Dict) -> bool:
        """Assess if content is ready for publication"""
        # Check key criteria
        word_count = len(content.split())
        has_citations = '[' in content
        minimal_errors = edit_summary.get("grammar_corrections", 0) < 5
        citations_valid = edit_summary.get("citation_issues", 0) == 0
        
        return all([
            1400 <= word_count <= 1600,  # Within word count range
            has_citations,
            minimal_errors,
            citations_valid
        ])
    
    def _extract_improvement_recommendations(self, review: str) -> List[str]:
        """Extract improvement recommendations from review"""
        recommendations = []
        lines = review.split('\n')
        
        in_recommendations = False
        for line in lines:
            if 'recommendation' in line.lower() or 'improvement' in line.lower():
                in_recommendations = True
                continue
            
            if in_recommendations and line.strip():
                if line.strip().startswith(('-', '•', '*', '1', '2', '3')):
                    rec = line.strip().lstrip('-•*0123456789. ')
                    if rec:
                        recommendations.append(rec)
                elif not line.strip():
                    if recommendations:
                        break
        
        return recommendations
    
    def _calculate_draft_quality(self, draft: str) -> float:
        """Calculate draft quality score"""
        score = 70.0  # Base score
        
        # Word count
        word_count = len(draft.split())
        if 1400 <= word_count <= 1600:
            score += 10
        
        # Citations
        citation_count = draft.count('[')
        if citation_count >= 10:
            score += 10
        
        # Structure
        if draft.count('##') >= 5:
            score += 5
        
        # Dakota mentions
        if 'dakota' in draft.lower():
            score += 5
        
        return min(100, score)
    
    def _has_strong_introduction(self, article: str) -> bool:
        """Check if article has a strong introduction"""
        lines = article.split('\n')
        
        # Check first few paragraphs
        first_content = '\n'.join(lines[:10])
        
        # Look for introduction markers
        has_hook = any(word in first_content.lower() for word in 
                      ['today', 'recent', 'growing', 'increasingly', 'critical'])
        has_preview = any(word in first_content.lower() for word in 
                         ['this article', 'we will', 'explore', 'examine'])
        
        return has_hook or has_preview
    
    def _extract_key_points(self, article: str) -> List[str]:
        """Extract key points from article"""
        key_points = []
        
        # Look for section headers
        lines = article.split('\n')
        for line in lines:
            if line.startswith('## ') and not line.startswith('### '):
                section = line.replace('## ', '').strip()
                if section and not any(skip in section.lower() for skip in 
                                     ['introduction', 'conclusion', 'summary']):
                    key_points.append(section)
        
        return key_points[:5]  # Top 5 sections
    
    def _summarize_section_changes(self, original: str, result: Dict[str, Any]) -> List[str]:
        """Summarize changes made to a section"""
        changes = []
        
        if "words_added" in result:
            changes.append(f"Added {result['words_added']} words")
        
        if "improvements_applied" in result:
            changes.extend(result["improvements_applied"])
        
        if "improvements" in result:
            changes.extend(result["improvements"])
        
        return changes[:3]  # Top 3 changes


class QualityTeamLead(BaseAgent):
    """Lead agent for quality team coordination"""
    
    def __init__(self):
        super().__init__(
            agent_id="quality_team_lead",
            agent_type="team_lead",
            team="quality"
        )
        self.capabilities = [
            "coordinate_quality_checks",
            "manage_compliance",
            "ensure_accuracy",
            "final_review",
            "quality_certification"
        ]
        self.model = DEFAULT_MODELS.get("orchestrator", "gpt-5")
        
        # Import quality agents dynamically to avoid circular imports
        from src.agents.quality_agents import FactCheckerAgent, ComplianceAgent, QualityAssuranceAgent
        
        # Initialize sub-agents
        self.fact_checker = FactCheckerAgent()
        self.compliance_agent = ComplianceAgent()
        self.qa_agent = QualityAssuranceAgent()
        
        self.sub_agents = {
            "fact_checker": self.fact_checker,
            "compliance_agent": self.compliance_agent,
            "qa_agent": self.qa_agent
        }
    
    def validate_task(self, task: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate quality team tasks"""
        valid_tasks = [
            "quality_review",
            "compliance_check",
            "fact_check",
            "final_approval",
            "quality_certification"
        ]
        
        if task not in valid_tasks:
            return False, f"Task '{task}' not supported by QualityTeamLead"
        
        return True, "Valid task"
    
    def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process quality coordination request"""
        task = message.task
        payload = message.payload
        
        if task == "quality_review":
            result = self._coordinate_quality_review(payload)
        elif task == "compliance_check":
            result = self._coordinate_compliance_check(payload)
        elif task == "fact_check":
            result = self._coordinate_fact_checking(payload)
        elif task == "final_approval":
            result = self._coordinate_final_approval(payload)
        else:
            result = self._issue_quality_certification(payload)
        
        return self._create_response(message, result)
    
    def _coordinate_quality_review(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate comprehensive quality review"""
        content = payload.get("content", "")
        requirements = payload.get("requirements", {})
        
        self.update_status(AgentStatus.WORKING, "Conducting quality review")
        
        # Phase 1: Fact checking
        fact_msg = self.delegate_task(
            "fact_checker",
            "accuracy_assessment",
            {"content": content}
        )
        fact_response = self.fact_checker.receive_message(fact_msg)
        if not fact_response.payload.get("success", True):
            return fact_response.payload
        
        # Phase 2: Compliance check
        compliance_msg = self.delegate_task(
            "compliance_agent",
            "check_compliance",
            {"content": content}
        )
        compliance_response = self.compliance_agent.receive_message(compliance_msg)
        if not compliance_response.payload.get("success", True):
            return compliance_response.payload
        
        # Phase 3: Quality assurance
        qa_msg = self.delegate_task(
            "qa_agent",
            "quality_review",
            {
                "content": content,
                "requirements": requirements
            }
        )
        qa_response = self.qa_agent.receive_message(qa_msg)
        if not qa_response.payload.get("success", True):
            return qa_response.payload
        
        # Compile results
        quality_report = {
            "fact_check": fact_response.payload,
            "compliance": compliance_response.payload,
            "quality_assurance": qa_response.payload
        }
        
        # Calculate overall quality score
        overall_score = self._calculate_overall_quality_score(quality_report)
        
        # Generate recommendations
        recommendations = self._compile_quality_recommendations(quality_report)
        
        self.update_status(AgentStatus.COMPLETED, "Quality review complete")
        
        return {
            "success": True,
            "overall_quality_score": overall_score,
            "quality_grade": self._determine_quality_grade(overall_score),
            "detailed_report": quality_report,
            "meets_standards": overall_score >= 85,
            "recommendations": recommendations,
            "critical_issues": self._identify_critical_issues(quality_report)
        }
    
    def _coordinate_compliance_check(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate compliance verification"""
        content = payload.get("content", "")
        
        # Full compliance check
        compliance_msg = self.delegate_task(
            "compliance_agent",
            "check_compliance",
            {"content": content}
        )
        compliance_response = self.compliance_agent.receive_message(compliance_msg)
        if not compliance_response.payload.get("success", True):
            return compliance_response.payload
        
        # Risk assessment
        risk_msg = self.delegate_task(
            "compliance_agent",
            "risk_assessment",
            {"content": content}
        )
        risk_response = self.compliance_agent.receive_message(risk_msg)
        if not risk_response.payload.get("success", True):
            return risk_response.payload
        
        # Disclaimer verification
        disclaimer_msg = self.delegate_task(
            "compliance_agent",
            "verify_disclaimers",
            {"content": content}
        )
        disclaimer_response = self.compliance_agent.receive_message(disclaimer_msg)
        if not disclaimer_response.payload.get("success", True):
            return disclaimer_response.payload
        
        return {
            "success": True,
            "compliance_status": compliance_response.payload,
            "risk_assessment": risk_response.payload,
            "disclaimer_status": disclaimer_response.payload,
            "is_compliant": compliance_response.payload.get("fully_compliant", False),
            "action_items": self._generate_compliance_action_items(
                compliance_response.payload,
                risk_response.payload,
                disclaimer_response.payload
            )
        }
    
    def _coordinate_fact_checking(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate comprehensive fact checking"""
        content = payload.get("content", "")
        sources = payload.get("sources", [])
        
        # Verify all facts
        fact_msg = self.delegate_task(
            "fact_checker",
            "verify_facts",
            {
                "content": content,
                "sources": sources
            }
        )
        fact_response = self.fact_checker.receive_message(fact_msg)
        if not fact_response.payload.get("success", True):
            return fact_response.payload
        
        # Check statistics
        stat_msg = self.delegate_task(
            "fact_checker",
            "check_statistics",
            {"content": content}
        )
        stat_response = self.fact_checker.receive_message(stat_msg)
        if not stat_response.payload.get("success", True):
            return stat_response.payload
        
        # Cross-reference sources
        cross_ref_msg = self.delegate_task(
            "fact_checker",
            "cross_reference",
            {
                "content": content,
                "sources": sources
            }
        )
        cross_ref_response = self.fact_checker.receive_message(cross_ref_msg)
        if not cross_ref_response.payload.get("success", True):
            return cross_ref_response.payload
        
        # Compile fact check report
        fact_check_report = {
            "facts": fact_response.payload,
            "statistics": stat_response.payload,
            "source_consistency": cross_ref_response.payload
        }
        
        accuracy_score = self._calculate_accuracy_score(fact_check_report)
        
        return {
            "success": True,
            "accuracy_score": accuracy_score,
            "fact_check_report": fact_check_report,
            "verified_claims": fact_response.payload.get("verified_claims", 0),
            "unverified_claims": fact_response.payload.get("unverified_claims", 0),
            "requires_correction": accuracy_score < 90,
            "corrections_needed": self._identify_needed_corrections(fact_check_report)
        }
    
    def _coordinate_final_approval(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate final approval process"""
        content = payload.get("content", "")
        quality_reports = payload.get("quality_reports", {})
        
        # Get final approval from QA
        approval_msg = self.delegate_task(
            "qa_agent",
            "final_approval",
            {
                "content": content,
                "quality_reports": quality_reports
            }
        )
        approval_response = self.qa_agent.receive_message(approval_msg)
        if not approval_response.payload.get("success", True):
            return approval_response.payload
        
        # If not approved, get improvement suggestions
        if not approval_response.payload.get("approved", False):
            suggestions_msg = self.delegate_task(
                "qa_agent",
                "improvement_suggestions",
                {
                    "content": content,
                    "quality_issues": self._extract_quality_issues(quality_reports)
                }
            )
            suggestions_response = self.qa_agent.receive_message(suggestions_msg)
            if not suggestions_response.payload.get("success", True):
                return suggestions_response.payload
            
            return {
                "success": True,
                "approved": False,
                "approval_report": approval_response.payload,
                "improvement_suggestions": suggestions_response.payload,
                "conditions_for_approval": approval_response.payload.get("conditions", [])
            }
        
        return {
            "success": True,
            "approved": True,
            "approval_report": approval_response.payload,
            "final_score": approval_response.payload.get("final_score", 0),
            "ready_for_publication": True
        }
    
    def _issue_quality_certification(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Issue quality certification for approved content"""
        content = payload.get("content", "")
        quality_scores = payload.get("quality_scores", {})
        
        # Verify all quality criteria met
        certification_criteria = {
            "accuracy": quality_scores.get("accuracy", 0) >= 90,
            "compliance": quality_scores.get("compliance", 0) >= 95,
            "readability": quality_scores.get("readability", 0) >= 80,
            "completeness": quality_scores.get("completeness", 0) >= 95,
            "overall_quality": quality_scores.get("overall", 0) >= 85
        }
        
        all_criteria_met = all(certification_criteria.values())
        
        if all_criteria_met:
            certification = {
                "status": "CERTIFIED",
                "certification_id": f"QC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "issued_by": self.agent_id,
                "issued_at": datetime.now().isoformat(),
                "quality_scores": quality_scores,
                "certification_level": self._determine_certification_level(quality_scores)
            }
        else:
            certification = {
                "status": "NOT_CERTIFIED",
                "failed_criteria": [k for k, v in certification_criteria.items() if not v],
                "recommendations": "Address failed criteria and resubmit for certification"
            }
        
        return {
            "success": True,
            "certification": certification,
            "certified": all_criteria_met,
            "quality_summary": self._generate_quality_summary(quality_scores, certification_criteria)
        }
    
    def _calculate_overall_quality_score(self, quality_report: Dict[str, Any]) -> float:
        """Calculate overall quality score from sub-reports"""
        weights = {
            "fact_check": 0.35,
            "compliance": 0.30,
            "quality_assurance": 0.35
        }
        
        scores = {
            "fact_check": quality_report["fact_check"].get("overall_accuracy_score", 0),
            "compliance": quality_report["compliance"].get("compliance_score", 0),
            "quality_assurance": quality_report["quality_assurance"].get("overall_quality_score", 0)
        }
        
        weighted_score = sum(scores[component] * weights[component] for component in weights)
        
        return weighted_score
    
    def _determine_quality_grade(self, score: float) -> str:
        """Determine quality grade based on score"""
        if score >= 95:
            return "Exceptional (A+)"
        elif score >= 90:
            return "Excellent (A)"
        elif score >= 85:
            return "Very Good (B+)"
        elif score >= 80:
            return "Good (B)"
        elif score >= 75:
            return "Acceptable (C+)"
        elif score >= 70:
            return "Marginal (C)"
        else:
            return "Below Standard (D)"
    
    def _compile_quality_recommendations(self, quality_report: Dict[str, Any]) -> List[str]:
        """Compile recommendations from all quality checks"""
        recommendations = []
        
        # From fact check
        if "recommendations" in quality_report["fact_check"]:
            recommendations.extend(quality_report["fact_check"]["recommendations"][:2])
        
        # From compliance
        if "recommendations" in quality_report["compliance"]:
            recommendations.extend(quality_report["compliance"]["recommendations"][:2])
        
        # From QA
        if "recommendations" in quality_report["quality_assurance"]:
            recommendations.extend(quality_report["quality_assurance"]["recommendations"][:2])
        
        # Deduplicate and prioritize
        unique_recommendations = list(dict.fromkeys(recommendations))
        
        return unique_recommendations[:5]  # Top 5 recommendations
    
    def _identify_critical_issues(self, quality_report: Dict[str, Any]) -> List[Dict[str, str]]:
        """Identify critical issues that must be addressed"""
        critical_issues = []
        
        # Check fact accuracy
        fact_accuracy = quality_report["fact_check"].get("accuracy_score", 100)
        if fact_accuracy < 90:
            critical_issues.append({
                "type": "accuracy",
                "severity": "HIGH",
                "description": f"Fact accuracy below threshold: {fact_accuracy:.1f}%",
                "action": "Verify and correct all unverified claims"
            })
        
        # Check compliance
        if not quality_report["compliance"].get("fully_compliant", True):
            critical_issues.extend([{
                "type": "compliance",
                "severity": "CRITICAL",
                "description": issue,
                "action": "Address immediately to meet regulatory requirements"
            } for issue in quality_report["compliance"].get("critical_issues", [])])
        
        # Check quality standards
        qa_score = quality_report["quality_assurance"].get("overall_quality_score", 100)
        if qa_score < 80:
            critical_issues.append({
                "type": "quality",
                "severity": "MEDIUM",
                "description": f"Quality score below standard: {qa_score:.1f}%",
                "action": "Improve content quality through editing and enhancement"
            })
        
        return critical_issues
    
    def _generate_compliance_action_items(self, compliance: Dict, risk: Dict, disclaimers: Dict) -> List[str]:
        """Generate specific compliance action items"""
        actions = []
        
        # From compliance check
        if not compliance.get("fully_compliant", True):
            actions.extend(compliance.get("recommendations", [])[:2])
        
        # From risk assessment
        if risk.get("risk_level") in ["HIGH", "CRITICAL"]:
            actions.extend(risk.get("mitigation_recommendations", [])[:2])
        
        # From disclaimer check
        if disclaimers.get("disclaimers_missing", 0) > 0:
            missing = disclaimers.get("missing_list", [])
            actions.append(f"Add missing disclaimers: {', '.join(missing)}")
        
        return actions[:5]  # Top 5 actions
    
    def _calculate_accuracy_score(self, fact_check_report: Dict[str, Any]) -> float:
        """Calculate overall accuracy score"""
        components = {
            "facts": fact_check_report["facts"].get("accuracy_score", 0),
            "statistics": (fact_check_report["statistics"].get("valid_statistics", 0) / 
                          max(fact_check_report["statistics"].get("total_statistics", 1), 1)) * 100,
            "sources": fact_check_report["source_consistency"].get("consistency_score", 0)
        }
        
        # Weighted average
        weights = {"facts": 0.4, "statistics": 0.3, "sources": 0.3}
        
        accuracy_score = sum(components[key] * weights[key] for key in weights)
        
        return accuracy_score
    
    def _identify_needed_corrections(self, fact_check_report: Dict[str, Any]) -> List[str]:
        """Identify specific corrections needed"""
        corrections = []
        
        # From fact verification
        unverified = fact_check_report["facts"].get("unverified_claims", 0)
        if unverified > 0:
            corrections.append(f"Verify or correct {unverified} unverified claims")
        
        # From statistics check
        invalid_stats = fact_check_report["statistics"].get("invalid_statistics", 0)
        if invalid_stats > 0:
            corrections.append(f"Correct {invalid_stats} invalid statistics")
        
        # From source consistency
        conflicts = fact_check_report["source_consistency"].get("conflicting_claims", [])
        if conflicts:
            corrections.append(f"Resolve {len(conflicts)} conflicting claims across sources")
        
        return corrections
    
    def _extract_quality_issues(self, quality_reports: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract quality issues from reports"""
        issues = []
        
        for report_name, report in quality_reports.items():
            if "issues" in report:
                for issue in report["issues"]:
                    issues.append({
                        "source": report_name,
                        "type": issue.get("type", "general"),
                        "description": issue.get("description", ""),
                        "severity": issue.get("severity", "medium")
                    })
        
        return issues
    
    def _determine_certification_level(self, quality_scores: Dict[str, float]) -> str:
        """Determine certification level based on scores"""
        avg_score = sum(quality_scores.values()) / len(quality_scores)
        
        if avg_score >= 95:
            return "PLATINUM"
        elif avg_score >= 90:
            return "GOLD"
        elif avg_score >= 85:
            return "SILVER"
        else:
            return "BRONZE"
    
    def _generate_quality_summary(self, scores: Dict[str, float], criteria: Dict[str, bool]) -> str:
        """Generate quality summary"""
        summary_lines = ["Quality Summary:"]
        
        for metric, score in scores.items():
            status = "✅" if criteria.get(metric, False) else "❌"
            summary_lines.append(f"- {metric.title()}: {score:.1f}% {status}")
        
        avg_score = sum(scores.values()) / len(scores)
        summary_lines.append(f"\nOverall Average: {avg_score:.1f}%")
        
        return "\n".join(summary_lines)


class PublishingTeamLead(BaseAgent):
    """Lead agent for publishing team coordination"""
    
    def __init__(self):
        super().__init__(
            agent_id="publishing_team_lead",
            agent_type="team_lead",
            team="publishing"
        )
        self.capabilities = [
            "prepare_publication",
            "seo_optimization",
            "metadata_generation",
            "distribution_planning",
            "social_content"
        ]
        self.model = DEFAULT_MODELS.get("orchestrator", "gpt-5")
        
        # For now, we'll simulate sub-agents with methods
        # In a full implementation, these would be separate agent classes
        self.sub_agents = {}
    
    def validate_task(self, task: str, payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate publishing team tasks"""
        valid_tasks = [
            "prepare_publication",
            "optimize_seo",
            "generate_metadata",
            "create_social_content",
            "plan_distribution"
        ]
        
        if task not in valid_tasks:
            return False, f"Task '{task}' not supported by PublishingTeamLead"
        
        return True, "Valid task"
    
    def process_message(self, message: AgentMessage) -> AgentMessage:
        """Process publishing coordination request"""
        task = message.task
        payload = message.payload
        
        if task == "prepare_publication":
            result = self._coordinate_publication_prep(payload)
        elif task == "optimize_seo":
            result = self._coordinate_seo_optimization(payload)
        elif task == "generate_metadata":
            result = self._coordinate_metadata_generation(payload)
        elif task == "create_social_content":
            result = self._coordinate_social_content(payload)
        else:
            result = self._plan_distribution_strategy(payload)
        
        return self._create_response(message, result)
    
    def _coordinate_publication_prep(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate publication preparation"""
        article = payload.get("article", "")
        metadata = payload.get("metadata", {})
        
        self.update_status(AgentStatus.WORKING, "Preparing for publication")

        # SEO optimization
        seo_result = self._optimize_for_seo(article, metadata)

        # Generate metadata
        metadata_result = self._generate_comprehensive_metadata(article, metadata)
        if not metadata_result.get("success", False):
            return {
                "success": False,
                "error": metadata_result.get("error", "Metadata generation failed")
            }

        # Create social content
        social_result = self._create_social_media_content(article, metadata)

        # Generate publication package
        publication_package = {
            "article": seo_result["optimized_content"],
            "metadata": metadata_result["metadata"],
            "seo": seo_result["seo_data"],
            "social": social_result["social_content"],
            "distribution": self._create_distribution_plan(metadata)
        }

        self.update_status(AgentStatus.COMPLETED, "Publication preparation complete")

        return {
            "success": True,
            "publication_package": publication_package,
            "seo_score": seo_result["seo_score"],
            "social_ready": len(social_result["social_content"]) > 0,
            "publication_checklist": self._generate_publication_checklist(publication_package)
        }
    
    def _coordinate_seo_optimization(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate SEO optimization"""
        content = payload.get("content", "")
        target_keywords = payload.get("keywords", [])
        
        return self._optimize_for_seo(content, {"keywords": target_keywords})
    
    def _coordinate_metadata_generation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate metadata generation"""
        content = payload.get("content", "")
        existing_metadata = payload.get("existing_metadata", {})
        
        return self._generate_comprehensive_metadata(content, existing_metadata)
    
    def _coordinate_social_content(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate social media content creation"""
        article = payload.get("article", "")
        metadata = payload.get("metadata", {})
        
        return self._create_social_media_content(article, metadata)
    
    def _plan_distribution_strategy(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Plan content distribution strategy"""
        metadata = payload.get("metadata", {})
        target_audience = payload.get("target_audience", "institutional investors")
        
        distribution_plan = self._create_distribution_plan(metadata)
        
        # Add audience-specific channels
        if target_audience == "institutional investors":
            distribution_plan["channels"].extend([
                "Institutional investor newsletter",
                "LinkedIn targeted posts",
                "Industry publication syndication"
            ])
        
        return {
            "success": True,
            "distribution_plan": distribution_plan,
            "estimated_reach": self._estimate_reach(distribution_plan),
            "timeline": self._create_distribution_timeline(distribution_plan)
        }
    
    def _optimize_for_seo(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize content for SEO"""
        seo_prompt = f"""Optimize this article for SEO:

{content[:2000]}...

Target keywords: {metadata.get('keywords', [])}

Provide:
1. Title tag (60 chars max)
2. Meta description (160 chars max)
3. Suggested URL slug
4. Header optimization recommendations
5. Keyword density analysis
6. Internal linking opportunities

Return SEO-optimized version and recommendations."""

        seo_analysis = self.query_llm(
            seo_prompt,
            reasoning_effort="medium",
            verbosity="high"
        )
        
        # Calculate SEO score
        seo_score = self._calculate_seo_score(content, metadata.get('keywords', []))
        
        return {
            "optimized_content": content,  # In production, would apply optimizations
            "seo_data": {
                "title_tag": self._extract_title_tag(seo_analysis),
                "seo_description": self._extract_meta_description(seo_analysis),
                "url_slug": self._generate_url_slug(metadata.get('title', '')),
                "keyword_density": self._calculate_keyword_density(content, metadata.get('keywords', []))
            },
            "seo_score": seo_score,
            "recommendations": self._extract_seo_recommendations(seo_analysis)
        }
    
    def _generate_comprehensive_metadata(self, content: str, existing_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive metadata"""
        metadata_prompt = f"""Generate comprehensive metadata for this article:

{content[:1500]}...

Create:
1. SEO-optimized title
2. Description (150-160 chars)
3. Keywords (8-10 relevant terms)
4. Categories (2-3)
5. Tags (5-8)
6. Author information
7. Publication date
8. Reading time
9. Difficulty level
10. Target audience

Return as structured data."""

        metadata_response = self.query_llm(
            metadata_prompt,
            reasoning_effort="low",
            verbosity="medium"
        )

        # Parse and structure metadata
        metadata = self._parse_metadata_response(metadata_response)
        metadata.update(existing_metadata)  # Preserve existing data

        # Add calculated fields
        metadata["word_count"] = len(content.split())
        metadata["read_time_minutes"] = self._calculate_reading_time(content)
        metadata["last_updated"] = datetime.now().isoformat()

        required_fields = ["keywords", "read_time_minutes", "key_takeaways"]
        missing = [f for f in required_fields if not metadata.get(f)]
        if missing:
            return {
                "success": False,
                "error": f"Missing required metadata fields: {', '.join(missing)}"
            }

        return {
            "success": True,
            "metadata": metadata,
            "completeness_score": self._calculate_metadata_completeness(metadata)
        }
    
    def _create_social_media_content(self, article: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create social media content"""
        social_prompt = f"""Create social media content for this article:

Title: {metadata.get('title', 'Article')}
Summary: {article[:1000]}...

Generate:
1. LinkedIn post (300 words, professional tone)
2. Twitter/X thread (5-7 tweets, include key stats)
3. Email newsletter snippet (150 words)
4. Executive summary (200 words)

Include hashtags and CTAs."""

        social_content = self.query_llm(
            social_prompt,
            reasoning_effort="medium",
            verbosity="high"
        )
        
        # Parse social content
        parsed_social = self._parse_social_content(social_content)
        
        return {
            "social_content": parsed_social,
            "platforms_covered": list(parsed_social.keys()),
            "estimated_engagement": self._estimate_social_engagement(parsed_social)
        }
    
    def _create_distribution_plan(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Create content distribution plan"""
        return {
            "channels": [
                "Dakota website",
                "Email newsletter",
                "LinkedIn company page",
                "Twitter/X",
                "Partner syndication"
            ],
            "timing": {
                "immediate": ["Website publication", "Email notification"],
                "day_1": ["LinkedIn post", "Twitter thread"],
                "week_1": ["Newsletter feature", "Partner syndication"],
                "ongoing": ["SEO optimization", "Social reshares"]
            },
            "target_metrics": {
                "views": 5000,
                "engagement_rate": 0.05,
                "shares": 100,
                "qualified_leads": 10
            }
        }
    
    def _calculate_seo_score(self, content: str, keywords: List[str]) -> float:
        """Calculate SEO score"""
        score = 70  # Base score
        
        # Check title
        lines = content.split('\n')
        if lines and lines[0].startswith('#'):
            score += 10
        
        # Check keyword density
        content_lower = content.lower()
        keyword_count = sum(content_lower.count(kw.lower()) for kw in keywords)
        word_count = len(content.split())
        
        if word_count > 0:
            keyword_density = (keyword_count / word_count) * 100
            if 1 <= keyword_density <= 3:
                score += 10
        
        # Check headers
        header_count = sum(1 for line in lines if line.startswith('#'))
        if header_count >= 5:
            score += 10
        
        return min(100, score)
    
    def _calculate_keyword_density(self, content: str, keywords: List[str]) -> Dict[str, float]:
        """Calculate keyword density"""
        content_lower = content.lower()
        word_count = len(content.split())
        
        density = {}
        for keyword in keywords:
            count = content_lower.count(keyword.lower())
            density[keyword] = (count / word_count * 100) if word_count > 0 else 0
        
        return density
    
    def _calculate_reading_time(self, content: str) -> int:
        """Calculate estimated reading time in minutes"""
        words = len(content.split())
        # Average reading speed: 200-250 words per minute
        return max(1, round(words / 225))
    
    def _calculate_metadata_completeness(self, metadata: Dict[str, Any]) -> float:
        """Calculate metadata completeness score"""
        required_fields = [
            "title", "description", "keywords", "categories",
            "tags", "author", "publication_date", "reading_time"
        ]
        
        present_fields = sum(1 for field in required_fields if field in metadata and metadata[field])
        
        return (present_fields / len(required_fields)) * 100
    
    def _generate_publication_checklist(self, package: Dict[str, Any]) -> List[Dict[str, bool]]:
        """Generate publication checklist"""
        checklist = [
            {
                "item": "Article content finalized",
                "completed": bool(package.get("article"))
            },
            {
                "item": "SEO optimization complete",
                "completed": package.get("seo", {}).get("seo_score", 0) >= 70
            },
            {
                "item": "Metadata generated",
                "completed": bool(package.get("metadata"))
            },
            {
                "item": "Social content created",
                "completed": bool(package.get("social"))
            },
            {
                "item": "Distribution plan ready",
                "completed": bool(package.get("distribution"))
            }
        ]
        
        return checklist
    
    def _estimate_reach(self, distribution_plan: Dict[str, Any]) -> int:
        """Estimate potential reach"""
        channel_reach = {
            "Dakota website": 2000,
            "Email newsletter": 5000,
            "LinkedIn company page": 3000,
            "Twitter/X": 1000,
            "Partner syndication": 2000
        }
        
        total_reach = sum(channel_reach.get(channel, 0) for channel in distribution_plan["channels"])
        
        return total_reach
    
    def _create_distribution_timeline(self, distribution_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create distribution timeline"""
        timeline = []
        
        for time_period, activities in distribution_plan["timing"].items():
            timeline.append({
                "period": time_period,
                "activities": activities,
                "status": "pending"
            })
        
        return timeline
    
    def _extract_title_tag(self, seo_analysis: str) -> str:
        """Extract title tag from SEO analysis"""
        # Simple extraction - in production would parse more carefully
        lines = seo_analysis.split('\n')
        for line in lines:
            if "title tag" in line.lower():
                # Extract the next meaningful content
                return line.split(':')[-1].strip()[:60]
        
        return "Investment Insights from Dakota"
    
    def _extract_meta_description(self, seo_analysis: str) -> str:
        """Extract meta description from SEO analysis"""
        lines = seo_analysis.split('\n')
        for line in lines:
            if "meta description" in line.lower():
                return line.split(':')[-1].strip()[:160]
        
        return "Expert insights on alternative investments for institutional investors."
    
    def _generate_url_slug(self, title: str) -> str:
        """Generate URL slug from title"""
        # Simple slug generation
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = slug.strip('-')
        
        return slug[:60]  # Limit length
    
    def _extract_seo_recommendations(self, seo_analysis: str) -> List[str]:
        """Extract SEO recommendations"""
        recommendations = []
        lines = seo_analysis.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['recommend', 'suggest', 'improve', 'optimize']):
                recommendations.append(line.strip())
        
        return recommendations[:5]
    
    def _parse_metadata_response(self, response: str) -> Dict[str, Any]:
        """Parse metadata from response"""
        # In production, would use structured parsing
        metadata = {
            "title": "",
            "description": "",
            "keywords": [],
            "categories": [],
            "tags": [],
            "author": "Dakota Research Team",
            "publication_date": datetime.now().isoformat(),
            "difficulty_level": "Professional",
            "target_audience": "Institutional Investors"
        }
        
        # Simple parsing logic
        lines = response.split('\n')
        current_field = None
        
        for line in lines:
            line = line.strip()
            if "title:" in line.lower():
                metadata["title"] = line.split(':', 1)[-1].strip()
            elif "description:" in line.lower():
                metadata["description"] = line.split(':', 1)[-1].strip()
            elif "keywords:" in line.lower():
                current_field = "keywords"
            elif "categories:" in line.lower():
                current_field = "categories"
            elif "tags:" in line.lower():
                current_field = "tags"
            elif current_field and line.startswith('-'):
                value = line.lstrip('-').strip()
                if current_field in metadata and isinstance(metadata[current_field], list):
                    metadata[current_field].append(value)
        
        return metadata
    
    def _parse_social_content(self, content: str) -> Dict[str, str]:
        """Parse social media content"""
        social = {
            "linkedin": "",
            "twitter": "",
            "email": "",
            "executive_summary": ""
        }
        
        # Simple parsing based on sections
        current_platform = None
        lines = content.split('\n')
        
        for line in lines:
            if "linkedin" in line.lower():
                current_platform = "linkedin"
            elif "twitter" in line.lower() or "tweet" in line.lower():
                current_platform = "twitter"
            elif "email" in line.lower():
                current_platform = "email"
            elif "executive" in line.lower():
                current_platform = "executive_summary"
            elif current_platform and line.strip():
                social[current_platform] += line + "\n"
        
        return social
    
    def _estimate_social_engagement(self, social_content: Dict[str, str]) -> Dict[str, float]:
        """Estimate social media engagement"""
        engagement_rates = {
            "linkedin": 0.05,  # 5% engagement rate
            "twitter": 0.02,   # 2% engagement rate
            "email": 0.25,     # 25% open rate
            "executive_summary": 0.10  # 10% forward rate
        }
        
        estimated_engagement = {}
        for platform, content in social_content.items():
            if content:
                estimated_engagement[platform] = engagement_rates.get(platform, 0.01)
        
        return estimated_engagement
