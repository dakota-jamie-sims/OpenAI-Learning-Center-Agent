"""Dakota Orchestrator with Data Analysis - Extended version with spreadsheet support"""

import asyncio
import os
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from src.models import ArticleRequest
from src.utils.logging import get_logger

# Import all agents including the new data analyzer
from .kb_researcher import DakotaKBResearcher
from .web_researcher import DakotaWebResearcher
from .data_analyzer import DakotaDataAnalyzer
from .research_synthesizer import DakotaResearchSynthesizer
from .content_writer import DakotaContentWriter
from .fact_checker_v2 import DakotaFactCheckerV2
from .iteration_manager import DakotaIterationManager
from .social_promoter import DakotaSocialPromoter
from .summary_writer import DakotaSummaryWriter
from .seo_specialist import DakotaSEOSpecialist
from .metrics_analyzer import DakotaMetricsAnalyzer

# Import base orchestrator
from .orchestrator import DakotaOrchestrator

logger = get_logger(__name__)


class DakotaOrchestratorWithData(DakotaOrchestrator):
    """Extended orchestrator that includes data analysis capabilities"""
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow with optional data analysis"""
        # Store data file info in instance for phase 2
        self.data_file = task.get("data_file")
        self.analysis_type = task.get("analysis_type", "general")
        
        # Debug logging
        self.logger.info(f"DakotaOrchestratorWithData - data_file: {self.data_file}")
        self.logger.info(f"DakotaOrchestratorWithData - analysis_type: {self.analysis_type}")
        
        # Call parent execute
        return await super().execute(task)
    
    async def _phase2_research(self, topic: str) -> Dict[str, Any]:
        """Phase 2: Research with optional data analysis"""
        
        # Get data file from instance
        data_file = getattr(self, 'data_file', None)
        analysis_type = getattr(self, 'analysis_type', 'general')
        
        # Debug logging
        self.logger.info(f"Phase 2 - data_file from instance: {data_file}")
        self.logger.info(f"Phase 2 - analysis_type: {analysis_type}")
        
        # Always deploy KB and Web researchers
        agents_to_deploy = 2
        if data_file:
            agents_to_deploy = 3  # Add data analyzer
            
        self.logger.info(f"Deploying {agents_to_deploy} subagents in parallel to research {topic}")
        
        # Create agents
        kb_researcher = DakotaKBResearcher()
        web_researcher = DakotaWebResearcher()
        
        # Create tasks list
        tasks = []
        
        # KB research task
        kb_task = asyncio.create_task(
            kb_researcher.execute({"topic": topic})
        )
        tasks.append(("kb", kb_task))
        
        # Web research task
        web_task = asyncio.create_task(
            web_researcher.execute({"topic": topic})
        )
        tasks.append(("web", web_task))
        
        # Data analysis task if file provided
        if data_file:
            data_analyzer = DakotaDataAnalyzer()
            data_task = asyncio.create_task(
                data_analyzer.execute({
                    "data_file": data_file,
                    "topic": topic,
                    "analysis_type": analysis_type
                })
            )
            tasks.append(("data", data_task))
        
        # Wait for all tasks to complete
        results = {}
        for name, task in tasks:
            try:
                result = await task
                results[name] = result
            except Exception as e:
                self.logger.error(f"{name} research failed: {e}")
                results[name] = {"success": False, "error": str(e)}
        
        # Combine results
        kb_result = results.get("kb", {})
        web_result = results.get("web", {})
        data_result = results.get("data", {}) if data_file else None
        
        combined_data = self._combine_research_results_with_data(kb_result, web_result, data_result)
        
        # Store for later phases
        self.phase_results["research"] = combined_data
        
        return self.format_response(True, data=combined_data)
    
    def _combine_research_results_with_data(self, kb_result: Dict, web_result: Dict, 
                                           data_result: Optional[Dict]) -> Dict[str, Any]:
        """Combine research results including data analysis"""
        
        # Start with the standard combination
        combined = {
            "sources": [],
            "insights": [],
            "kb_data": {},
            "data_analysis": None
        }
        
        # Add KB insights (not sources)
        if kb_result.get("success"):
            kb_data = kb_result.get("data", {})
            combined["insights"].extend(kb_data.get("insights", []))
            combined["kb_data"] = kb_data
        
        # Add web sources and insights
        if web_result.get("success"):
            web_data = web_result.get("data", {})
            combined["sources"].extend(web_data.get("sources", []))
            if web_data.get("summary"):
                combined["insights"].append(web_data["summary"])
        
        # Add data analysis if available
        if data_result and data_result.get("success"):
            data_analysis = data_result.get("data", {})
            combined["data_analysis"] = data_analysis
            
            # Add data insights
            if data_analysis.get("insights"):
                combined["insights"].extend(data_analysis["insights"])
            
            # Add data source as a citation with proper format
            if data_analysis.get("data_source"):
                combined["sources"].append({
                    "title": f"Internal Data Analysis: {data_analysis['data_source']}",
                    "url": "https://www.dakota.com/internal-analysis",  # Use a placeholder Dakota URL
                    "snippet": f"Analysis of {data_analysis.get('row_count', 0)} rows with {data_analysis.get('column_count', 0)} columns",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "type": "data_analysis",
                    "authority": 3  # High authority for internal data
                })
        
        return combined