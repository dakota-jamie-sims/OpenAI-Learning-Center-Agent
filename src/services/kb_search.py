"""Knowledge Base Search Service.

Adds retry support and optional timeouts to all OpenAI API calls so that
transient failures are retried and logged. Retry counts are surfaced to
callers in the returned metadata.
"""
import os
import json
import time
import logging
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

logger = logging.getLogger(__name__)

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

    def __init__(
        self,
        client: Optional[OpenAI] = None,
        timeout: Optional[float] = None,
        max_retries: int = 3,
    ):
        self.client = client or OpenAI(timeout=timeout)
        self.timeout = timeout
        self.max_retries = max_retries
        self.vector_store_id = os.getenv("VECTOR_STORE_ID") or os.getenv("OPENAI_VECTOR_STORE_ID")

        if not self.vector_store_id:
            raise ValueError("No vector store ID found in environment variables")

    def _with_retry(self, func, timeout: Optional[float] = None, **kwargs) -> Tuple[Any, int]:
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
            result = retryer.call(func, timeout=timeout, **kwargs)
            attempts = retryer.statistics.get("attempt_number", 1) - 1
            return result, attempts
        except RETRY_EXCEPTIONS as e:
            attempts = retryer.statistics.get("attempt_number", 1)
            logger.error("OpenAI transient error after %d attempts: %s", attempts, e)
            raise TransientOpenAIError(
                f"Transient OpenAI error after {attempts} attempts: {e}"
            ) from e
        except Exception as e:
            logger.error("OpenAI permanent error: %s", e)
            raise PermanentOpenAIError(str(e)) from e

    def search(
        self,
        query: str,
        max_results: int = 5,
        include_metadata: bool = True,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Search the knowledge base for relevant content"""

        timeout = timeout or self.timeout
        total_retries = 0

        try:
            assistant, attempts = self._with_retry(
                self.client.beta.assistants.create,
                timeout=timeout,
                name="KB Search Assistant",
                model="gpt-4-turbo",
                instructions="You are a knowledge base search assistant. Search for relevant information and provide accurate results with proper citations.",
                tools=[{"type": "file_search"}],
                tool_resources={"file_search": {"vector_store_ids": [self.vector_store_id]}},
            )
            total_retries += attempts

            thread, attempts = self._with_retry(
                self.client.beta.threads.create, timeout=timeout
            )
            total_retries += attempts

            search_prompt = f"""Search the Dakota knowledge base for information about: {query}

Please provide:
1. Most relevant articles or sections
2. Key insights and data points
3. Proper citations with article titles
4. Brief summary of each result

Focus on the most recent and relevant information."""
            _, attempts = self._with_retry(
                self.client.beta.threads.messages.create,
                timeout=timeout,
                thread_id=thread.id,
                role="user",
                content=search_prompt,
            )
            total_retries += attempts

            run, attempts = self._with_retry(
                self.client.beta.threads.runs.create,
                timeout=timeout,
                thread_id=thread.id,
                assistant_id=assistant.id,
            )
            total_retries += attempts

            while run.status in ["queued", "in_progress"]:
                time.sleep(0.5)
                run, attempts = self._with_retry(
                    self.client.beta.threads.runs.retrieve,
                    timeout=timeout,
                    thread_id=thread.id,
                    run_id=run.id,
                )
                total_retries += attempts

            if run.status == "completed":
                messages, attempts = self._with_retry(
                    self.client.beta.threads.messages.list,
                    timeout=timeout,
                    thread_id=thread.id,
                )
                total_retries += attempts
                response = messages.data[0].content[0].text.value

                citations = []
                if hasattr(messages.data[0].content[0].text, "annotations"):
                    for annotation in messages.data[0].content[0].text.annotations:
                        if hasattr(annotation, "file_citation"):
                            citations.append(
                                {
                                    "file_id": annotation.file_citation.file_id,
                                    "quote": annotation.text,
                                }
                            )

                result = {
                    "success": True,
                    "query": query,
                    "results": response,
                    "citations_count": len(citations),
                    "status": "completed",
                    "retry_attempts": total_retries,
                }

                if include_metadata:
                    result["metadata"] = {
                        "vector_store_id": self.vector_store_id,
                        "max_results": max_results,
                        "citations": citations[:max_results] if citations else [],
                    }
            else:
                result = {
                    "success": False,
                    "query": query,
                    "error": f"Search failed with status: {run.status}",
                    "status": run.status,
                    "retry_attempts": total_retries,
                }

            _, attempts = self._with_retry(
                self.client.beta.assistants.delete,
                timeout=timeout,
                assistant_id=assistant.id,
            )
            total_retries += attempts

            return result
        except Exception as e:
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "status": "error",
                "retry_attempts": total_retries,
            }

    def search_similar_articles(
        self, topic: str, limit: int = 3, timeout: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Find similar articles in the knowledge base"""
        search_result = self.search(
            f"Find articles similar to or about: {topic}",
            max_results=limit,
            timeout=timeout,
        )

        if search_result["success"]:
            return self._parse_article_results(search_result["results"])
        return []

    def get_dakota_insights(
        self, topic: str, timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get Dakota-specific insights on a topic"""
        search_result = self.search(
            f"Dakota Way philosophy and insights about: {topic}",
            max_results=3,
            timeout=timeout,
        )

        return {
            "success": search_result["success"],
            "insights": search_result.get("results", ""),
            "topic": topic,
        }

    def verify_fact(
        self, claim: str, timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """Verify a claim against the knowledge base"""
        search_result = self.search(
            f"Verify this claim with evidence: {claim}", max_results=5, timeout=timeout
        )

        return {
            "claim": claim,
            "verification_status": "verified" if search_result["success"] else "unverified",
            "evidence": search_result.get("results", ""),
            "citations_count": search_result.get("citations_count", 0),
        }

    def _parse_article_results(self, results_text: str) -> List[Dict[str, Any]]:
        """Parse article results from search text"""
        articles = []
        lines = results_text.split("\n")

        current_article = {}
        for line in lines:
            if line.strip().startswith("Article:") or line.strip().startswith("Title:"):
                if current_article:
                    articles.append(current_article)
                current_article = {"title": line.replace("Article:", "").replace("Title:", "").strip()}
            elif line.strip() and current_article:
                if "summary" not in current_article:
                    current_article["summary"] = line.strip()
                else:
                    current_article["summary"] += " " + line.strip()

        if current_article:
            articles.append(current_article)

        return articles[:3]  # Return top 3 articles


# Convenience function for backward compatibility
def search_knowledge_base(query: str, max_results: int = 5, timeout: Optional[float] = None) -> str:
    """Legacy function for knowledge base search"""
    searcher = KnowledgeBaseSearcher(timeout=timeout)
    result = searcher.search(query, max_results, timeout=timeout)

    if result["success"]:
        return result["results"]
    else:
        return f"Search failed: {result.get('error', 'Unknown error')}"
