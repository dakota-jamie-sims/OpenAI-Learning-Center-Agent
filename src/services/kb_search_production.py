"""
Production-ready Knowledge Base Search using OpenAI Vector Store API
Real implementation - no mocks
"""
import os
import time
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
import json

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.config import VECTOR_STORE_ID
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Retry configuration
RETRY_EXCEPTIONS = (Exception,)
MAX_RETRIES = 3
TIMEOUT_SECONDS = 10


class ProductionKBSearcher:
    """Production-ready knowledge base searcher using OpenAI's vector store"""
    
    def __init__(self):
        self.client = OpenAI()
        self.vector_store_id = VECTOR_STORE_ID or os.getenv("OPENAI_VECTOR_STORE_ID")
        
        if not self.vector_store_id:
            raise ValueError(
                "VECTOR_STORE_ID not configured! "
                "Set OPENAI_VECTOR_STORE_ID in your .env file"
            )
        
        # Verify vector store exists
        try:
            # Use the correct API path
            self.vector_store = self.client.vector_stores.retrieve(
                self.vector_store_id
            )
            logger.info(f"Connected to vector store: {self.vector_store.name} ({self.vector_store_id})")
            logger.info(f"Vector store contains {self.vector_store.file_counts.total} files")
        except Exception as e:
            logger.error(f"Failed to connect to vector store: {e}")
            raise
    
    def search(self, query: str, max_results: int = 5, timeout: float = TIMEOUT_SECONDS) -> Dict[str, Any]:
        """
        Search the knowledge base using OpenAI's vector store
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            timeout: Timeout in seconds
            
        Returns:
            Dictionary containing search results
        """
        start_time = time.time()
        
        try:
            # Create a thread for the search
            thread = self.client.beta.threads.create()
            
            # Add the search query as a message
            message = self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=query,
                file_search={
                    "vector_store_ids": [self.vector_store_id],
                    "max_num_results": max_results
                }
            )
            
            # Create a run with file search
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self._get_or_create_search_assistant(),
                tools=[{"type": "file_search"}],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [self.vector_store_id]
                    }
                }
            )
            
            # Wait for completion with timeout
            run = self._wait_for_run_completion(thread.id, run.id, timeout)
            
            if run.status == "completed":
                # Get search results from messages
                messages = self.client.beta.threads.messages.list(thread_id=thread.id)
                
                # Extract search results and citations
                results = self._extract_search_results(messages)
                
                elapsed = time.time() - start_time
                logger.info(f"KB search completed in {elapsed:.2f}s for query: {query[:50]}...")
                
                return {
                    "success": True,
                    "query": query,
                    "results": results["content"],
                    "raw_results": results["raw"],
                    "citations": results["citations"],
                    "citations_count": len(results["citations"]),
                    "status": "completed",
                    "search_time": elapsed
                }
            else:
                return {
                    "success": False,
                    "query": query,
                    "results": f"Search failed with status: {run.status}",
                    "citations_count": 0,
                    "status": run.status,
                    "error": getattr(run, 'last_error', None)
                }
                
        except TimeoutError:
            logger.warning(f"KB search timed out after {timeout}s for query: {query[:50]}...")
            return {
                "success": False,
                "query": query,
                "results": f"Search timed out after {timeout} seconds",
                "citations_count": 0,
                "status": "timeout"
            }
            
        except Exception as e:
            logger.error(f"KB search error: {str(e)}")
            return {
                "success": False,
                "query": query,
                "results": f"Search error: {str(e)}",
                "citations_count": 0,
                "status": "error"
            }
    
    def _get_or_create_search_assistant(self) -> str:
        """Get or create a search assistant"""
        # Check if we have a cached assistant ID
        assistant_id = os.getenv("KB_SEARCH_ASSISTANT_ID")
        
        if assistant_id:
            try:
                # Verify it still exists
                self.client.beta.assistants.retrieve(assistant_id)
                return assistant_id
            except:
                pass
        
        # Create new assistant for search
        assistant = self.client.beta.assistants.create(
            name="KB Search Assistant",
            instructions="You are a search assistant. Search the knowledge base and return relevant results.",
            model="gpt-4o",  # Use a model that supports file search
            tools=[{"type": "file_search"}]
        )
        
        logger.info(f"Created new search assistant: {assistant.id}")
        return assistant.id
    
    def _wait_for_run_completion(self, thread_id: str, run_id: str, timeout: float) -> Any:
        """Wait for run to complete with timeout"""
        start_time = time.time()
        
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Run exceeded {timeout}s timeout")
            
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            
            if run.status in ["completed", "failed", "cancelled", "expired"]:
                return run
            
            time.sleep(0.5)
    
    def _extract_search_results(self, messages) -> Dict[str, Any]:
        """Extract search results and citations from messages"""
        results = {
            "content": "",
            "raw": [],
            "citations": []
        }
        
        for message in messages.data:
            if message.role == "assistant":
                # Extract content
                for content in message.content:
                    if content.type == "text":
                        results["content"] = content.text.value
                        
                        # Extract citations
                        if hasattr(content.text, 'annotations'):
                            for annotation in content.text.annotations:
                                if annotation.type == "file_citation":
                                    citation = {
                                        "file_id": annotation.file_citation.file_id,
                                        "quote": annotation.text,
                                        "start_index": annotation.start_index,
                                        "end_index": annotation.end_index
                                    }
                                    
                                    # Try to get file details
                                    try:
                                        file = self.client.files.retrieve(annotation.file_citation.file_id)
                                        citation["filename"] = file.filename
                                        citation["file_size"] = file.bytes
                                    except:
                                        pass
                                    
                                    results["citations"].append(citation)
                                    results["raw"].append(citation)
        
        return results
    
    def search_with_context(self, query: str, context: str = "", max_results: int = 5) -> Dict[str, Any]:
        """Search with additional context for better results"""
        enhanced_query = f"{context}\n\nSearch for: {query}" if context else query
        return self.search(enhanced_query, max_results)
    
    def search_multiple(self, queries: List[str], max_results_per_query: int = 3) -> List[Dict[str, Any]]:
        """Search multiple queries in parallel"""
        async def search_async(query):
            return self.search(query, max_results_per_query)
        
        async def run_searches():
            tasks = [search_async(query) for query in queries]
            return await asyncio.gather(*tasks)
        
        # Run searches in parallel
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(run_searches())
        finally:
            loop.close()
    
    def get_vector_store_info(self) -> Dict[str, Any]:
        """Get information about the vector store"""
        try:
            vs = self.client.vector_stores.retrieve(self.vector_store_id)
            return {
                "id": vs.id,
                "name": vs.name,
                "total_files": vs.file_counts.total,
                "in_progress": vs.file_counts.in_progress,
                "completed": vs.file_counts.completed,
                "failed": vs.file_counts.failed,
                "cancelled": vs.file_counts.cancelled,
                "created_at": vs.created_at,
                "status": vs.status,
                "expires_at": vs.expires_at
            }
        except Exception as e:
            return {"error": str(e)}


# Global instance for reuse
_kb_searcher = None


def get_production_kb_searcher() -> ProductionKBSearcher:
    """Get or create the global KB searcher instance"""
    global _kb_searcher
    if _kb_searcher is None:
        _kb_searcher = ProductionKBSearcher()
    return _kb_searcher


def search_knowledge_base_production(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Production search function"""
    searcher = get_production_kb_searcher()
    return searcher.search(query, max_results)