"""Unified configuration for the Dakota Learning Center system.

This module consolidates settings that were previously spread across
multiple configuration files.  Environment specific overrides can be
provided in ``config_working.py`` and will be loaded automatically when
present.
"""

from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------
load_dotenv()

# Directory configuration ----------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Allow overriding the output directory with an environment variable
OUTPUT_DIR = Path(os.getenv("DAKOTA_OUTPUT_DIR", PROJECT_ROOT / "output")).resolve()
RUNS_DIR = OUTPUT_DIR
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"
PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def prompt_path(name: str) -> str:
    """Return the absolute path to a prompt file by name."""

    return str(PROMPTS_DIR / name)


def read_prompt(name: str) -> str:
    """Read the contents of a prompt file."""

    p = prompt_path(name)
    with open(p, "r", encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# API and model configuration
# ---------------------------------------------------------------------------

# Vector Store id for File Search (optional)
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID", "").strip() or None

# Default models (best-for-cost mix; override via .env)
DEFAULT_MODELS: Dict[str, str] = {
    "orchestrator": os.getenv("ORCHESTRATOR_MODEL", "gpt-4.1"),
    "web_researcher": os.getenv("WEB_RESEARCHER_MODEL", "gpt-4.1"),
    "kb_researcher": os.getenv("KB_RESEARCHER_MODEL", "gpt-4.1-mini"),
    "synthesizer": os.getenv("SYNTHESIZER_MODEL", "gpt-4.1"),
    "writer": os.getenv("WRITER_MODEL", "gpt-4.1"),
    "seo": os.getenv("SEO_MODEL", "gpt-4.1-mini"),
    "fact_checker": os.getenv("FACT_CHECKER_MODEL", "gpt-4.1"),
    "summary": os.getenv("SUMMARY_MODEL", "gpt-4.1-mini"),
    "social": os.getenv("SOCIAL_MODEL", "gpt-4.1-mini"),
    "iteration": os.getenv("ITERATION_MODEL", "gpt-4.1"),
    "metrics": os.getenv("METRICS_MODEL", "gpt-4.1-mini"),
    "evidence": os.getenv("EVIDENCE_MODEL", "gpt-4.1"),
    "claim_checker": os.getenv("CLAIM_CHECKER_MODEL", "gpt-4.1-mini"),
    "metadata": os.getenv("METADATA_MODEL", "gpt-4.1-mini"),
}


# ---------------------------------------------------------------------------
# Budget & caps (soft)
# ---------------------------------------------------------------------------
BUDGET_USD = float(os.getenv("BUDGET_USD", "1.50"))
MAX_WEB_CALLS = int(os.getenv("MAX_WEB_CALLS", "80"))
MAX_FILE_CALLS = int(os.getenv("MAX_FILE_CALLS", "10"))

OUTPUT_TOKEN_CAPS = {
    "writer_max_tokens": int(os.getenv("WRITER_MAX_TOKENS", "3500")),
    "summary_max_tokens": int(os.getenv("SUMMARY_MAX_TOKENS", "500")),
    "social_max_tokens": int(os.getenv("SOCIAL_MAX_TOKENS", "900")),
    "seo_max_tokens": int(os.getenv("SEO_MAX_TOKENS", "900")),
    "metrics_max_tokens": int(os.getenv("METRICS_MAX_TOKENS", "700")),
    "synth_max_tokens": int(os.getenv("SYNTH_MAX_TOKENS", "1600")),
    "factcheck_max_tokens": int(os.getenv("FACTCHECK_MAX_TOKENS", "1000")),
}


# ---------------------------------------------------------------------------
# Feature toggles
# ---------------------------------------------------------------------------
ENABLE_EVIDENCE = os.getenv("ENABLE_EVIDENCE", "1") == "1"
ENABLE_CLAIM_CHECK = os.getenv("ENABLE_CLAIM_CHECK", "1") == "1"
ENABLE_SUMMARY = os.getenv("ENABLE_SUMMARY", "1") == "1"
ENABLE_SOCIAL = os.getenv("ENABLE_SOCIAL", "1") == "1"
ENABLE_METRICS = os.getenv("ENABLE_METRICS", "1") == "1"
ENABLE_SEO = os.getenv("ENABLE_SEO", "1") == "1"


# ---------------------------------------------------------------------------
# Quality Requirements
# ---------------------------------------------------------------------------
MIN_WORD_COUNT = int(os.getenv("MIN_WORD_COUNT", "1750"))
MIN_SOURCES = int(os.getenv("MIN_SOURCES", "10"))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "2"))
REQUIRE_URL_VERIFICATION = os.getenv("REQUIRE_URL_VERIFICATION", "true").lower() == "true"
REQUIRE_DAKOTA_URLS = os.getenv("REQUIRE_DAKOTA_URLS", "true").lower() == "true"
FACT_CHECK_MANDATORY = os.getenv("FACT_CHECK_MANDATORY", "true").lower() == "true"

