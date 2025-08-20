"""
Base orchestrator class with responses API support
"""
import os
import json
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from src.services.openai_responses_client import ResponsesClient
from src.config import DEFAULT_MODELS, OUTPUT_BASE_DIR

load_dotenv()


class BaseOrchestrator:
    """Base class for all orchestrators using Responses API"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.responses_client = ResponsesClient()
        self.output_dir = Path(OUTPUT_BASE_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store_id = os.getenv("VECTOR_STORE_ID") or os.getenv("OPENAI_VECTOR_STORE_ID")
    
    def create_response(
        self,
        prompt: str,
        model: Optional[str] = None,
        reasoning_effort: str = "medium",
        verbosity: str = "medium",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Create a response using the Responses API"""
        if model is None:
            model = DEFAULT_MODELS["orchestrator"]
            
        response = self.responses_client.create_response(
            model=model,
            input_text=prompt,
            reasoning_effort=reasoning_effort,
            verbosity=verbosity,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return self._extract_text(response)
    
    def _extract_text(self, response) -> str:
        """Extract text from responses API response"""
        if hasattr(response, 'content') and response.content:
            if isinstance(response.content, list) and len(response.content) > 0:
                texts = []
                for item in response.content:
                    if hasattr(item, 'text'):
                        texts.append(item.text)
                return "\n\n".join(texts)
            elif hasattr(response.content, 'text'):
                return response.content.text
        return str(response)
    
    def parse_json_response(self, text: str) -> Dict[str, Any]:
        """Extract and parse JSON from response text"""
        import re
        
        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Fallback
        return {}
    
    def create_output_directory(self, topic: str) -> Path:
        """Create a timestamped output directory for the article"""
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        safe_topic = "".join(c for c in topic if c.isalnum() or c in " -_").strip()[:50]
        article_dir = self.output_dir / f"{timestamp}-{safe_topic}"
        article_dir.mkdir(parents=True, exist_ok=True)
        return article_dir