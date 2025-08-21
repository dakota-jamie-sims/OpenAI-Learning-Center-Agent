"""
Knowledge Base Search Service
Provides search functionality for the Dakota knowledge base using vector store
"""
import os
from typing import List, Dict, Any, Optional, Tuple
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
import json
import time
import logging

logger = logging.getLogger(__name__)

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

class KnowledgeBaseSearcher:
    """Handles knowledge base searches using OpenAI's vector store"""
    
    def __init__(self, client: Optional[OpenAI] = None, timeout: Optional[float] = None, max_retries: int = 3):
        self.client = client or OpenAI(timeout=timeout)
        self.vector_store_id = os.getenv("VECTOR_STORE_ID") or os.getenv("OPENAI_VECTOR_STORE_ID")
        self.timeout = timeout
        self.max_retries = max_retries
        self.assistant = None  # Will be created once and reused
        
        if not self.vector_store_id:
            raise ValueError("No vector store ID found in environment variables")
        
        # Create assistant once at initialization
        self._initialize_assistant()
    
    def _initialize_assistant(self):
        """Initialize the assistant with retry support"""
        def create_assistant():
            return self.client.beta.assistants.create(
                name="KB Search Assistant",
                model="gpt-4-turbo",
                instructions="You are a knowledge base search assistant. Search for relevant information and provide accurate results with proper citations.",
                tools=[{"type": "file_search"}],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [self.vector_store_id]
                    }
                }
            )
        
        assistant, _ = self._with_retry(create_assistant)
        self.assistant = assistant
    
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
            result = retryer.call(func, timeout=timeout or self.timeout, **kwargs)
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
    
    def search(self, query: str, max_results: int = 5, include_metadata: bool = True) -> Dict[str, Any]:
        """
        Search the knowledge base for relevant content
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            include_metadata: Whether to include metadata about the search
            
        Returns:
            Dictionary containing search results and metadata
        """
        try:
            # Create thread with retry
            thread, _ = self._with_retry(self.client.beta.threads.create)
            
            search_prompt = f"""Search the Dakota knowledge base for information about: {query}

Please provide:
1. Most relevant articles or sections
2. Key insights and data points
3. Proper citations with article titles
4. Brief summary of each result

Focus on the most recent and relevant information."""

            # Create message with retry
            message, _ = self._with_retry(
                self.client.beta.threads.messages.create,
                thread_id=thread.id,
                role="user",
                content=search_prompt
            )
            
            # Run the assistant with retry
            run, _ = self._with_retry(
                self.client.beta.threads.runs.create,
                thread_id=thread.id,
                assistant_id=self.assistant.id
            )
            
            # Wait for completion with retry-wrapped status checks
            while run.status in ['queued', 'in_progress']:
                time.sleep(0.5)
                run, _ = self._with_retry(
                    self.client.beta.threads.runs.retrieve,
                    thread_id=thread.id,
                    run_id=run.id
                )
            
            if run.status == 'completed':
                # Get the response with retry
                messages, _ = self._with_retry(
                    self.client.beta.threads.messages.list,
                    thread_id=thread.id
                )
                response = messages.data[0].content[0].text.value
                
                # Extract citations if available
                citations = []
                if hasattr(messages.data[0].content[0].text, 'annotations'):
                    for annotation in messages.data[0].content[0].text.annotations:
                        if hasattr(annotation, 'file_citation'):
                            citations.append({
                                "file_id": annotation.file_citation.file_id,
                                "quote": annotation.text
                            })
                
                result = {
                    "success": True,
                    "query": query,
                    "results": response,
                    "citations_count": len(citations),
                    "status": "completed"
                }
                
                if include_metadata:
                    result["metadata"] = {
                        "vector_store_id": self.vector_store_id,
                        "max_results": max_results,
                        "citations": citations[:max_results] if citations else []
                    }
                
            else:
                result = {
                    "success": False,
                    "query": query,
                    "error": f"Search failed with status: {run.status}",
                    "status": run.status
                }
            
            return result
            
        except TransientOpenAIError as e:
            logger.error(f"Transient error during search: {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "status": "error"
            }
        except PermanentOpenAIError as e:
            logger.error(f"Permanent error during search: {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "status": "error"
            }
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "status": "error"
            }
    
    def search_similar_articles(self, topic: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Find similar articles in the knowledge base"""
        search_result = self.search(
            f"Find articles similar to or about: {topic}",
            max_results=limit
        )
        
        if search_result["success"]:
            return self._parse_article_results(search_result["results"])
        return []
    
    def get_dakota_insights(self, topic: str) -> Dict[str, Any]:
        """Get Dakota-specific insights on a topic"""
        search_result = self.search(
            f"Dakota Way philosophy and insights about: {topic}",
            max_results=3
        )
        
        return {
            "success": search_result["success"],
            "insights": search_result.get("results", ""),
            "topic": topic
        }
    
    def verify_fact(self, claim: str) -> Dict[str, Any]:
        """Verify a claim against the knowledge base"""
        search_result = self.search(
            f"Verify this claim with evidence: {claim}",
            max_results=5
        )
        
        return {
            "claim": claim,
            "verification_status": "verified" if search_result["success"] else "unverified",
            "evidence": search_result.get("results", ""),
            "citations_count": search_result.get("citations_count", 0)
        }
    
    def _parse_article_results(self, results_text: str) -> List[Dict[str, Any]]:
        """Parse article results from search text"""
        # Simple parsing - in production, this would be more sophisticated
        articles = []
        lines = results_text.split('\n')
        
        current_article = {}
        for line in lines:
            if line.strip().startswith('Article:') or line.strip().startswith('Title:'):
                if current_article:
                    articles.append(current_article)
                current_article = {"title": line.replace('Article:', '').replace('Title:', '').strip()}
            elif line.strip() and current_article:
                if 'summary' not in current_article:
                    current_article['summary'] = line.strip()
                else:
                    current_article['summary'] += ' ' + line.strip()
        
        if current_article:
            articles.append(current_article)
        
        return articles[:3]  # Return top 3 articles
    
    def cleanup(self):
        """Cleanup the assistant when done"""
        if self.assistant:
            try:
                self.client.beta.assistants.delete(assistant_id=self.assistant.id)
                logger.info(f"Deleted assistant {self.assistant.id}")
            except Exception as e:
                logger.warning(f"Failed to delete assistant: {e}")
            self.assistant = None
    
    def __del__(self):
        """Ensure assistant is cleaned up on deletion"""
        self.cleanup()


# Convenience function for backward compatibility
def search_knowledge_base(query: str, max_results: int = 5) -> str:
    """Legacy function for knowledge base search"""
    searcher = KnowledgeBaseSearcher()
    try:
        result = searcher.search(query, max_results)
        
        if result["success"]:
            return result["results"]
        else:
            return f"Search failed: {result.get('error', 'Unknown error')}"
    finally:
        # Ensure cleanup for one-off searches
        searcher.cleanup()