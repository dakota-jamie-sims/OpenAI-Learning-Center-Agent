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
OUTPUT_DIR = PROJECT_ROOT / "output"
RUNS_DIR = OUTPUT_DIR  # For backward compatibility
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")

# Model Selection (Optimized for GPT-5 and GPT-4.1)
DEFAULT_MODELS = {
    "web_researcher": "gpt-4.1",         # Fast, efficient research
    "kb_researcher": "gpt-4.1",          # Knowledge base integration
    "synthesizer": "gpt-5",              # Advanced synthesis capabilities
    "writer": "gpt-5",                   # Premium content generation
    "factchecker": "gpt-5",              # Maximum accuracy verification
    "iteration": "gpt-5",                # Advanced self-improvement
    "metrics": "gpt-4.1",                # Standard metrics analysis
    "seo": "gpt-4.1",                    # SEO optimization
    "summary": "gpt-5",                  # High-quality executive summaries
    "social": "gpt-4.1",                 # Social media content
    "evidence": "gpt-5",                 # Critical evidence validation
    "claims": "gpt-5",                   # Advanced claim verification
    "metadata": "gpt-4.1"                # Metadata generation
}

# Quality Thresholds (ZERO COMPROMISE)
MIN_WORD_COUNT = 2000  # Increased from 1750
MIN_SOURCES = 12       # Increased from 10
MAX_ITERATIONS = 3     # Allow more iterations for perfection
MIN_READING_TIME = 8   # Minutes (ensures depth)
MAX_BROKEN_LINKS = 0   # Zero tolerance for broken links

# Dakota-Specific Requirements
REQUIRE_ALLOCATION_DATA = True    # Articles should include real allocation amounts
REQUIRE_INVESTOR_TYPES = True     # Must specify RIA, Pension, etc.
REQUIRE_FUNDRAISING_APPLICATION = True  # Must have practical takeaways
MIN_DAKOTA_REFERENCES = 2         # Reference existing Dakota content

# Data Freshness Requirements (100% Current Data)
MAX_AGE_MARKET_DATA_DAYS = 30     # Market data must be within 30 days
MAX_AGE_ALLOCATION_DATA_DAYS = 90 # Allocation data within 90 days
MAX_AGE_GENERAL_DATA_DAYS = 180   # General data within 6 months
REQUIRE_CURRENT_YEAR_DATA = True  # Must have 2025 data
REQUIRE_DATED_CITATIONS = True    # All citations must include dates

# Target Audience (Dakota's Database)
TARGET_INVESTORS = [
    "RIAs (Registered Investment Advisors)",
    "Family Offices",
    "Multi-Family Offices (MFOs)",
    "Public Pension Funds",
    "Corporate Pension Funds",
    "Endowments",
    "Foundations",
    "OCIOs",
    "Institutional Consultants",
    "Insurance Companies",
    "Fund of Funds",
    "Healthcare Systems",
    "Bank Trusts",
    "Broker Dealers"
]

# Dakota Philosophy
DAKOTA_CORE_VALUE = "Focus on What Matters Most"
DAKOTA_WAY_PRINCIPLES = [
    "Set Expectations",
    "Know Who to Call On",
    "Become a Master Messenger",
    "Master Your CRM"
]

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