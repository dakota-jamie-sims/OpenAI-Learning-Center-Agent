"""
Enhanced Configuration for Zero-Compromise Quality
Dakota Learning Center Article Generation System
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

# Model Selection (GPT-4 for maximum quality)
DEFAULT_MODELS = {
    "web_researcher": "gpt-4-turbo-preview",
    "kb_researcher": "gpt-4-turbo-preview",
    "synthesizer": "gpt-4-turbo-preview",
    "writer": "gpt-4-turbo-preview",
    "factchecker": "gpt-4-turbo-preview",
    "iteration": "gpt-4-turbo-preview",
    "metrics": "gpt-4",
    "seo": "gpt-4",
    "summary": "gpt-4",
    "social": "gpt-4",
    "evidence": "gpt-4",
    "claims": "gpt-4-turbo-preview"
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