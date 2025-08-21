"""Rate limiter for API calls"""

import time
import threading
from collections import deque
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, rate: float, capacity: int, name: str = "RateLimiter"):
        """
        Args:
            rate: Tokens per second to add
            capacity: Maximum bucket capacity
            name: Name for logging
        """
        self.rate = rate
        self.capacity = capacity
        self.name = name
        
        self.tokens = capacity
        self.last_update = time.time()
        self._lock = threading.Lock()
        
        # Track recent requests for monitoring
        self.request_times = deque(maxlen=1000)
    
    def acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """
        Acquire tokens from the bucket
        
        Args:
            tokens: Number of tokens to acquire
            timeout: Maximum time to wait for tokens
            
        Returns:
            True if tokens were acquired, False if timeout
        """
        start_time = time.time()
        
        while True:
            with self._lock:
                self._refill()
                
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    self.request_times.append(time.time())
                    return True
                
                if timeout is not None and (time.time() - start_time) >= timeout:
                    logger.warning(
                        f"{self.name}: Rate limit timeout after {timeout}s "
                        f"(needed {tokens} tokens, have {self.tokens:.2f})"
                    )
                    return False
            
            # Wait a bit before trying again
            time.sleep(0.1)
    
    def _refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_update
        
        # Add tokens based on rate
        new_tokens = elapsed * self.rate
        self.tokens = min(self.tokens + new_tokens, self.capacity)
        self.last_update = now
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics"""
        with self._lock:
            now = time.time()
            recent_requests = [t for t in self.request_times if now - t < 60]
            
            return {
                "name": self.name,
                "current_tokens": self.tokens,
                "capacity": self.capacity,
                "rate": self.rate,
                "requests_per_minute": len(recent_requests),
            }


class RateLimiterGroup:
    """Manages multiple rate limiters"""
    
    def __init__(self):
        self.limiters = {}
        self._lock = threading.Lock()
    
    def add_limiter(self, name: str, rate: float, capacity: int):
        """Add a new rate limiter"""
        with self._lock:
            self.limiters[name] = RateLimiter(rate, capacity, name)
    
    def acquire(self, name: str, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        """Acquire tokens from a specific limiter"""
        limiter = self.limiters.get(name)
        if not limiter:
            logger.warning(f"Rate limiter '{name}' not found")
            return True  # Allow if limiter doesn't exist
        
        return limiter.acquire(tokens, timeout)
    
    def get_all_stats(self) -> dict:
        """Get statistics for all limiters"""
        with self._lock:
            return {
                name: limiter.get_stats()
                for name, limiter in self.limiters.items()
            }


# Global rate limiter group
rate_limiter_group = RateLimiterGroup()


def with_rate_limit(limiter_name: str, tokens: int = 1, timeout: float = 10):
    """Decorator to add rate limiting to functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not rate_limiter_group.acquire(limiter_name, tokens, timeout):
                raise Exception(f"Rate limit exceeded for {limiter_name}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


# Initialize default rate limiters
def init_default_limiters():
    """Initialize rate limiters based on production config"""
    from src.config_production import RATE_LIMITS
    
    # LLM calls limiter (per minute -> per second)
    rate_limiter_group.add_limiter(
        "llm_calls",
        rate=RATE_LIMITS["llm_calls_per_minute"] / 60,
        capacity=RATE_LIMITS["llm_calls_per_minute"]
    )
    
    # Web search limiter
    rate_limiter_group.add_limiter(
        "web_searches",
        rate=RATE_LIMITS["web_searches_per_minute"] / 60,
        capacity=RATE_LIMITS["web_searches_per_minute"]
    )
    
    # KB search limiter
    rate_limiter_group.add_limiter(
        "kb_searches",
        rate=RATE_LIMITS["kb_searches_per_minute"] / 60,
        capacity=RATE_LIMITS["kb_searches_per_minute"]
    )
    
    logger.info("Default rate limiters initialized")