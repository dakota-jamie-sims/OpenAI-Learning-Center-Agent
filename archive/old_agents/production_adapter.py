"""
Production Adapter - Bridges V2 system with existing agents
Allows testing production optimizations without rewriting all agents
"""
import os
import sys
from typing import Type, Dict, Any

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import existing agents
from src.agents.dakota_agents.kb_researcher import DakotaKBResearcher
from src.agents.dakota_agents.web_researcher import DakotaWebResearcher
from src.agents.dakota_agents.research_synthesizer import DakotaResearchSynthesizer
from src.agents.dakota_agents.content_writer import DakotaContentWriter
from src.agents.dakota_agents.fact_checker_v2 import DakotaFactCheckerV2
from src.agents.dakota_agents.iteration_manager import DakotaIterationManager
from src.agents.dakota_agents.social_promoter import DakotaSocialPromoter
from src.agents.dakota_agents.summary_writer import DakotaSummaryWriter
from src.agents.dakota_agents.seo_specialist import DakotaSEOSpecialist
from src.agents.dakota_agents.metrics_analyzer import DakotaMetricsAnalyzer

# Create V2 aliases that use existing agents
class DakotaKBResearcherV2(DakotaKBResearcher):
    """KB Researcher V2 - Adapter for existing KB researcher"""
    pass

class DakotaWebResearcherV2(DakotaWebResearcher):
    """Web Researcher V2 - Adapter for existing web researcher"""
    pass

class DakotaResearchSynthesizerV2(DakotaResearchSynthesizer):
    """Research Synthesizer V2 - Adapter with plan_synthesis method"""
    
    async def plan_synthesis(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Quick synthesis planning (lightweight)"""
        # Just return the task as the plan for now
        return {
            "topic": task.get("topic"),
            "approach": "comprehensive",
            "sections": ["overview", "insights", "recommendations"]
        }

class DakotaContentWriterV2(DakotaContentWriter):
    """Content Writer V2 - Adapter for existing content writer"""
    pass

class DakotaFactCheckerV3(DakotaFactCheckerV2):
    """Fact Checker V3 - Adapter for existing fact checker v2"""
    pass

class DakotaIterationManagerV2(DakotaIterationManager):
    """Iteration Manager V2 - Adapter for existing iteration manager"""
    pass

class DakotaSocialPromoterV2(DakotaSocialPromoter):
    """Social Promoter V2 - Adapter for existing social promoter"""
    pass

class DakotaSummaryWriterV2(DakotaSummaryWriter):
    """Summary Writer V2 - Adapter for existing summary writer"""
    pass

class DakotaSEOSpecialistV2(DakotaSEOSpecialist):
    """SEO Specialist V2 - Adapter for existing SEO specialist"""
    pass


# Agent factory for easy access
def get_agent_v2(agent_name: str) -> Type:
    """Get V2 agent by name"""
    agents = {
        "kb_researcher": DakotaKBResearcherV2,
        "web_researcher": DakotaWebResearcherV2,
        "research_synthesizer": DakotaResearchSynthesizerV2,
        "content_writer": DakotaContentWriterV2,
        "fact_checker": DakotaFactCheckerV3,
        "iteration_manager": DakotaIterationManagerV2,
        "social_promoter": DakotaSocialPromoterV2,
        "summary_writer": DakotaSummaryWriterV2,
        "seo_specialist": DakotaSEOSpecialistV2,
        "metrics_analyzer": DakotaMetricsAnalyzer  # No V2 needed
    }
    
    return agents.get(agent_name)