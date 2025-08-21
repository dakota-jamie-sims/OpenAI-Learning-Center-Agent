"""Production configuration for multi-agent system"""

import os
from typing import Dict, Any

# Production timeouts (in seconds)
TIMEOUTS = {
    "llm_call": 45,          # Individual LLM call timeout
    "web_search": 10,        # Web search timeout
    "kb_search": 20,         # Knowledge base search timeout
    "agent_task": 60,        # Individual agent task timeout
    "total_generation": 300, # Total article generation timeout (5 minutes)
}

# Retry configuration
RETRY_CONFIG = {
    "max_attempts": 3,
    "initial_delay": 1,      # seconds
    "max_delay": 10,         # seconds
    "exponential_base": 2,
}

# Rate limiting
RATE_LIMITS = {
    "llm_calls_per_minute": 20,
    "web_searches_per_minute": 30,
    "kb_searches_per_minute": 30,
}

# Circuit breaker settings
CIRCUIT_BREAKER = {
    "failure_threshold": 3,   # Failures before opening circuit
    "recovery_timeout": 30,   # Seconds before attempting recovery
    "half_open_requests": 1,  # Test requests in half-open state
}

# Production model configuration - optimized for speed and reliability
PRODUCTION_MODELS = {
    "default": "gpt-5-mini",           # Faster default model
    "orchestrator": "gpt-5-mini",      # Orchestrator doesn't need heavy reasoning
    "web_researcher": "gpt-5-mini",    # Fast web analysis
    "kb_researcher": "gpt-5-nano",     # Lightweight KB search
    "synthesizer": "gpt-5",           # Full model for synthesis
    "writer": "gpt-5",                # Full model for writing
    "seo": "gpt-5-nano",              # Lightweight SEO
    "fact_checker": "gpt-5-mini",     # Balanced fact checking
    "summary": "gpt-5-nano",          # Lightweight summaries
    "social": "gpt-5-nano",           # Lightweight social media
    "iteration": "gpt-5-mini",        # Balanced iteration
    "metrics": "gpt-5-nano",          # Lightweight metrics
    "evidence": "gpt-5-mini",         # Balanced evidence
    "claim_checker": "gpt-5-nano",    # Lightweight claims
    "metadata": "gpt-5-nano",         # Lightweight metadata
}

# LLM call optimization
LLM_OPTIMIZATION = {
    "default_reasoning_effort": "minimal",
    "default_verbosity": "low",
    "max_prompt_length": 2000,        # Characters
    "max_output_tokens": 500,         # Default max tokens
    "temperature": 0.3,               # Lower temperature for consistency
}

# Caching configuration
CACHE_CONFIG = {
    "enable_caching": True,
    "cache_ttl": 300,                 # 5 minutes
    "max_cache_size": 1000,           # Maximum cached items
    "cache_web_searches": True,
    "cache_kb_searches": True,
    "cache_llm_calls": False,         # Don't cache LLM calls
}

# Error handling
ERROR_HANDLING = {
    "fallback_on_timeout": True,
    "use_cached_on_error": True,
    "max_consecutive_failures": 5,
    "error_notification_threshold": 3,
}

# Monitoring and metrics
MONITORING = {
    "enable_metrics": True,
    "metrics_interval": 60,           # Seconds
    "log_slow_operations": True,
    "slow_operation_threshold": 10,   # Seconds
    "enable_health_checks": True,
    "health_check_interval": 30,      # Seconds
}

# Agent configuration
AGENT_CONFIG = {
    "max_concurrent_agents": 5,
    "agent_timeout_multiplier": 1.5,  # Agent timeout = task_timeout * multiplier
    "enable_agent_pooling": True,
    "agent_pool_size": 10,
    "agent_keepalive": 300,           # Seconds
}

# Production feature flags
FEATURE_FLAGS = {
    "enable_parallel_research": True,
    "enable_smart_chunking": True,
    "enable_response_streaming": False,  # Not yet implemented
    "enable_fallback_models": True,
    "enable_request_deduplication": True,
    "enable_progressive_enhancement": True,
}

# Quality thresholds
QUALITY_THRESHOLDS = {
    "min_research_sources": 3,        # Minimum sources before writing
    "min_confidence_score": 0.7,      # Minimum confidence for facts
    "max_hallucination_score": 0.2,   # Maximum allowed hallucination
    "min_coherence_score": 0.8,       # Minimum text coherence
}

# Resource limits
RESOURCE_LIMITS = {
    "max_memory_mb": 512,             # Maximum memory per request
    "max_cpu_seconds": 60,            # Maximum CPU time per request
    "max_tokens_per_request": 10000,  # Maximum total tokens
    "max_api_calls_per_request": 50,  # Maximum API calls
}

def get_production_config() -> Dict[str, Any]:
    """Get complete production configuration"""
    return {
        "timeouts": TIMEOUTS,
        "retry": RETRY_CONFIG,
        "rate_limits": RATE_LIMITS,
        "circuit_breaker": CIRCUIT_BREAKER,
        "models": PRODUCTION_MODELS,
        "llm_optimization": LLM_OPTIMIZATION,
        "cache": CACHE_CONFIG,
        "error_handling": ERROR_HANDLING,
        "monitoring": MONITORING,
        "agents": AGENT_CONFIG,
        "features": FEATURE_FLAGS,
        "quality": QUALITY_THRESHOLDS,
        "resources": RESOURCE_LIMITS,
    }

# Environment-specific overrides
if os.getenv("ENVIRONMENT") == "production":
    # Production overrides
    TIMEOUTS["llm_call"] = 30
    RATE_LIMITS["llm_calls_per_minute"] = 30
elif os.getenv("ENVIRONMENT") == "staging":
    # Staging overrides
    MONITORING["metrics_interval"] = 30
    CACHE_CONFIG["cache_ttl"] = 600