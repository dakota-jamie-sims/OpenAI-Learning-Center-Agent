"""
OpenAI Responses API Client for GPT-5
Uses the new responses API which supports reasoning chains and better tool handling
"""
import os
from typing import Dict, Any, Optional, List
from openai import OpenAI
from dotenv import load_dotenv
from src.utils.logging import get_logger

load_dotenv()

logger = get_logger(__name__)


class ResponsesClient:
    """Wrapper for OpenAI Responses API with GPT-5 support"""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.previous_response_id = None
        logger.debug("ResponsesClient initialized")
    
    def create_response(
        self,
        model: str,
        input_text: str,
        reasoning_effort: str = "medium",
        verbosity: str = "medium",
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[Dict] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
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
        logger.debug("Creating response with model %s", model)
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
        if temperature is not None:
            request_data["temperature"] = temperature
            
        if max_tokens:
            request_data["max_tokens"] = max_tokens
            
        if tools:
            request_data["tools"] = tools
            
        if tool_choice:
            request_data["tool_choice"] = tool_choice
        
        # Add any additional kwargs
        request_data.update(kwargs)
        
        # Make the API call
        response = self.client.responses.create(**request_data)
        logger.debug("Response received")
        
        # Store response ID for next turn
        if hasattr(response, 'id'):
            self.previous_response_id = response.id
            
        return response
    
    def create_simple_response(
        self,
        model: str,
        prompt: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Simple helper for basic text generation
        
        Returns just the text content
        """
        logger.debug("Creating simple response with model %s", model)
        response = self.create_response(
            model=model,
            input_text=prompt,
            reasoning_effort="minimal",
            verbosity="medium",
            temperature=temperature,
            max_tokens=max_tokens
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
        logger.debug("Conversation reset")
