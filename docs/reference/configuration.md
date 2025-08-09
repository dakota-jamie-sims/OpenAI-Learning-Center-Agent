# Configuration Reference

Complete reference for all configuration options in the Dakota Learning Center system.

## Configuration File

Location: `src/config_enhanced.py`

## Environment Variables

### Required
```bash
OPENAI_API_KEY=sk-...        # Your OpenAI API key
```

### Optional
```bash
VECTOR_STORE_ID=vs_...       # Created by setup_vector_store.py
```

## Quality Thresholds

### Word and Source Requirements
```python
MIN_WORD_COUNT = 2000        # Minimum words per article
MIN_SOURCES = 12             # Minimum number of citations
MAX_ITERATIONS = 3           # Maximum quality improvement attempts
MIN_READING_TIME = 8         # Minimum reading time in minutes
MAX_BROKEN_LINKS = 0         # Zero tolerance for broken URLs
```

### Credibility Requirements
```python
MIN_CREDIBILITY = 0.8        # 80% overall credibility required
MIN_FACT_ACCURACY = 0.9      # 90% of facts must be verified
```

## Model Configuration

### Default Models
```python
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
```

## Research Budgets

### API Call Limits
```python
MAX_WEB_CALLS = 100          # Maximum web searches per research
MAX_FILE_CALLS = 15          # Maximum knowledge base searches
```

### Token Limits
```python
OUTPUT_TOKEN_CAPS = {
    "synth_max_tokens": 3000,      # Research synthesis
    "metrics_max_tokens": 1500,    # Quality metrics
    "seo_max_tokens": 1500,        # SEO metadata
    "factcheck_max_tokens": 2000,  # Fact checking
    "summary_max_tokens": 1000,    # Executive summary
    "social_max_tokens": 800,      # Social media posts
}
```

## Feature Flags

```python
ENABLE_EVIDENCE = True       # Generate evidence tracking
ENABLE_CLAIM_CHECK = True    # Verify all claims
ENABLE_SEO = True           # Generate SEO metadata
ENABLE_METRICS = True       # Track quality metrics
ENABLE_SUMMARY = True       # Create executive summaries
ENABLE_SOCIAL = True        # Generate social media content
FACT_CHECK_MANDATORY = True # Cannot skip fact-checking
```

## Content Standards

### Required Sections
```python
REQUIRED_SECTIONS = [
    "Key Insights at a Glance",
    "Key Takeaways",
    "Conclusion"
]
```

### Forbidden Sections
```python
FORBIDDEN_SECTIONS = [
    "Introduction",
    "Executive Summary",  # Separate deliverable
    "About Dakota",
    "Disclaimer"
]
```

## Citation Standards

### Source Requirements
```python
CITATION_STANDARDS = {
    "require_primary_sources": True,
    "max_source_age_months": 12,
    "require_publication_date": True,
    "require_author_attribution": True,
}
```

### Domain Preferences
```python
"preferred_domains": [
    "sec.gov",
    "federalreserve.gov",
    "imf.org",
    "worldbank.org",
    "nber.org",
    "jstor.org",
    "bloomberg.com",
    "wsj.com",
    "ft.com",
    "reuters.com"
]

"banned_domains": [
    "wikipedia.org",     # No Wikipedia as primary source
    "reddit.com",
    "quora.com",
    "medium.com"         # Unless verified expert
]
```

## Validation Rules

### Structure Validation
```python
VALIDATION_RULES = {
    "structure": {
        "require_yaml_frontmatter": True,
        "require_all_sections": True,
        "max_heading_depth": 3,
        "require_internal_links": True
    }
}
```

### Content Validation
```python
"content": {
    "max_passive_voice_percentage": 20,
    "max_sentence_length": 30,  # words
    "require_data_points": True,
    "min_examples_per_section": 1
}
```

### Style Guidelines
```python
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
```

## Directory Configuration

```python
PROJECT_ROOT = Path(__file__).parent.parent
RUNS_DIR = PROJECT_ROOT / "runs"
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"
```

## Logging Configuration

```python
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
```

## Quality Report Settings

```python
QUALITY_REPORT_CONFIG = {
    "generate_report": True,
    "include_metrics": True,
    "include_validation_details": True,
    "include_source_analysis": True,
    "include_readability_scores": True,
    "export_format": "markdown"  # or "json"
}
```

## Customization Examples

### Stricter Quality Standards
```python
# In config_enhanced.py
MIN_WORD_COUNT = 2500        # Increase minimum
MIN_SOURCES = 15             # More sources required
MIN_CREDIBILITY = 0.85       # Higher credibility bar
```

### Different Models
```python
# Use GPT-3.5 for cost savings
DEFAULT_MODELS = {
    "web_researcher": "gpt-3.5-turbo",
    "writer": "gpt-4",  # Keep GPT-4 for writing
    # ...
}
```

### Disable Features
```python
ENABLE_SOCIAL = False        # Skip social media generation
ENABLE_SEO = False          # Skip SEO metadata
```

## Override at Runtime

Some settings can be overridden:
```bash
# Custom word count
python main_chat.py generate "topic" --words 3000

# Quick mode (overrides MIN_WORD_COUNT to 500)
python main_chat.py generate "topic" --quick
```