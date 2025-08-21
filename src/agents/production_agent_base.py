"""Production-ready base agent with robust error handling"""

import asyncio
import time
from typing import Dict, Any, Optional, Union
from functools import wraps
import logging

from src.agents.multi_agent_base import BaseAgent, AgentMessage, LLMAPIError
from src.services.openai_responses_client import ResponsesClient, TransientOpenAIError
from src.config_production import (
    TIMEOUTS, RETRY_CONFIG, LLM_OPTIMIZATION, 
    CIRCUIT_BREAKER, get_production_config
)
from src.utils.circuit_breaker import with_circuit_breaker
from functools import lru_cache

logger = logging.getLogger(__name__)


def with_timeout(timeout_key: str = "agent_task"):
    """Decorator to add timeout to agent methods"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            timeout = TIMEOUTS.get(timeout_key, 60)
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"Timeout after {timeout}s in {func.__name__}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we'll rely on the underlying timeout
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


def with_retry(max_attempts: Optional[int] = None):
    """Decorator to add retry logic"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            attempts = max_attempts or RETRY_CONFIG["max_attempts"]
            delay = RETRY_CONFIG["initial_delay"]
            
            for attempt in range(attempts):
                try:
                    return await func(*args, **kwargs)
                except TransientOpenAIError as e:
                    if attempt == attempts - 1:
                        raise
                    logger.warning(
                        f"Retry {attempt + 1}/{attempts} after error: {e}"
                    )
                    await asyncio.sleep(delay)
                    delay = min(delay * RETRY_CONFIG["exponential_base"], 
                              RETRY_CONFIG["max_delay"])
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            attempts = max_attempts or RETRY_CONFIG["max_attempts"]
            delay = RETRY_CONFIG["initial_delay"]
            
            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except TransientOpenAIError as e:
                    if attempt == attempts - 1:
                        raise
                    logger.warning(
                        f"Retry {attempt + 1}/{attempts} after error: {e}"
                    )
                    time.sleep(delay)
                    delay = min(delay * RETRY_CONFIG["exponential_base"], 
                              RETRY_CONFIG["max_delay"])
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


