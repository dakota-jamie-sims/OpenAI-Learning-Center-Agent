"""Base agent class for Dakota agents using GPT-5 models"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from src.services.openai_responses_client import ResponsesClient
from src.config import DEFAULT_MODELS
from src.utils.logging import get_logger

logger = get_logger(__name__)


class DakotaBaseAgent:
    """Base class for all Dakota agents with GPT-5 support"""
    
    def __init__(self, agent_name: str, model_override: Optional[str] = None):
        self.agent_name = agent_name
        self.logger = get_logger(f"dakota.{agent_name}")
        
        # Determine model based on agent type
        if model_override:
            self.model = model_override
        elif agent_name in ["fact_checker", "metrics_analyzer"]:
            self.model = DEFAULT_MODELS.get("analyzer", "gpt-5-mini")
        elif agent_name in ["kb_researcher", "web_researcher"]:
            self.model = DEFAULT_MODELS.get("researcher", "gpt-5-mini")
        else:
            self.model = DEFAULT_MODELS.get("default", "gpt-5")
        
        # Initialize ResponsesClient
        self.client = ResponsesClient(timeout=30)
        
        # Agent state
        self.status = "ready"
        self.current_task = None
        self.history = []
        
    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement execute()")
        
    async def query_llm(self, prompt: str, max_tokens: int = 1000, 
                       reasoning_effort: str = "low") -> str:
        """Query LLM with proper GPT-5 parameters"""
        try:
            # Prepare parameters for GPT-5
            create_params = {
                "model": self.model,
                "input_text": prompt,
                "reasoning_effort": reasoning_effort,
                "verbosity": "low",
                "max_tokens": max_tokens
            }
            
            # Don't add temperature for GPT-5 models
            if not self.model.startswith("gpt-5"):
                create_params["temperature"] = 0.3
            
            # Make the call
            response = await asyncio.to_thread(
                self.client.create_response,
                **create_params
            )
            
            # Extract text from response based on Responses API structure
            # response.output is a list where:
            # - output[0] is reasoning/meta (type: ResponseOutputReasoning) 
            # - output[1] is the message (type: ResponseOutputMessage) with content (if present)
            if hasattr(response, 'output') and response.output:
                # Look for ResponseOutputMessage items
                for item in response.output:
                    # Check if this is a message item
                    if hasattr(item, 'type') and item.type == 'message':
                        if hasattr(item, 'content') and item.content:
                            # content is a list of ResponseOutputText items
                            if isinstance(item.content, list) and len(item.content) > 0:
                                for content_item in item.content:
                                    if hasattr(content_item, 'text'):
                                        # text is already a string
                                        return content_item.text
                    # Also check items without explicit type
                    elif hasattr(item, 'content') and item.content:
                        if isinstance(item.content, list):
                            for content_item in item.content:
                                if hasattr(content_item, 'text') and isinstance(content_item.text, str):
                                    return content_item.text
                        elif hasattr(item.content, 'text'):
                            return str(item.content.text)
            
            # If we only got reasoning and no message, log and retry with different params
            self.logger.warning(f"No message in response. Output types: {[type(item).__name__ for item in response.output] if hasattr(response, 'output') else 'No output'}")
            
            # Try a simpler request without reasoning
            if reasoning_effort != "minimal":
                self.logger.info("Retrying with minimal reasoning effort...")
                try:
                    retry_params = {
                        "model": self.model,
                        "input_text": prompt,
                        "reasoning_effort": "minimal",
                        "verbosity": "medium",  # Increase verbosity
                        "max_tokens": max_tokens
                    }
                    
                    retry_response = await asyncio.to_thread(
                        self.client.create_response,
                        **retry_params
                    )
                    
                    # Try to extract from retry
                    if hasattr(retry_response, 'output') and retry_response.output:
                        for item in retry_response.output:
                            if hasattr(item, 'content') and item.content:
                                if isinstance(item.content, list) and len(item.content) > 0:
                                    for content_item in item.content:
                                        if hasattr(content_item, 'text'):
                                            return content_item.text
                except Exception as retry_error:
                    self.logger.error(f"Retry failed: {retry_error}")
            
            return "Content generation in progress..."
            
        except Exception as e:
            self.logger.error(f"LLM query error in {self.agent_name}: {e}")
            raise
            
    def update_status(self, status: str, message: str = ""):
        """Update agent status"""
        self.status = status
        self.logger.info(f"Status: {status} - {message}")
        
    def log_task_completion(self, task: Dict[str, Any], result: Dict[str, Any]):
        """Log completed task to history"""
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "task": task,
            "result": result,
            "duration": result.get("duration", 0)
        })
        
    async def validate_input(self, task: Dict[str, Any]) -> bool:
        """Validate task input - can be overridden by subclasses"""
        required_fields = self.get_required_fields()
        for field in required_fields:
            if field not in task:
                self.logger.error(f"Missing required field: {field}")
                return False
        return True
        
    def get_required_fields(self) -> List[str]:
        """Get required fields for this agent - override in subclasses"""
        return ["topic"]
        
    def format_response(self, success: bool, data: Any = None, 
                       error: str = None) -> Dict[str, Any]:
        """Standard response format"""
        response = {
            "agent": self.agent_name,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        
        if success and data is not None:
            response["data"] = data
        elif not success and error:
            response["error"] = error
            
        return response