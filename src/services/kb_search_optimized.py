"""
Optimized Knowledge Base Search Service using direct file search
Much faster than assistant-based search
"""
import os
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.config import VECTOR_STORE_ID
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Retry configuration
RETRY_EXCEPTIONS = (Exception,)  # Retry on all exceptions
MAX_RETRIES = 3
TIMEOUT_SECONDS = 10  # Much shorter timeout


class OptimizedKBSearcher:
    """Optimized knowledge base searcher using direct file search"""
    
    def __init__(self):
        self.client = OpenAI()
        self.vector_store_id = VECTOR_STORE_ID or os.getenv("OPENAI_VECTOR_STORE_ID")
        
        if not self.vector_store_id:
            logger.warning("No vector store ID configured - KB search will return empty results")
    
    def search(self, query: str, max_results: int = 5, timeout: float = TIMEOUT_SECONDS) -> Dict[str, Any]:
        """
        Search the knowledge base using direct file search API
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            timeout: Timeout in seconds
            
        Returns:
            Dictionary containing search results
        """
        if not self.vector_store_id:
            return {
                "success": False,
                "query": query,
                "results": "No vector store configured",
                "citations_count": 0,
                "status": "no_vector_store"
            }
        
        start_time = time.time()
        
        try:
            # Use file search directly - much faster than assistant
            response = self._search_with_timeout(query, max_results, timeout)
            
            elapsed = time.time() - start_time
            logger.info(f"KB search completed in {elapsed:.2f}s for query: {query[:50]}...")
            
            return {
                "success": True,
                "query": query,
                "results": self._format_results(response),
                "citations_count": len(response) if response else 0,
                "status": "completed",
                "search_time": elapsed
            }
            
        except TimeoutError:
            logger.warning(f"KB search timed out after {timeout}s for query: {query[:50]}...")
            return {
                "success": False,
                "query": query,
                "results": [],  # Return empty list instead of string
                "citations_count": 0,
                "status": "timeout",
                "error": f"Search timed out after {timeout} seconds"
            }
            
        except Exception as e:
            logger.error(f"KB search error: {str(e)}")
            return {
                "success": False,
                "query": query,
                "results": [],  # Return empty list instead of string
                "citations_count": 0,
                "status": "error"
            }
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(min=1, max=10),
        retry=retry_if_exception_type(RETRY_EXCEPTIONS)
    )
    def _search_with_timeout(self, query: str, max_results: int, timeout: float) -> List[Dict[str, Any]]:
        """Execute search with timeout and retry logic"""
        # Create a thread for the search
        import concurrent.futures
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(self._perform_search, query, max_results)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                raise TimeoutError(f"Search exceeded {timeout}s timeout")
    
    def _perform_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Perform the actual vector search"""
        try:
            # Use Responses API for KB search - the correct API for file search
            from src.services.kb_search_responses import search_kb_responses
            
            logger.info(f"Performing REAL KB search using Responses API for: {query[:50]}...")
            
            # Get real results from vector store
            result = search_kb_responses(query, max_results)
            
            if result["success"]:
                # Convert results to expected format
                search_results = []
                
                # Use citations if available
                if result.get("citations"):
                    for citation in result["citations"][:max_results]:
                        search_results.append({
                            "file_name": citation.get("filename", "Unknown file"),
                            "content": citation.get("content", ""),
                            "relevance_score": citation.get("score", 0.9),
                            "file_id": citation.get("file_id", "")
                        })
                
                # If no citations but have formatted results
                if not search_results and result.get("results"):
                    content = result["results"]
                    if content and "No results" not in content:
                        # Use the formatted content as a single result
                        search_results.append({
                            "file_name": "Dakota Knowledge Base",
                            "content": content[:500],
                            "relevance_score": 0.85
                        })
                
                return search_results[:max_results]
            else:
                logger.warning(f"KB search failed: {result.get('error', 'Unknown error')}")
                return []
                
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            # If search fails, return empty results
            return []
    
    def _format_results(self, raw_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format search results into structured data"""
        if not raw_results:
            return []
        
        formatted = []
        for i, result in enumerate(raw_results, 1):
            formatted.append({
                "title": result.get('file_name', f'Dakota Document {i}'),
                "content": result.get('content', 'No content available'),
                "file_name": result.get('file_name', 'Unknown'),
                "score": result.get('score', 0.8),  # Default relevance score
                "type": "knowledge_base"
            })
        
        return formatted
    
    def search_with_fallback(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Search with automatic fallback to web search if KB fails"""
        result = self.search(query, max_results, timeout=5)  # Shorter timeout for fallback
        
        if not result["success"]:
            logger.info("KB search failed, suggesting web search fallback")
            result["fallback_suggested"] = "web_search"
            result["results"] = []  # Keep results as empty list
        
        return result


# Global instance for reuse
_kb_searcher = None


def get_kb_searcher() -> OptimizedKBSearcher:
    """Get or create the global KB searcher instance"""
    global _kb_searcher
    if _kb_searcher is None:
        _kb_searcher = OptimizedKBSearcher()
    return _kb_searcher


def search_knowledge_base(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Convenience function to search knowledge base"""
    searcher = get_kb_searcher()
    return searcher.search_with_fallback(query, max_results)