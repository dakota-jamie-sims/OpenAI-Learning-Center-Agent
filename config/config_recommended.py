"""
Recommended Configuration with Actual OpenAI Models
Dakota Learning Center Article Generation System
Updated: August 2025
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Directory Configuration
PROJECT_ROOT = Path(__file__).parent.parent
RUNS_DIR = PROJECT_ROOT / "runs"
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")

# Model Selection - BALANCED CONFIGURATION (Quality + Cost)
# Using actual OpenAI models available as of August 2025
DEFAULT_MODELS = {
    # Critical quality agents - use GPT-4 Turbo for best results
    "writer": "gpt-4-turbo",           # Premium content generation (1,750+ words)
    "factchecker": "gpt-4-turbo",      # Critical accuracy verification
    "synthesizer": "gpt-4-turbo",      # Complex synthesis task
    
    # Research and analysis agents - use GPT-4o for good performance
    "web_researcher": "gpt-4o",        # Web search and synthesis
    "kb_researcher": "gpt-4o",         # Knowledge base analysis
    "evidence": "gpt-4o",              # Evidence verification
    "claims": "gpt-4o",                # Claims validation
    "iteration": "gpt-4o",             # Improvement reasoning
    
    # Supporting agents - use GPT-4o-mini for efficiency
    "summary": "gpt-4o-mini",          # Summary generation
    "metrics": "gpt-4o-mini",          # Metrics analysis
    
    # Low-complexity agents - use GPT-3.5 Turbo for cost savings
    "seo": "gpt-3.5-turbo",           # SEO optimization
    "social": "gpt-3.5-turbo"         # Social media content
}

# Alternative Model Configurations
HIGH_QUALITY_MODELS = {
    # Use GPT-4 Turbo for all complex tasks
    "web_researcher": "gpt-4-turbo",
    "kb_researcher": "gpt-4-turbo",
    "synthesizer": "gpt-4-turbo",
    "writer": "gpt-4-turbo",
    "factchecker": "gpt-4-turbo",
    "iteration": "gpt-4-turbo",
    "evidence": "gpt-4-turbo",
    "claims": "gpt-4-turbo",
    "summary": "gpt-4o",
    "metrics": "gpt-4o",
    "seo": "gpt-4o",
    "social": "gpt-3.5-turbo"
}

COST_OPTIMIZED_MODELS = {
    # Minimize costs while maintaining quality
    "writer": "gpt-4o",
    "factchecker": "gpt-4o",
    "synthesizer": "gpt-4o-mini",
    "web_researcher": "gpt-4o-mini",
    "kb_researcher": "gpt-4o-mini",
    "iteration": "gpt-4o-mini",
    "evidence": "gpt-4o-mini",
    "claims": "gpt-4o-mini",
    "summary": "gpt-4o-mini",
    "metrics": "gpt-4o-mini",
    "seo": "gpt-3.5-turbo",
    "social": "gpt-3.5-turbo"
}

# Quality Thresholds (ZERO COMPROMISE)
MIN_WORD_COUNT = 2000  # Increased from 1750
MIN_SOURCES = 12       # Increased from 10
MAX_ITERATIONS = 3     # Allow more iterations for perfection
MIN_READING_TIME = 8   # Minutes (ensures depth)
MAX_BROKEN_LINKS = 0   # Zero tolerance for broken links

# Research Budgets (Generous for thoroughness)
MAX_WEB_CALLS = 100    # Increased from 80
MAX_FILE_CALLS = 15    # Increased from 10

# Token Caps (Generous for quality)
OUTPUT_TOKEN_CAPS = {
    "synth_max_tokens": 3000,      # Increased
    "metrics_max_tokens": 1500,    # Increased
    "seo_max_tokens": 1500,        # Increased
    "factcheck_max_tokens": 2000,  # Increased
    "summary_max_tokens": 1000,    # Increased
    "social_max_tokens": 800,      # Increased
}

# Feature Flags (All enabled for maximum quality)
ENABLE_EVIDENCE = True      # Evidence tracking
ENABLE_CLAIM_CHECK = True   # Claim verification
ENABLE_SEO = True          # SEO optimization
ENABLE_METRICS = True      # Quality metrics
ENABLE_SUMMARY = True      # Executive summaries
ENABLE_SOCIAL = True       # Social media content
FACT_CHECK_MANDATORY = True # Cannot skip fact-checking

# Quality Standards
REQUIRED_SECTIONS = [
    "Key Insights at a Glance",
    "Key Takeaways",
    "Conclusion"
]

FORBIDDEN_SECTIONS = [
    "Introduction",
    "Executive Summary",  # Separate deliverable
    "About Dakota",
    "Disclaimer"
]

# Citation Requirements
CITATION_STANDARDS = {
    "require_primary_sources": True,
    "max_source_age_months": 12,  # Recent data only
    "require_publication_date": True,
    "require_author_attribution": True,
    "banned_domains": [
        "wikipedia.org",  # No Wikipedia as primary source
        "reddit.com",
        "quora.com",
        "medium.com"  # Unless verified expert
    ],
    "preferred_domains": [
        "sec.gov",
        "federalreserve.gov",
        "imf.org",
        "worldbank.org",
        "nber.org",
        "jstor.org",
        "sciencedirect.com",
        "morningstar.com",
        "bloomberg.com",
        "wsj.com",
        "ft.com",
        "reuters.com"
    ]
}

# Validation Rules
VALIDATION_RULES = {
    "structure": {
        "require_yaml_frontmatter": True,
        "require_all_sections": True,
        "max_heading_depth": 3,
        "require_internal_links": True
    },
    "content": {
        "max_passive_voice_percentage": 20,
        "max_sentence_length": 30,  # words
        "require_data_points": True,
        "min_examples_per_section": 1
    },
    "style": {
        "forbidden_phrases": [
            "arguably",
            "it goes without saying",
            "needless to say",
            "in conclusion",
            "in summary"
        ],
        "tone": "professional_conversational"
    }
}

# Logging Configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "handlers": {
        "file": {
            "filename": "article_generation.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5
        },
        "console": {
            "stream": "stdout"
        }
    }
}

# Quality Report Settings
QUALITY_REPORT_CONFIG = {
    "generate_report": True,
    "include_metrics": True,
    "include_validation_details": True,
    "include_source_analysis": True,
    "include_readability_scores": True,
    "export_format": "markdown"  # or "json"
}