# Required/forbidden sections used by orchestrators
REQUIRED_SECTIONS = [
    "Key Insights at a Glance",
    "Key Takeaways",
    "Conclusion",
]

FORBIDDEN_SECTIONS = [
    "Introduction",
    "Executive Summary",
    "About Dakota",
    "Disclaimer",
]


# Citation standards ---------------------------------------------------------
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
        "mckinsey.com",
    ],
    "banned_domains": [
        "wikipedia.org",
        "investopedia.com",
        "reddit.com",
        "quora.com",
    ],
}


# ---------------------------------------------------------------------------
# Validation configuration
# ---------------------------------------------------------------------------
STANDARD_VALIDATION = {
    "min_credibility": 0.8,
    "min_fact_accuracy": 0.9,
    "require_citation_for_all_facts": True,
    "max_unverified_facts": 0,
    "min_source_credibility": 7,
    "require_current_year_data": True,
}

PRIVATE_MARKET_VALIDATION = {
    "min_credibility": 0.7,
    "min_fact_accuracy": 0.85,
    "require_citation_for_all_facts": False,
    "max_unverified_facts": 5,
    "min_source_credibility": 6,
    "require_current_year_data": True,
}

LOCATION_BASED_VALIDATION = {
    "min_credibility": 0.6,
    "min_fact_accuracy": 0.75,
    "require_citation_for_all_facts": False,
    "max_unverified_facts": 15,
    "min_source_credibility": 5,
    "require_current_year_data": False,
}

QUICK_BRIEF_VALIDATION = {
    "min_credibility": 0.7,
    "min_fact_accuracy": 0.8,
    "require_citation_for_all_facts": False,
    "max_unverified_facts": 5,
    "min_source_credibility": 6,
    "require_current_year_data": False,
}


def get_validation_config(topic: str, word_count: int = 2000) -> Dict[str, float | int | bool]:
    """Determine appropriate validation config based on topic and type."""

    topic_lower = topic.lower()

    # Location-based content takes precedence
    location_keywords = [
        "top 10",
        "best firms in",
        "leading firms in",
        "firms in",
        "companies in",
        "investors in",
        "in atlanta",
        "in dallas",
        "in austin",
        "in nashville",
        "in memphis",
        "in charlotte",
        "in raleigh",
        "in boston",
        "in chicago",
        "in denver",
        "in miami",
        "in seattle",
        "in portland",
        "in texas",
        "in california",
        "in new york",
        "in florida",
    ]
    if any(k in topic_lower for k in location_keywords) or (
        "top" in topic_lower and ("in " in topic_lower or "texas" in topic_lower or "california" in topic_lower)
    ):
        return LOCATION_BASED_VALIDATION

    private_keywords = [
        "private equity",
        "pe firms",
        "venture capital",
        "vc firms",
        "private funds",
        "hedge funds",
        "family offices",
    ]
    if any(k in topic_lower for k in private_keywords):
        return PRIVATE_MARKET_VALIDATION

    if word_count <= 500:
        return QUICK_BRIEF_VALIDATION

    return STANDARD_VALIDATION


MUST_CITE_PATTERNS = [
    r"\$[\d,]+(?:\.\d+)?(?:\s*(?:billion|million|trillion))",
    r"(?:raised|allocated|invested|committed)\s+\$",
    r"\d+%\s+(?:increase|decrease|growth|decline)",
    r"(?:returned|generated|yielded)\s+\d+%",
    r"(?:AUM|assets under management)",
    r"(?:IRR|internal rate of return)",
]


def is_key_fact(fact_text: str) -> bool:
    """Determine if a fact is critical and must have citation."""

    for pattern in MUST_CITE_PATTERNS:
        if re.search(pattern, fact_text, re.IGNORECASE):
            return True
    return False


# ---------------------------------------------------------------------------
# Environment specific overrides -------------------------------------------
# ---------------------------------------------------------------------------
try:  # pragma: no cover - optional overrides
    from .config_working import *  # type: ignore
except Exception:  # pragma: no cover
    pass

