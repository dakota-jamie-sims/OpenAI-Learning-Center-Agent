"""
Production Knowledge Base Search using OpenAI Responses API
Uses the correct API as documented in OpenAI docs
"""
import os
import time
from typing import Dict, Any, List, Optional
import logging

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config import VECTOR_STORE_ID
from src.utils.logging import get_logger

logger = get_logger(__name__)

MAX_RETRIES = 3
TIMEOUT_SECONDS = 10


class ResponsesKBSearcher:
    """Production KB search using Responses API with file_search tool"""
    
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
            self.vector_store = self.client.vector_stores.retrieve(self.vector_store_id)
            logger.info(f"Connected to vector store: {self.vector_store.name}")
            logger.info(f"Vector store contains {self.vector_store.file_counts.total} files")
        except Exception as e:
            logger.error(f"Failed to connect to vector store: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(min=1, max=5)
    )
    def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Search the knowledge base using Responses API
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary containing search results
        """
        start_time = time.time()
        
        try:
            # Use Responses API with file_search tool
            response = self.client.responses.create(
                model="gpt-4o",  # Fast model for search
                input=f"Search the knowledge base for: {query}",
                tools=[{
                    "type": "file_search",
                    "vector_store_ids": [self.vector_store_id],
                    "max_num_results": max_results
                }],
                include=["file_search_call.results"]  # Include search results
            )
            
            # Extract results
            results = self._extract_results(response)
            
            elapsed = time.time() - start_time
            logger.info(f"KB search completed in {elapsed:.2f}s for query: {query[:50]}...")
            
            return {
                "success": True,
                "query": query,
                "results": results["formatted"],
                "raw_results": results["raw"],
                "citations": results["citations"],
                "citations_count": len(results["citations"]),
                "search_time": elapsed
            }
            
        except Exception as e:
            logger.error(f"KB search error: {str(e)}")
            return {
                "success": False,
                "query": query,
                "results": f"Search error: {str(e)}",
                "citations_count": 0,
                "error": str(e)
            }
    
    def _extract_results(self, response) -> Dict[str, Any]:
        """Extract search results from Responses API output"""
        results = {
            "formatted": "",
            "raw": [],
            "citations": []
        }
        
        # Process output items
        for item in response.output:
            if item.type == "file_search_call":
                # Extract search results if included
                if hasattr(item, 'search_results') and item.search_results:
                    for result in item.search_results:
                        citation = {
                            "file_id": result.get("file_id", ""),
                            "filename": result.get("filename", "Unknown"),
                            "content": result.get("content", ""),
                            "score": result.get("score", 0)
                        }
                        results["raw"].append(citation)
                        results["citations"].append(citation)
            
            elif item.type == "message":
                # Extract the assistant's response
                for content in item.content:
                    if content.type == "output_text":
                        results["formatted"] = content.text
                        
                        # Extract file citations from annotations
                        if hasattr(content, 'annotations'):
                            for ann in content.annotations:
                                if ann.type == "file_citation":
                                    # Update citation info if we have it
                                    for cit in results["citations"]:
                                        if cit["file_id"] == ann.file_id:
                                            cit["text"] = ann.text if hasattr(ann, 'text') else ""
                                            cit["filename"] = ann.filename if hasattr(ann, 'filename') else cit["filename"]
        
        # If no formatted result, create one from raw results
        if not results["formatted"] and results["raw"]:
            formatted_parts = []
            for i, result in enumerate(results["raw"][:5], 1):
                formatted_parts.append(f"{i}. From {result['filename']}:")
                formatted_parts.append(f"   {result['content'][:200]}...")
                formatted_parts.append("")
            results["formatted"] = "\n".join(formatted_parts)
        
        return results
    
    def search_batch(self, queries: List[str], max_results_per_query: int = 3) -> List[Dict[str, Any]]:
        """Search multiple queries"""
        results = []
        for query in queries:
            result = self.search(query, max_results_per_query)
            results.append(result)
            time.sleep(0.1)  # Rate limiting
        return results


# Global instance
_searcher = None


def get_responses_kb_searcher() -> ResponsesKBSearcher:
    """Get or create searcher instance"""
    global _searcher
    if _searcher is None:
        _searcher = ResponsesKBSearcher()
    return _searcher


def search_kb_responses(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Convenience function for KB search using Responses API"""
    searcher = get_responses_kb_searcher()
    return searcher.search(query, max_results)