class ProductionAgent(BaseAgent):
    """Production-ready agent with enhanced error handling and monitoring"""
    
    def __init__(self, agent_id: str, agent_type: str, team: str = None):
        super().__init__(agent_id, agent_type, team)
        
        # Use production configuration
        self.config = get_production_config()
        self.timeouts = self.config["timeouts"]
        
        # Initialize production ResponsesClient
        self.responses_client = ResponsesClient(
            timeout=self.timeouts["llm_call"],
            max_retries=RETRY_CONFIG["max_attempts"]
        )
        
        # Simple cache for expensive operations
        self._cache = {}
        self._cache_timestamps = {}
        
        # Metrics tracking
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_latency": 0,
            "cache_hits": 0,
            "cache_misses": 0,
        }
        
        # Use production models
        self.model = self.config["models"].get(
            agent_type.lower(), 
            self.config["models"]["default"]
        )
    
    @with_circuit_breaker(
        name="llm_calls",
        failure_threshold=CIRCUIT_BREAKER["failure_threshold"],
        recovery_timeout=CIRCUIT_BREAKER["recovery_timeout"],
        expected_exception=LLMAPIError
    )
    @with_retry()
    def query_llm(
        self,
        prompt: str,
        reasoning_effort: Optional[str] = None,
        verbosity: Optional[str] = None,
        timeout: Optional[float] = None,
        max_tokens: Optional[int] = None,
        use_cache: bool = True,
        **kwargs,
    ) -> str:
        """Production-ready LLM query with caching and error handling"""
        start_time = time.time()
        self.metrics["total_requests"] += 1
        
        # Use production defaults
        reasoning_effort = reasoning_effort or LLM_OPTIMIZATION["default_reasoning_effort"]
        verbosity = verbosity or LLM_OPTIMIZATION["default_verbosity"]
        timeout = timeout or self.timeouts["llm_call"]
        max_tokens = max_tokens or LLM_OPTIMIZATION["max_output_tokens"]
        
        # Truncate prompt if too long
        if len(prompt) > LLM_OPTIMIZATION["max_prompt_length"]:
            logger.warning(f"Truncating prompt from {len(prompt)} to {LLM_OPTIMIZATION['max_prompt_length']} chars")
            prompt = prompt[:LLM_OPTIMIZATION["max_prompt_length"]]
        
        # Check cache
        cache_key = f"{self.model}:{prompt[:100]}:{reasoning_effort}:{verbosity}"
        if use_cache and self.config["cache"]["enable_caching"]:
            # Simple TTL check
            if cache_key in self._cache:
                cache_time = self._cache_timestamps.get(cache_key, 0)
                if time.time() - cache_time < self.config["cache"]["cache_ttl"]:
                    self.metrics["cache_hits"] += 1
                    self.metrics["successful_requests"] += 1
                    return self._cache[cache_key]
            self.metrics["cache_misses"] += 1
        
        try:
            # Remove max_tokens from kwargs if present
            filtered_kwargs = {k: v for k, v in kwargs.items() if k != "max_tokens"}
            
            # Don't pass temperature for GPT-5 models
            create_params = {
                "model": self.model,
                "input_text": prompt,
                "reasoning_effort": reasoning_effort,
                "verbosity": verbosity,
                "timeout": timeout,
                "max_tokens": max_tokens,
                **filtered_kwargs,
            }
            
            # Only add temperature for models that support it
            if not self.model.startswith("gpt-5"):
                create_params["temperature"] = LLM_OPTIMIZATION.get("temperature", 0.3)
            
            response = self.responses_client.create_response(**create_params)
            
            # Extract text content
            result = self._extract_response_text(response)
            
            # Cache successful result
            if use_cache and self.config["cache"]["enable_caching"]:
                self._cache[cache_key] = result
                self._cache_timestamps[cache_key] = time.time()
                
                # Cleanup old cache entries
                if len(self._cache) > self.config["cache"]["max_cache_size"]:
                    # Remove oldest entries
                    oldest = sorted(self._cache_timestamps.items(), key=lambda x: x[1])[:10]
                    for old_key, _ in oldest:
                        self._cache.pop(old_key, None)
                        self._cache_timestamps.pop(old_key, None)
            
            # Update metrics
            self.metrics["successful_requests"] += 1
            self.metrics["total_latency"] += time.time() - start_time
            
            # Log slow operations
            elapsed = time.time() - start_time
            if elapsed > self.config["monitoring"]["slow_operation_threshold"]:
                logger.warning(f"Slow LLM operation: {elapsed:.2f}s for {self.agent_id}")
            
            return result
            
        except Exception as e:
            self.metrics["failed_requests"] += 1
            logger.error(f"LLM query failed for {self.agent_id}: {e}")
            
            # Try fallback if enabled
            if self.config["features"]["enable_fallback_models"]:
                return self._fallback_query(prompt, reasoning_effort, verbosity)
            
            raise LLMAPIError(str(e))
    
    def _extract_response_text(self, response) -> str:
        """Extract text from various response formats"""
        # Responses API format
        if hasattr(response, 'content') and response.content:
            if isinstance(response.content, list) and len(response.content) > 0:
                if hasattr(response.content[0], 'text'):
                    return response.content[0].text
        
        # Fallback for output_text helper
        if hasattr(response, 'output_text'):
            return response.output_text
        
        # Chat Completions API format
        if hasattr(response, "choices") and response.choices:
            return response.choices[0].message.content
        
        # Last resort
        return str(response)
    
    def _fallback_query(self, prompt: str, reasoning_effort: str, verbosity: str) -> str:
        """Fallback query with simpler model"""
        logger.info(f"Attempting fallback query for {self.agent_id}")
        
        # Use nano model for fallback
        fallback_model = "gpt-5-nano"
        
        try:
            # No temperature for GPT-5 models
            response = self.responses_client.create_response(
                model=fallback_model,
                input_text=prompt[:1000],  # Shorter prompt
                reasoning_effort="minimal",
                verbosity="low",
                timeout=10,
                max_tokens=200,
            )
            return self._extract_response_text(response)
        except Exception as e:
            logger.error(f"Fallback query also failed: {e}")
            return "Error: Unable to process request. Please try again."
    
    @with_timeout("agent_task")
    async def process_message_async(self, message: AgentMessage) -> AgentMessage:
        """Async message processing with timeout"""
        return self.process_message(message)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get agent performance metrics"""
        avg_latency = (
            self.metrics["total_latency"] / self.metrics["successful_requests"]
            if self.metrics["successful_requests"] > 0
            else 0
        )
        
        return {
            **self.metrics,
            "average_latency": avg_latency,
            "success_rate": (
                self.metrics["successful_requests"] / self.metrics["total_requests"]
                if self.metrics["total_requests"] > 0
                else 0
            ),
            "cache_hit_rate": (
                self.metrics["cache_hits"] / 
                (self.metrics["cache_hits"] + self.metrics["cache_misses"])
                if (self.metrics["cache_hits"] + self.metrics["cache_misses"]) > 0
                else 0
            ),
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "model": self.model,
            "metrics": self.get_metrics(),
            "cache_size": len(self._cache),
            "memory_count": len(self.memory),
        }