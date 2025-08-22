# Dakota Agents Module
"""
Dakota multi-agent system implementation using GPT-5 models with Responses API.
Mimics the Learning Center Agent architecture with parallel execution and verification.
"""

from .orchestrator import DakotaOrchestrator
from .kb_researcher import DakotaKBResearcher
from .web_researcher import DakotaWebResearcher
from .research_synthesizer import DakotaResearchSynthesizer
from .content_writer import DakotaContentWriter
from .metrics_analyzer import DakotaMetricsAnalyzer
from .seo_specialist import DakotaSEOSpecialist
from .fact_checker import DakotaFactChecker
from .iteration_manager import DakotaIterationManager
from .social_promoter import DakotaSocialPromoter
from .summary_writer import DakotaSummaryWriter

__all__ = [
    'DakotaOrchestrator',
    'DakotaKBResearcher',
    'DakotaWebResearcher',
    'DakotaResearchSynthesizer',
    'DakotaContentWriter',
    'DakotaMetricsAnalyzer',
    'DakotaSEOSpecialist',
    'DakotaFactChecker',
    'DakotaIterationManager',
    'DakotaSocialPromoter',
    'DakotaSummaryWriter'
]