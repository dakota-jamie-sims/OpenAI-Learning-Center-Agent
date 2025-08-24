"""
Optimized KB Search V2 - Production ready with caching and timeouts
Works with existing ResponsesClient and vector store
"""
import os
import time
import asyncio
import hashlib
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import VECTOR_STORE_ID
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Configuration
MAX_RETRIES = 2  # Reduced from 3
TIMEOUT_SECONDS = 5  # Reduced from 10
CACHE_TTL = 3600  # 1 hour


class OptimizedKBSearcherV2:
    """Optimized KB search with caching and reduced timeouts"""
    
    def __init__(self):
        self.client = OpenAI()
        self.vector_store_id = VECTOR_STORE_ID or os.getenv("OPENAI_VECTOR_STORE_ID")
        
        if not self.vector_store_id:
            raise ValueError("VECTOR_STORE_ID not configured!")
        
        # In-memory cache
        self.cache = {}
        self.cache_timestamps = {}
        
        # Verify vector store exists
        try:
            self.vector_store = self.client.vector_stores.retrieve(self.vector_store_id)
            logger.info(f"Connected to vector store: {self.vector_store.name}")
        except Exception as e:
            logger.error(f"Failed to connect to vector store: {e}")
            raise
    
    def _cache_key(self, query: str) -> str:
        """Generate cache key for a query"""
        return hashlib.md5(query.encode()).hexdigest()
    
    def _get_from_cache(self, query: str) -> Optional[Dict[str, Any]]:
        """Get result from cache if valid"""
        cache_key = self._cache_key(query)
        
        if cache_key in self.cache:
            timestamp = self.cache_timestamps.get(cache_key, 0)
            if time.time() - timestamp < CACHE_TTL:
                logger.debug(f"Cache hit for: {query[:50]}...")
                return self.cache[cache_key]
        
        return None
    
    def _set_cache(self, query: str, result: Dict[str, Any]):
        """Set result in cache"""
        cache_key = self._cache_key(query)
        self.cache[cache_key] = result
        self.cache_timestamps[cache_key] = time.time()
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(min=0.5, max=2)
    )
    def _search_with_timeout(self, query: str, max_results: int) -> Dict[str, Any]:
        """Execute search with strict timeout"""
        # Use gpt-4o-mini for fast search
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": f"Search the knowledge base for: {query}"
            }],
            tools=[{
                "type": "file_search",
                "file_search": {
                    "vector_store_ids": [self.vector_store_id],
                    "max_num_results": max_results
                }
            }],
            timeout=TIMEOUT_SECONDS
        )
        
        return self._extract_results(response, query)
    
    def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Search with caching and timeout protection"""
        start_time = time.time()
        
        # Check cache first
        cached = self._get_from_cache(query)
        if cached:
            return cached
        
        try:
            # Execute search with timeout
            result = self._search_with_timeout(query, max_results)
            
            # Cache successful result
            self._set_cache(query, result)
            
            elapsed = time.time() - start_time
            logger.info(f"KB search completed in {elapsed:.2f}s for: {query[:50]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"KB search error: {str(e)}")
            
            # Return degraded response
            return {
                "success": False,
                "query": query,
                "results": self._get_fallback_results(query),
                "citations": [],
                "citations_count": 0,
                "error": str(e)
            }
    
    def _extract_results(self, response, query: str) -> Dict[str, Any]:
        """Extract search results from response"""
        citations = []
        formatted_results = []
        
        # Extract from tool calls
        if hasattr(response, 'choices') and response.choices:
            choice = response.choices[0]
            
            # Get message content
            if hasattr(choice, 'message') and choice.message.content:
                formatted_results.append(choice.message.content)
            
            # Get tool call results
            if hasattr(choice, 'message') and hasattr(choice.message, 'tool_calls'):
                for tool_call in choice.message.tool_calls:
                    if hasattr(tool_call, 'function') and hasattr(tool_call.function, 'arguments'):
                        try:
                            args = json.loads(tool_call.function.arguments)
                            if 'results' in args:
                                for result in args['results']:
                                    citations.append({
                                        'file_id': result.get('file_id', ''),
                                        'filename': result.get('filename', 'Unknown'),
                                        'content': result.get('content', ''),
                                        'score': result.get('score', 0.0)
                                    })
                        except:
                            pass
        
        # Format results
        formatted_text = "\n".join(formatted_results) if formatted_results else "No specific results found."
        
        return {
            "success": True,
            "query": query,
            "results": formatted_text,
            "citations": citations,
            "citations_count": len(citations),
            "raw_results": citations
        }
    
    def _get_fallback_results(self, query: str) -> str:
        """Quick fallback results"""
        fallbacks = {
            "private equity": "See Dakota's PE fund databases and regional firm rankings.",
            "family office": "Dakota has extensive family office resources by geography.",
            "alternative": "Explore Dakota's alternative investment insights and trends.",
            "ria": "Check Dakota's RIA databases and top firm rankings."
        }
        
        query_lower = query.lower()
        for key, response in fallbacks.items():
            if key in query_lower:
                return response
        
        return "Please check Dakota's Learning Center for relevant articles."
    
    async def search_async(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Async version of search"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.search, query, max_results)
    
    def clear_cache(self):
        """Clear the cache"""
        self.cache.clear()
        self.cache_timestamps.clear()
        logger.info("KB search cache cleared")


# Global instance
_searcher = None


def get_optimized_kb_searcher() -> OptimizedKBSearcherV2:
    """Get or create searcher instance"""
    global _searcher
    if _searcher is None:
        _searcher = OptimizedKBSearcherV2()
    return _searcher


def search_kb_optimized(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Convenience function for optimized KB search"""
    searcher = get_optimized_kb_searcher()
    return searcher.search(query, max_results)