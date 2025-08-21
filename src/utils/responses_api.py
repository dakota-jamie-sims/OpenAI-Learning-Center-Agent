"""
Utility functions for OpenAI Responses API
Handles all GPT-5 model calls across the system
"""
import os
from typing import Dict, Any, Optional, List, Union
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Initialize client
client = OpenAI()

# Reasoning effort levels for different use cases
REASONING_EFFORTS = {
    "high": {"effort": "high"},  # For complex analysis, orchestration
    "medium": {"effort": "medium"},  # For standard generation tasks
    "low": {"effort": "low"},  # For simple tasks, quick responses
    "minimal": {"effort": "minimal"}  # For very fast, simple operations
}

# Text verbosity levels
TEXT_VERBOSITY = {
    "high": {"verbosity": "high"},    # Detailed explanations
    "medium": {"verbosity": "medium"},  # Standard responses
    "low": {"verbosity": "low"}     # Brief, to-the-point
}


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=10),
    reraise=True
)
def create_response(
    prompt: str,
    model: str = "gpt-5",
    reasoning_effort: str = "medium",
    text_verbosity: str = "medium",
    max_thinking_tokens: Optional[int] = None,
    tools: Optional[List[Dict[str, Any]]] = None,
    include: Optional[List[str]] = None,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Create a response using the Responses API
    
    Args:
        prompt: The input prompt
        model: The GPT-5 model variant (gpt-5, gpt-5-mini, gpt-5-nano)
        reasoning_effort: Level of reasoning (high, medium, low, minimal)
        text_verbosity: Output verbosity (high, medium, low)
        max_thinking_tokens: Optional limit on thinking tokens
        tools: Optional list of tools (e.g., file_search)
        include: Optional list of response fields to include
        temperature: Temperature for generation
        
    Returns:
        Dict containing the response and metadata
    """
    try:
        # Build the request
        request_params = {
            "model": model,
            "input": prompt,
            "reasoning": REASONING_EFFORTS.get(reasoning_effort, {"effort": reasoning_effort}),
            "text": TEXT_VERBOSITY.get(text_verbosity, {"verbosity": text_verbosity}),
            "temperature": temperature
        }
        
        # Add optional parameters
        if max_thinking_tokens:
            request_params["max_thinking_tokens"] = max_thinking_tokens
        
        if tools:
            request_params["tools"] = tools
            
        if include:
            request_params["include"] = include
        
        # Make the API call
        response = client.responses.create(**request_params)
        
        # Extract the text content
        text_content = ""
        citations = []
        metadata = {}
        
        # Process output items
        for item in response.output:
            if item.type == "message":
                for content in item.content:
                    if content.type == "output_text":
                        text_content = content.text
                        # Extract annotations if present
                        if hasattr(content, 'annotations'):
                            for ann in content.annotations:
                                if ann.type == "file_citation":
                                    citations.append({
                                        "file_id": ann.file_id,
                                        "filename": getattr(ann, 'filename', 'Unknown'),
                                        "text": getattr(ann, 'text', '')
                                    })
            elif item.type == "file_search_call":
                metadata["file_search"] = {
                    "id": item.id,
                    "status": item.status,
                    "queries": getattr(item, 'queries', [])
                }
        
        # Get usage information
        usage = getattr(response, 'usage', {})
        
        return {
            "success": True,
            "content": text_content,
            "citations": citations,
            "metadata": metadata,
            "usage": {
                "prompt_tokens": getattr(usage, 'prompt_tokens', 0),
                "completion_tokens": getattr(usage, 'completion_tokens', 0),
                "thinking_tokens": getattr(usage, 'thinking_tokens', 0),
                "total_tokens": getattr(usage, 'total_tokens', 0)
            },
            "model": model,
            "reasoning_effort": reasoning_effort
        }
        
    except Exception as e:
        logger.error(f"Responses API error: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "content": ""
        }


def create_response_with_kb_search(
    prompt: str,
    vector_store_id: str,
    model: str = "gpt-5",
    max_search_results: int = 5,
    reasoning_effort: str = "medium",
    text_verbosity: str = "medium",
    **kwargs
) -> Dict[str, Any]:
    """
    Create a response with knowledge base search
    
    Args:
        prompt: The input prompt
        vector_store_id: The vector store ID to search
        model: The GPT-5 model variant
        max_search_results: Maximum search results
        reasoning_effort: Level of reasoning
        text_verbosity: Output verbosity
        **kwargs: Additional arguments for create_response
        
    Returns:
        Dict containing the response with KB search results
    """
    tools = [{
        "type": "file_search",
        "vector_store_ids": [vector_store_id],
        "max_num_results": max_search_results
    }]
    
    include = ["file_search_call.results"]
    
    return create_response(
        prompt=prompt,
        model=model,
        reasoning_effort=reasoning_effort,
        text_verbosity=text_verbosity,
        tools=tools,
        include=include,
        **kwargs
    )


def select_model_for_task(task_type: str) -> tuple[str, str, str]:
    """
    Select appropriate GPT-5 model and settings for a task
    
    Args:
        task_type: Type of task (orchestrator, research, writing, etc.)
        
    Returns:
        Tuple of (model, reasoning_effort, text_verbosity)
    """
    task_configs = {
        # High-level coordination
        "orchestrator": ("gpt-5", "high", "medium"),
        "team_lead": ("gpt-5-mini", "medium", "medium"),
        
        # Research tasks
        "research_complex": ("gpt-5", "high", "high"),
        "research_simple": ("gpt-5-nano", "low", "low"),
        "kb_search": ("gpt-5-nano", "minimal", "low"),
        "web_search": ("gpt-5-nano", "low", "low"),

        # Writing tasks
        "writing_main": ("gpt-5", "medium", "high"),
        "writing_section": ("gpt-5-mini", "medium", "medium"),
        "editing": ("gpt-5-mini", "medium", "medium"),

        # Analysis tasks
        "quality_check": ("gpt-5-mini", "medium", "medium"),
        "fact_check": ("gpt-5-mini", "high", "low"),
        "metadata": ("gpt-5-nano", "low", "low"),
        
        # Default
        "default": ("gpt-5-mini", "medium", "medium")
    }
    
    return task_configs.get(task_type, task_configs["default"])


def migrate_chat_completion_call(
    messages: List[Dict[str, str]],
    model: str = "gpt-5",
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Helper to migrate from chat completions to responses API
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: The GPT-5 model to use
        temperature: Temperature setting
        max_tokens: Not used in Responses API, included for compatibility
        **kwargs: Additional arguments
        
    Returns:
        Dict containing the response
    """
    # Convert messages to a single prompt
    prompt_parts = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        
        if role == "system":
            prompt_parts.append(f"Instructions: {content}")
        elif role == "user":
            prompt_parts.append(f"User: {content}")
        elif role == "assistant":
            prompt_parts.append(f"Assistant: {content}")
    
    prompt = "\n\n".join(prompt_parts)
    
    # Determine task type from context
    task_type = kwargs.get("task_type", "default")
    model_name, reasoning, verbosity = select_model_for_task(task_type)
    
    # Use provided model if it's a GPT-5 variant
    if model.startswith("gpt-5"):
        model_name = model
    
    return create_response(
        prompt=prompt,
        model=model_name,
        reasoning_effort=reasoning,
        text_verbosity=verbosity,
        temperature=temperature,
        **kwargs
    )