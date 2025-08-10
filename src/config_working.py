"""
Working Configuration with Valid OpenAI Models
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
PROMPTS_DIR = PROJECT_ROOT / "src" / "prompts"

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID")

# Model Selection - Using actual OpenAI models
DEFAULT_MODELS = {
    "web_researcher": "gpt-4-turbo-preview",     # Good for research
    "kb_researcher": "gpt-4-turbo-preview",      # Knowledge base integration
    "synthesizer": "gpt-4-turbo-preview",        # Synthesis capabilities
    "writer": "gpt-4-turbo-preview",             # Content generation
    "factchecker": "gpt-4-turbo-preview",        # Accuracy verification
    "iteration": "gpt-4-turbo-preview",          # Self-improvement
    "metrics": "gpt-3.5-turbo",                  # Simple metrics analysis
    "seo": "gpt-3.5-turbo",                      # SEO optimization
    "summary": "gpt-4-turbo-preview",            # Executive summaries
    "social": "gpt-3.5-turbo",                   # Social media content
    "evidence": "gpt-4-turbo-preview",           # Evidence validation
    "claims": "gpt-4-turbo-preview",             # Claim verification
    "metadata": "gpt-3.5-turbo",                 # Metadata generation
    # Add missing mappings
    "web_researcher": "gpt-4-turbo-preview",
    "kb_researcher": "gpt-4-turbo-preview",
    "research_synthesizer": "gpt-4-turbo-preview",
    "content_writer": "gpt-4-turbo-preview",
    "fact_checker": "gpt-4-turbo-preview",
    "claim_checker": "gpt-4-turbo-preview",
    "seo_specialist": "gpt-3.5-turbo",
    "metrics_analyzer": "gpt-3.5-turbo",
    "summary_writer": "gpt-4-turbo-preview",
    "social_promoter": "gpt-3.5-turbo",
    "iteration_manager": "gpt-4-turbo-preview",
    "evidence_packager": "gpt-4-turbo-preview",
    "metadata_generator": "gpt-3.5-turbo"
}

# Quality Thresholds
MIN_WORD_COUNT = 2000  # Target word count
MIN_SOURCES = 12       # Minimum sources required
MAX_ITERATIONS = 3     # Allow iterations for quality
MIN_READING_TIME = 8   # Minutes (ensures depth)
MAX_BROKEN_LINKS = 0   # Zero tolerance for broken links

# Dakota-Specific Requirements
REQUIRE_ALLOCATION_DATA = True    # Articles should include real allocation amounts
REQUIRE_INVESTOR_TYPES = True     # Must specify RIA, Pension, etc.
REQUIRE_FUNDRAISING_APPLICATION = True  # Must have practical takeaways
MIN_DAKOTA_REFERENCES = 2         # Reference existing Dakota content

# Required Sections
REQUIRED_SECTIONS = [
    "Key Takeaways",
    "Introduction", 
    "Main Analysis",
    "Practical Applications",
    "Related Dakota Learning Center Articles"
]

# Forbidden Sections
FORBIDDEN_SECTIONS = [
    "About Dakota",
    "Contact Us",
    "Disclaimer",
    "Copyright",
    "Legal Notice"
]

# Citation Standards
CITATION_STANDARDS = {
    "min_citations": 12,
    "min_inline_citations": 8,
    "prefer_primary_sources": True,
    "max_source_age_months": 12,
    "preferred_domains": [
        "preqin.com",
        "pitchbook.com", 
        "bloomberg.com",
        "reuters.com",
        "wsj.com",
        "ft.com",
        "sec.gov",
        "federalreserve.gov",
        "cambridgeassociates.com",
        "mckinsey.com"
    ],
    "banned_domains": [
        "wikipedia.org",
        "investopedia.com",
        "reddit.com",
        "quora.com"
    ]
}

# Output Token Caps
OUTPUT_TOKEN_CAPS = {
    "synth_max_tokens": 2000,
    "summary_max_tokens": 500,
    "social_max_tokens": 300
}

# Feature Flags
ENABLE_EVIDENCE = True
ENABLE_CLAIM_CHECK = True
ENABLE_SEO = True
ENABLE_METRICS = True
ENABLE_SUMMARY = True
ENABLE_SOCIAL = True

# Budget Settings
MAX_WEB_CALLS = 10
MAX_FILE_CALLS = 10

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def prompt_path(name: str) -> str:
    return str(PROMPTS_DIR / name)

def read_prompt(name: str) -> str:
    p = prompt_path(name)
    with open(p, "r", encoding="utf-8") as f:
        return f.read()