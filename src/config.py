import os
from dotenv import load_dotenv
load_dotenv()

# Vector Store id for File Search (optional)
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID", "").strip() or None

# Web search configuration
WEB_SEARCH_API_KEY = os.getenv("WEB_SEARCH_API_KEY", "").strip()
WEB_SEARCH_API_ENDPOINT = os.getenv(
    "WEB_SEARCH_API_ENDPOINT", "https://google.serper.dev/search"
).strip()

# Caching configuration
CACHE_SIZE = int(os.getenv("CACHE_SIZE", "128"))
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))

# Default models (best-for-cost mix; override via .env)
DEFAULT_MODELS = {
    "default": os.getenv("DEFAULT_MODEL", "gpt-5"),
    "orchestrator": os.getenv("ORCHESTRATOR_MODEL", "gpt-5"),
    "web_researcher": os.getenv("WEB_RESEARCHER_MODEL", "gpt-5"),
    "kb_researcher": os.getenv("KB_RESEARCHER_MODEL", "gpt-5-mini"),
    "synthesizer": os.getenv("SYNTHESIZER_MODEL", "gpt-5"),
    "writer": os.getenv("WRITER_MODEL", "gpt-5"),
    "seo": os.getenv("SEO_MODEL", "gpt-5-nano"),
    "fact_checker": os.getenv("FACT_CHECKER_MODEL", "gpt-5"),
    "summary": os.getenv("SUMMARY_MODEL", "gpt-5-mini"),
    "social": os.getenv("SOCIAL_MODEL", "gpt-5-nano"),
    "iteration": os.getenv("ITERATION_MODEL", "gpt-5"),
    "metrics": os.getenv("METRICS_MODEL", "gpt-5-mini"),
    "evidence": os.getenv("EVIDENCE_MODEL", "gpt-5"),
    "claim_checker": os.getenv("CLAIM_CHECKER_MODEL", "gpt-5-mini"),
    "metadata": os.getenv("METADATA_MODEL", "gpt-5-mini"),
}

# Output directories
OUTPUT_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output", "articles"))
OUTPUT_DIR = OUTPUT_BASE_DIR  # Alias for compatibility
RUNS_DIR = OUTPUT_BASE_DIR  # For compatibility
os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)

# Alternative: Use environment variable if set
if os.getenv("DAKOTA_OUTPUT_DIR"):
    OUTPUT_BASE_DIR = os.path.abspath(os.getenv("DAKOTA_OUTPUT_DIR"))
    OUTPUT_DIR = OUTPUT_BASE_DIR
    RUNS_DIR = OUTPUT_BASE_DIR
    os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)

# Prompts dir
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")

def prompt_path(name: str) -> str:
    return os.path.join(PROMPTS_DIR, name)

def read_prompt(name: str) -> str:
    p = prompt_path(name)
    with open(p, "r", encoding="utf-8") as f:
        return f.read()

# -------- Budget & caps (soft) --------
BUDGET_USD = float(os.getenv("BUDGET_USD", "1.50"))
MAX_WEB_CALLS = int(os.getenv("MAX_WEB_CALLS", "80"))
MAX_FILE_CALLS = int(os.getenv("MAX_FILE_CALLS", "10"))

# Research configuration
RESEARCH_CONFIG = {
    "min_sources": int(os.getenv("MIN_SOURCES", "5")),
    "max_data_age_days": int(os.getenv("MAX_DATA_AGE_DAYS", "180")),
    "preferred_sources": [
        "mckinsey.com",
        "bain.com", 
        "bcg.com",
        "preqin.com",
        "pitchbook.com",
        "dakota.com"
    ]
}

OUTPUT_TOKEN_CAPS = {
    "writer_max_tokens": int(os.getenv("WRITER_MAX_TOKENS", "3500")),
    "summary_max_tokens": int(os.getenv("SUMMARY_MAX_TOKENS", "500")),
    "social_max_tokens": int(os.getenv("SOCIAL_MAX_TOKENS", "900")),
    "seo_max_tokens": int(os.getenv("SEO_MAX_TOKENS", "900")),
    "metrics_max_tokens": int(os.getenv("METRICS_MAX_TOKENS", "700")),
    "synth_max_tokens": int(os.getenv("SYNTH_MAX_TOKENS", "1600")),
    "factcheck_max_tokens": int(os.getenv("FACTCHECK_MAX_TOKENS", "1000")),
}

# -------- Feature toggles --------
ENABLE_EVIDENCE = os.getenv("ENABLE_EVIDENCE", "1") == "1"
ENABLE_CLAIM_CHECK = os.getenv("ENABLE_CLAIM_CHECK", "1") == "1"
ENABLE_SUMMARY = os.getenv("ENABLE_SUMMARY", "1") == "1"
ENABLE_SOCIAL = os.getenv("ENABLE_SOCIAL", "1") == "1"
ENABLE_METRICS = os.getenv("ENABLE_METRICS", "1") == "1"
ENABLE_SEO = os.getenv("ENABLE_SEO", "1") == "1"

# -------- Quality Requirements --------
MIN_WORD_COUNT = int(os.getenv("MIN_WORD_COUNT", "1750"))
MIN_SOURCES = int(os.getenv("MIN_SOURCES", "10"))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "2"))
REQUIRE_URL_VERIFICATION = os.getenv("REQUIRE_URL_VERIFICATION", "true").lower() == "true"
REQUIRE_DAKOTA_URLS = os.getenv("REQUIRE_DAKOTA_URLS", "true").lower() == "true"
FACT_CHECK_MANDATORY = os.getenv("FACT_CHECK_MANDATORY", "true").lower() == "true"

# Article configuration
ARTICLE_CONFIG = {
    "target_word_count": int(os.getenv("TARGET_WORD_COUNT", "2000")),
    "min_word_count": MIN_WORD_COUNT,
    "default_tone": "professional yet conversational",
    "default_audience": "institutional investors and financial professionals",
    "include_metadata": True,
    "include_social": True,
    "include_summary": True
}
