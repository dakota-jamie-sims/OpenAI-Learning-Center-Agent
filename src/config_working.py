"""Environment-specific configuration overrides.

This module is optional and provides overrides for the default settings in
``config.py``.  It is intended for local or experimental setups where different
model selections or paths are required.  ``config.py`` will automatically load
any variables defined here if the file exists.
"""

from pathlib import Path

# Example: override output directory to stay within the repository
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "output"
RUNS_DIR = OUTPUT_DIR

# Example: use older, generally available model names
DEFAULT_MODELS = {
    "web_researcher": "gpt-4-turbo-preview",
    "kb_researcher": "gpt-4-turbo-preview",
    "synthesizer": "gpt-4-turbo-preview",
    "writer": "gpt-4-turbo-preview",
    "fact_checker": "gpt-4-turbo-preview",
    "claim_checker": "gpt-4-turbo-preview",
    "summary": "gpt-4-turbo-preview",
    "social": "gpt-3.5-turbo",
    "seo": "gpt-3.5-turbo",
    "metrics": "gpt-3.5-turbo",
    "iteration": "gpt-4-turbo-preview",
    "evidence": "gpt-4-turbo-preview",
}

