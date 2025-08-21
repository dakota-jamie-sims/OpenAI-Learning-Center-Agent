"""Circuit breaker pattern for fault tolerance"""

import time
import threading
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """Circuit breaker to prevent cascading failures"""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 30,
        expected_exception: type = Exception,
        name: str = "CircuitBreaker"
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self._lock = threading.Lock()
        
    def __call__(self, func: Callable) -> Callable:
        """Decorator to wrap functions with circuit breaker"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        return wrapper
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection"""
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"{self.name}: Circuit half-open, attempting reset")
                else:
                    raise Exception(f"{self.name}: Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit"""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful call"""
        with self._lock:
            self.failure_count = 0
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                logger.info(f"{self.name}: Circuit closed, recovered successfully")
    
    def _on_failure(self):
        """Handle failed call"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(
                    f"{self.name}: Circuit opened after {self.failure_count} failures"
                )
    
    def reset(self):
        """Manually reset the circuit breaker"""
        with self._lock:
            self.failure_count = 0
            self.last_failure_time = None
            self.state = CircuitState.CLOSED
            logger.info(f"{self.name}: Circuit manually reset")
    
    def get_state(self) -> dict:
        """Get current circuit breaker state"""
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "last_failure_time": self.last_failure_time,
            }


class CircuitBreakerManager:
    """Manages multiple circuit breakers"""
    
    def __init__(self):
        self.breakers = {}
        self._lock = threading.Lock()
    
    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30,
        expected_exception: type = Exception
    ) -> CircuitBreaker:
        """Get existing or create new circuit breaker"""
        with self._lock:
            if name not in self.breakers:
                self.breakers[name] = CircuitBreaker(
                    failure_threshold=failure_threshold,
                    recovery_timeout=recovery_timeout,
                    expected_exception=expected_exception,
                    name=name
                )
            return self.breakers[name]
    
    def reset_all(self):
        """Reset all circuit breakers"""
        with self._lock:
            for breaker in self.breakers.values():
                breaker.reset()
    
    def get_states(self) -> dict:
        """Get states of all circuit breakers"""
        with self._lock:
            return {
                name: breaker.get_state()
                for name, breaker in self.breakers.items()
            }


# Global circuit breaker manager
circuit_manager = CircuitBreakerManager()


def with_circuit_breaker(
    name: str,
    failure_threshold: int = 3,
    recovery_timeout: float = 30,
    expected_exception: type = Exception
):
    """Decorator to add circuit breaker to a function"""
    def decorator(func):
        breaker = circuit_manager.get_or_create(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception
        )
        return breaker(func)
    return decorator