"""OpenAI Responses API Client for GPT-5.

This module now wraps all API calls with a retry mechanism and exposes
retry information to callers. A ``timeout`` can also be specified and is
propagated to the underlying :class:`openai.OpenAI` client.
"""
import os
import logging
from typing import Dict, Any, Optional, List, Tuple

from dotenv import load_dotenv
from openai import (
    OpenAI,
    APIError,
    APIConnectionError,
    RateLimitError,
    APITimeoutError,
)
from tenacity import (
    Retrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

load_dotenv()


logger = logging.getLogger(__name__)


def supports_temperature(model: str) -> bool:
    """Return ``True`` if the given model supports the ``temperature`` parameter."""
    # Reasoning models (prefixed with o1, o3, o4, etc.) currently do not support
    # temperature adjustments.
    reasoning_prefixes = ("o1", "o3", "o4")
    return not model.lower().startswith(reasoning_prefixes)


# Exceptions that should trigger a retry
RETRY_EXCEPTIONS = (
    APIError,
    APIConnectionError,
    RateLimitError,
    APITimeoutError,
)


class TransientOpenAIError(RuntimeError):
    """Error raised when transient failures persist after retries."""


class PermanentOpenAIError(RuntimeError):
    """Error raised for non-retryable OpenAI failures."""


class ResponsesClient:
    """Wrapper for OpenAI Responses API with GPT-5 support"""

    def __init__(self, timeout: Optional[float] = None, max_retries: int = 3):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=timeout)
        self.previous_response_id = None
        self.timeout = timeout
        self.max_retries = max_retries

    def _with_retry(
        self, func, timeout: Optional[float] = None, **kwargs
    ) -> Tuple[Any, int]:
        """Execute an API call with retries.

        Returns the result and the number of retry attempts performed.
        Raises :class:`TransientOpenAIError` for retryable failures and
        :class:`PermanentOpenAIError` for non-retryable ones.
        """
        retryer = Retrying(
            reraise=True,
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(min=1, max=10, multiplier=1),
            retry=retry_if_exception_type(RETRY_EXCEPTIONS),
            before_sleep=lambda rs: logger.warning(
                "Retrying OpenAI API call (%s/%s) after error: %s",
                rs.attempt_number,
                self.max_retries,
                rs.outcome.exception(),
            ),
        )

        try:
            result = retryer(func, timeout=timeout, **kwargs)
            attempts = retryer.statistics.get("attempt_number", 1) - 1
            return result, attempts
        except RETRY_EXCEPTIONS as e:
            attempts = retryer.statistics.get("attempt_number", 1)
            logger.error(
                "OpenAI transient error after %d attempts: %s", attempts, e
            )
            raise TransientOpenAIError(
                f"Transient OpenAI error after {attempts} attempts: {e}"
            ) from e
        except Exception as e:  # Non-retryable
            logger.error("OpenAI permanent error: %s", e)
            raise PermanentOpenAIError(str(e)) from e
    
    def create_response(
        self,
        model: str,
        input_text: str,
        reasoning_effort: str = "medium",
        verbosity: str = "medium",
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Dict] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a response using the Responses API
        
        Args:
            model: Model to use (gpt-5, gpt-5-mini, gpt-5-nano)
            input_text: The input prompt
            reasoning_effort: minimal, low, medium, high
            verbosity: low, medium, high
            tools: Optional list of tools
            tool_choice: Optional tool choice configuration
            temperature: Temperature for sampling
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Response dictionary
        """
        request_data = {
            "model": model,
            "input": input_text,
            "reasoning": {
                "effort": reasoning_effort
            },
            "text": {
                "verbosity": verbosity
            }
        }
        
        # Add previous response ID for conversation continuity
        if self.previous_response_id:
            request_data["previous_response_id"] = self.previous_response_id
        
        # Add optional parameters
        if temperature is not None and supports_temperature(model):
            request_data["temperature"] = temperature
            
        if max_tokens:
            request_data["max_tokens"] = max_tokens
            
        if tools:
            request_data["tools"] = tools
            
        if tool_choice:
            request_data["tool_choice"] = tool_choice
        
        # Add any additional kwargs (excluding timeout)
        request_data.update(kwargs)

        timeout = timeout or self.timeout

        # Make the API call with retries
        response, attempts = self._with_retry(
            self.client.responses.create, timeout=timeout, **request_data
        )

        # Surface retry attempts to caller
        setattr(response, "retry_attempts", attempts)

        # Store response ID for next turn
        if hasattr(response, 'id'):
            self.previous_response_id = response.id
            
        return response
    
    def create_simple_response(
        self,
        model: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        timeout: Optional[float] = None,
    ) -> str:
        """
        Simple helper for basic text generation
        
        Returns just the text content
        """
        response = self.create_response(
            model=model,
            input_text=prompt,
            reasoning_effort="minimal",
            verbosity="medium",
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        
        # Extract text from response
        if hasattr(response, 'content') and response.content:
            if isinstance(response.content, list) and len(response.content) > 0:
                return response.content[0].text
            elif hasattr(response.content, 'text'):
                return response.content.text
        
        return str(response)
    
    def reset_conversation(self):
        """Reset the conversation by clearing previous response ID"""
        self.previous_response_id = None