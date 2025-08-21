"""
Direct Knowledge Base Search using Thread-based approach
Production-ready, fast implementation
"""
import os
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from src.config import VECTOR_STORE_ID
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Configuration
MAX_RETRIES = 3
TIMEOUT_SECONDS = 8
SEARCH_MODEL = "gpt-4o"  # Fast model for search


class DirectKBSearcher:
    """Direct KB search without creating persistent assistants"""
    
    def __init__(self):
        self.client = OpenAI()
        self.vector_store_id = VECTOR_STORE_ID or os.getenv("OPENAI_VECTOR_STORE_ID")
        
        if not self.vector_store_id:
            raise ValueError("VECTOR_STORE_ID not configured!")
        
        # Verify vector store
        try:
            self.vector_store = self.client.vector_stores.retrieve(self.vector_store_id)
            logger.info(f"Connected to vector store: {self.vector_store.name}")
            logger.info(f"Files in store: {self.vector_store.file_counts.total}")
        except Exception as e:
            logger.error(f"Failed to connect to vector store: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(min=1, max=5),
        retry=retry_if_exception_type(Exception)
    )
    def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Fast search using thread-based approach
        """
        start_time = time.time()
        
        try:
            # Create a temporary assistant for this search
            assistant = self.client.assistants.create(
                name="KB Search",
                instructions=f"""You are a search assistant. Search the knowledge base for: {query}
                
Return the {max_results} most relevant results with:
1. Source file name
2. Relevant quote or content
3. Brief summary of relevance

Format each result clearly.""",
                model=SEARCH_MODEL,
                tools=[{"type": "file_search"}],
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [self.vector_store_id]
                    }
                }
            )
            
            # Create thread
            thread = self.client.threads.create()
            
            # Add message
            self.client.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=query
            )
            
            # Run search
            run = self.client.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant.id,
                max_prompt_tokens=1000,
                max_completion_tokens=2000
            )
            
            # Wait for completion
            run = self._wait_for_completion(thread.id, run.id)
            
            # Get results
            if run.status == "completed":
                messages = self.client.threads.messages.list(thread_id=thread.id)
                
                # Extract results
                results = self._extract_results(messages)
                
                # Clean up - delete assistant
                self.client.assistants.delete(assistant.id)
                
                elapsed = time.time() - start_time
                logger.info(f"KB search completed in {elapsed:.2f}s")
                
                return {
                    "success": True,
                    "query": query,
                    "results": results["formatted"],
                    "citations": results["citations"],
                    "citations_count": len(results["citations"]),
                    "search_time": elapsed
                }
            else:
                # Clean up
                self.client.assistants.delete(assistant.id)
                
                return {
                    "success": False,
                    "query": query,
                    "results": f"Search failed: {run.status}",
                    "error": getattr(run, 'last_error', None)
                }
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            return {
                "success": False,
                "query": query,
                "results": f"Error: {str(e)}",
                "error": str(e)
            }
    
    def _wait_for_completion(self, thread_id: str, run_id: str) -> Any:
        """Wait for run completion with timeout"""
        start = time.time()
        
        while time.time() - start < TIMEOUT_SECONDS:
            run = self.client.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            
            if run.status in ["completed", "failed", "cancelled", "expired"]:
                return run
                
            time.sleep(0.3)
        
        # Timeout - cancel the run
        try:
            self.client.threads.runs.cancel(thread_id=thread_id, run_id=run_id)
        except:
            pass
            
        raise TimeoutError(f"Search exceeded {TIMEOUT_SECONDS}s timeout")
    
    def _extract_results(self, messages) -> Dict[str, Any]:
        """Extract search results from messages"""
        results = {
            "formatted": "",
            "citations": []
        }
        
        for message in messages.data:
            if message.role == "assistant":
                for content in message.content:
                    if content.type == "text":
                        results["formatted"] = content.text.value
                        
                        # Extract annotations
                        if hasattr(content.text, 'annotations'):
                            for ann in content.text.annotations:
                                if ann.type == "file_citation":
                                    citation = {
                                        "file_id": ann.file_citation.file_id,
                                        "text": ann.text,
                                        "start": ann.start_index,
                                        "end": ann.end_index
                                    }
                                    
                                    # Try to get filename
                                    try:
                                        file_info = self.client.files.retrieve(
                                            ann.file_citation.file_id
                                        )
                                        citation["filename"] = file_info.filename
                                    except:
                                        citation["filename"] = "Unknown"
                                    
                                    results["citations"].append(citation)
                        break
        
        return results
    
    def search_batch(self, queries: List[str], max_results_per_query: int = 3) -> List[Dict[str, Any]]:
        """Search multiple queries efficiently"""
        results = []
        for query in queries:
            result = self.search(query, max_results_per_query)
            results.append(result)
            # Small delay to avoid rate limits
            time.sleep(0.1)
        return results


# Global instance
_searcher = None


def get_direct_kb_searcher() -> DirectKBSearcher:
    """Get or create searcher instance"""
    global _searcher
    if _searcher is None:
        _searcher = DirectKBSearcher()
    return _searcher


def search_kb_direct(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Convenience function for direct KB search"""
    searcher = get_direct_kb_searcher()
    return searcher.search(query, max_results)