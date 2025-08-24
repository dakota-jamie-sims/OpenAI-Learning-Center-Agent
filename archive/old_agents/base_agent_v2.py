"""Base agent V2 with connection pooling and optimizations"""

import asyncio
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from src.services.openai_connection_pool import acquire_openai_client
from src.config import DEFAULT_MODELS
from src.utils.logging import get_logger
from src.utils.circuit_breaker import CircuitBreaker
from prometheus_client import Counter, Histogram

logger = get_logger(__name__)

# Metrics
agent_requests = Counter('agent_requests_total', 'Total agent requests', ['agent', 'status'])
agent_duration = Histogram('agent_duration_seconds', 'Agent execution duration', ['agent'])
llm_requests = Counter('llm_requests_total', 'Total LLM requests', ['agent', 'model'])
llm_duration = Histogram('llm_duration_seconds', 'LLM request duration', ['agent', 'model'])


class DakotaBaseAgentV2:
    """Optimized base agent with connection pooling"""
    
    def __init__(self, agent_name: str, model_override: Optional[str] = None):
        self.agent_name = agent_name
        self.logger = get_logger(f"dakota.{agent_name}")
        
        # Optimized model selection
        self.model = self._select_model(agent_name, model_override)
        
        # Determine connection pool based on agent type
        self.pool_name = self._get_pool_name(agent_name)
        
        # Circuit breaker for this agent
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30
        )
        
        # Agent state
        self.status = "ready"
        self.current_task = None
        self.history = []
        
        # Response cache (agent-level)
        self.response_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    def _select_model(self, agent_name: str, model_override: Optional[str]) -> str:
        """Select optimal model for agent type"""
        if model_override:
            return model_override
            
        # Optimized model mapping for speed
        model_map = {
            # Lightweight tasks
            "orchestrator": "gpt-5-nano",
            "kb_researcher": "gpt-5-nano",
            "metrics_analyzer": "gpt-5-nano",
            "seo_specialist": "gpt-5-nano",
            "social_promoter": "gpt-5-nano",
            
            # Medium complexity
            "web_researcher": "gpt-5-mini",
            "fact_checker": "gpt-5-mini",
            "summary_writer": "gpt-5-mini",
            "iteration_manager": "gpt-5-mini",
            
            # Heavy reasoning
            "research_synthesizer": "gpt-5",
            "content_writer": "gpt-5",
        }
        
        return model_map.get(agent_name, "gpt-5-mini")
    
    def _get_pool_name(self, agent_name: str) -> str:
        """Get appropriate connection pool for agent"""
        if agent_name in ["kb_researcher", "web_researcher"]:
            return "search"
        elif agent_name in ["content_writer", "research_synthesizer"]:
            return "content"
        elif agent_name == "orchestrator":
            return "orchestrator"
        else:
            return "analysis"
    
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute task with metrics"""
        agent_requests.labels(agent=self.agent_name, status="started").inc()
        start_time = time.time()
        
        try:
            with agent_duration.labels(agent=self.agent_name).time():
                result = await self._execute_impl(task)
                
            agent_requests.labels(agent=self.agent_name, status="success").inc()
            return result
            
        except Exception as e:
            agent_requests.labels(agent=self.agent_name, status="error").inc()
            self.logger.error(f"Agent execution error: {e}")
            return self.format_response(False, error=str(e))
    
    async def _execute_impl(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """To be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _execute_impl()")
    
    async def query_llm(self, prompt: str, max_tokens: int = 1000, 
                       reasoning_effort: str = "minimal",
                       use_cache: bool = True) -> str:
        """Query LLM with connection pooling and caching"""
        
        # Check cache first
        if use_cache:
            cache_key = f"{self.model}:{hash(prompt)}"
            if cache_key in self.response_cache:
                cached_time, cached_response = self.response_cache[cache_key]
                if time.time() - cached_time < self.cache_ttl:
                    self.logger.debug("Cache hit for LLM query")
                    return cached_response
        
        llm_requests.labels(agent=self.agent_name, model=self.model).inc()
        
        async with acquire_openai_client(self.pool_name) as client:
            try:
                with llm_duration.labels(agent=self.agent_name, model=self.model).time():
                    # Use circuit breaker
                    response = await self.circuit_breaker.call(
                        self._make_llm_call,
                        client, prompt, max_tokens, reasoning_effort
                    )
                
                # Extract text efficiently
                text = self._extract_text(response)
                
                # Cache response
                if use_cache and text:
                    self.response_cache[cache_key] = (time.time(), text)
                
                return text
                
            except Exception as e:
                self.logger.error(f"LLM query error: {e}")
                raise
    
    async def _make_llm_call(self, client, prompt: str, max_tokens: int, reasoning_effort: str) -> Any:
        """Make actual LLM call with timeout"""
        create_params = {
            "model": self.model,
            "input": prompt,
            "reasoning": {"effort": reasoning_effort},
            "text": {"verbosity": "low"},
            "max_completion_tokens": max_tokens
        }
        
        # Don't add temperature for GPT-5 models
        if not self.model.startswith("gpt-5"):
            create_params["temperature"] = 0.3
        
        # Use asyncio timeout
        async def _do_call():
            return await asyncio.to_thread(
                client.responses.create,
                **create_params
            )
        
        return await asyncio.wait_for(_do_call(), timeout=30)
    
    def _extract_text(self, response) -> str:
        """Fast text extraction from response"""
        # Try direct output_text first (fastest)
        if hasattr(response, 'output_text') and response.output_text:
            return response.output_text
        
        # Try output array
        if hasattr(response, 'output') and response.output:
            for item in response.output:
                # Skip reasoning items
                if hasattr(item, 'type') and item.type == 'reasoning':
                    continue
                    
                # Extract from message items
                if hasattr(item, 'content'):
                    if isinstance(item.content, str):
                        return item.content
                    elif isinstance(item.content, list) and item.content:
                        if hasattr(item.content[0], 'text'):
                            return item.content[0].text
        
        return "Content generation in progress..."
    
    def update_status(self, status: str, message: str = ""):
        """Update agent status"""
        self.status = status
        self.logger.info(f"Status: {status} - {message}")
    
    def format_response(self, success: bool, data: Any = None, error: str = None) -> Dict[str, Any]:
        """Format standardized response"""
        response = {
            "success": success,
            "agent": self.agent_name,
            "timestamp": datetime.now().isoformat()
        }
        
        if data is not None:
            response["data"] = data
        
        if error:
            response["error"] = error
            
        return response
    
    def clear_cache(self):
        """Clear response cache"""
        self.response_cache.clear()
        self.logger.info("Cleared response cache")