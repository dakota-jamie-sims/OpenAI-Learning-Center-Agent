from dataclasses import dataclass, field
from pathlib import Path
import os


def _default_output_dir() -> str:
    env = os.getenv("DAKOTA_OUTPUT_DIR")
    if env:
        path = Path(env).expanduser().resolve()
    else:
        path = Path(__file__).resolve().parents[3] / "Dakota Learning Center Articles"
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def _prompts_dir() -> str:
    return str(Path(__file__).resolve().parents[1] / "prompts")


def _knowledge_base_dir() -> str:
    return str(Path(__file__).resolve().parents[1] / "knowledge_base")


@dataclass
class Settings:
    # Vector store
    VECTOR_STORE_ID: str | None = field(default_factory=lambda: os.getenv("VECTOR_STORE_ID") or None)

    # Model configuration
    ORCHESTRATOR_MODEL: str = field(default_factory=lambda: os.getenv("ORCHESTRATOR_MODEL", "gpt-4.1"))
    WEB_RESEARCHER_MODEL: str = field(default_factory=lambda: os.getenv("WEB_RESEARCHER_MODEL", "gpt-4.1"))
    KB_RESEARCHER_MODEL: str = field(default_factory=lambda: os.getenv("KB_RESEARCHER_MODEL", "gpt-4.1-mini"))
    SYNTHESIZER_MODEL: str = field(default_factory=lambda: os.getenv("SYNTHESIZER_MODEL", "gpt-4.1"))
    WRITER_MODEL: str = field(default_factory=lambda: os.getenv("WRITER_MODEL", "gpt-4.1"))
    SEO_MODEL: str = field(default_factory=lambda: os.getenv("SEO_MODEL", "gpt-4.1-mini"))
    FACT_CHECKER_MODEL: str = field(default_factory=lambda: os.getenv("FACT_CHECKER_MODEL", "gpt-4.1"))
    SUMMARY_MODEL: str = field(default_factory=lambda: os.getenv("SUMMARY_MODEL", "gpt-4.1-mini"))
    SOCIAL_MODEL: str = field(default_factory=lambda: os.getenv("SOCIAL_MODEL", "gpt-4.1-mini"))
    ITERATION_MODEL: str = field(default_factory=lambda: os.getenv("ITERATION_MODEL", "gpt-4.1"))
    METRICS_MODEL: str = field(default_factory=lambda: os.getenv("METRICS_MODEL", "gpt-4.1-mini"))
    EVIDENCE_MODEL: str = field(default_factory=lambda: os.getenv("EVIDENCE_MODEL", "gpt-4.1"))
    CLAIM_CHECKER_MODEL: str = field(default_factory=lambda: os.getenv("CLAIM_CHECKER_MODEL", "gpt-4.1-mini"))

    # Budget & caps
    BUDGET_USD: float = field(default_factory=lambda: float(os.getenv("BUDGET_USD", "1.50")))
    MAX_WEB_CALLS: int = field(default_factory=lambda: int(os.getenv("MAX_WEB_CALLS", "80")))
    MAX_FILE_CALLS: int = field(default_factory=lambda: int(os.getenv("MAX_FILE_CALLS", "10")))

    WRITER_MAX_TOKENS: int = field(default_factory=lambda: int(os.getenv("WRITER_MAX_TOKENS", "3500")))
    SUMMARY_MAX_TOKENS: int = field(default_factory=lambda: int(os.getenv("SUMMARY_MAX_TOKENS", "500")))
    SOCIAL_MAX_TOKENS: int = field(default_factory=lambda: int(os.getenv("SOCIAL_MAX_TOKENS", "900")))
    SEO_MAX_TOKENS: int = field(default_factory=lambda: int(os.getenv("SEO_MAX_TOKENS", "900")))
    METRICS_MAX_TOKENS: int = field(default_factory=lambda: int(os.getenv("METRICS_MAX_TOKENS", "700")))
    SYNTH_MAX_TOKENS: int = field(default_factory=lambda: int(os.getenv("SYNTH_MAX_TOKENS", "1600")))
    FACTCHECK_MAX_TOKENS: int = field(default_factory=lambda: int(os.getenv("FACTCHECK_MAX_TOKENS", "1000")))

    # Feature toggles
    ENABLE_EVIDENCE: bool = field(default_factory=lambda: os.getenv("ENABLE_EVIDENCE", "1") == "1")
    ENABLE_CLAIM_CHECK: bool = field(default_factory=lambda: os.getenv("ENABLE_CLAIM_CHECK", "1") == "1")
    ENABLE_SUMMARY: bool = field(default_factory=lambda: os.getenv("ENABLE_SUMMARY", "1") == "1")
    ENABLE_SOCIAL: bool = field(default_factory=lambda: os.getenv("ENABLE_SOCIAL", "1") == "1")
    ENABLE_METRICS: bool = field(default_factory=lambda: os.getenv("ENABLE_METRICS", "1") == "1")
    ENABLE_SEO: bool = field(default_factory=lambda: os.getenv("ENABLE_SEO", "1") == "1")

    # Quality requirements
    MIN_WORD_COUNT: int = field(default_factory=lambda: int(os.getenv("MIN_WORD_COUNT", "1750")))
    MIN_SOURCES: int = field(default_factory=lambda: int(os.getenv("MIN_SOURCES", "10")))
    MAX_ITERATIONS: int = field(default_factory=lambda: int(os.getenv("MAX_ITERATIONS", "2")))
    REQUIRE_URL_VERIFICATION: bool = field(default_factory=lambda: os.getenv("REQUIRE_URL_VERIFICATION", "true").lower() == "true")
    REQUIRE_DAKOTA_URLS: bool = field(default_factory=lambda: os.getenv("REQUIRE_DAKOTA_URLS", "true").lower() == "true")
    FACT_CHECK_MANDATORY: bool = field(default_factory=lambda: os.getenv("FACT_CHECK_MANDATORY", "true").lower() == "true")

    # Directories
    OUTPUT_BASE_DIR: str = field(default_factory=_default_output_dir)
    RUNS_DIR: str = field(init=False)
    PROMPTS_DIR: str = field(default_factory=_prompts_dir)
    KNOWLEDGE_BASE_DIR: str = field(default_factory=_knowledge_base_dir)

    def __post_init__(self):
        self.RUNS_DIR = self.OUTPUT_BASE_DIR

    @property
    def DEFAULT_MODELS(self) -> dict:
        return {
            "orchestrator": self.ORCHESTRATOR_MODEL,
            "web_researcher": self.WEB_RESEARCHER_MODEL,
            "kb_researcher": self.KB_RESEARCHER_MODEL,
            "synthesizer": self.SYNTHESIZER_MODEL,
            "writer": self.WRITER_MODEL,
            "seo": self.SEO_MODEL,
            "fact_checker": self.FACT_CHECKER_MODEL,
            "summary": self.SUMMARY_MODEL,
            "social": self.SOCIAL_MODEL,
            "iteration": self.ITERATION_MODEL,
            "metrics": self.METRICS_MODEL,
            "evidence": self.EVIDENCE_MODEL,
            "claim_checker": self.CLAIM_CHECKER_MODEL,
        }

    @property
    def OUTPUT_TOKEN_CAPS(self) -> dict:
        return {
            "writer_max_tokens": self.WRITER_MAX_TOKENS,
            "summary_max_tokens": self.SUMMARY_MAX_TOKENS,
            "social_max_tokens": self.SOCIAL_MAX_TOKENS,
            "seo_max_tokens": self.SEO_MAX_TOKENS,
            "metrics_max_tokens": self.METRICS_MAX_TOKENS,
            "synth_max_tokens": self.SYNTH_MAX_TOKENS,
            "factcheck_max_tokens": self.FACTCHECK_MAX_TOKENS,
        }
