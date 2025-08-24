"""
Production-optimized Knowledge Base Search Service V2
Features:
- Connection pooling for OpenAI clients
- In-memory and Redis caching
- Batch search optimization
- Circuit breaker pattern
- Metrics collection
"""
import os
import time
import asyncio
import hashlib
import json
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
import logging
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
import redis
from prometheus_client import Counter, Histogram, Gauge

from src.config import VECTOR_STORE_ID
from src.utils.logging import get_logger
from src.utils.circuit_breaker import CircuitBreaker

logger = get_logger(__name__)

# Metrics
kb_search_counter = Counter('kb_search_total', 'Total KB searches', ['status'])
kb_search_duration = Histogram('kb_search_duration_seconds', 'KB search duration')
kb_cache_hits = Counter('kb_cache_hits_total', 'Cache hits')
kb_cache_misses = Counter('kb_cache_misses_total', 'Cache misses')
active_searches = Gauge('kb_active_searches', 'Currently active searches')

# Configuration
MAX_CONCURRENT_SEARCHES = 5
CACHE_TTL = 3600  # 1 hour
BATCH_SIZE = 10
TIMEOUT_SECONDS = 5  # Reduced from 10-20 seconds


class ConnectionPool:
    """OpenAI client connection pool"""
    
    def __init__(self, pool_size: int = 5):
        self.pool_size = pool_size
        self.clients = []
        self.available = asyncio.Queue(maxsize=pool_size)
        self.semaphore = asyncio.Semaphore(pool_size)
        self._initialized = False
        
    async def initialize(self):
        """Initialize the connection pool"""
        if self._initialized:
            return
            
        for _ in range(self.pool_size):
            client = OpenAI()
            self.clients.append(client)
            await self.available.put(client)
        
        self._initialized = True
        logger.info(f"Initialized connection pool with {self.pool_size} clients")
    
    async def acquire(self) -> OpenAI:
        """Acquire a client from the pool"""
        if not self._initialized:
            await self.initialize()
        
        async with self.semaphore:
            client = await self.available.get()
            return client
    
    async def release(self, client: OpenAI):
        """Release a client back to the pool"""
        await self.available.put(client)


class ProductionKBSearchV2:
    """Production-optimized KB search with all performance enhancements"""
    
    def __init__(self):
        self.vector_store_id = VECTOR_STORE_ID or os.getenv("OPENAI_VECTOR_STORE_ID")
        
        if not self.vector_store_id:
            raise ValueError("VECTOR_STORE_ID not configured!")
        
        # Connection pool
        self.connection_pool = ConnectionPool(pool_size=5)
        
        # Thread pool for CPU-bound operations
        self.thread_pool = ThreadPoolExecutor(max_workers=4)
        
        # In-memory cache
        self.memory_cache = {}
        self.cache_timestamps = {}
        
        # Redis cache (optional)
        self.redis_client = self._init_redis()
        
        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
            expected_exception=Exception
        )
        
        # Batch queue
        self.batch_queue = asyncio.Queue()
        self.batch_results = {}
        self.batch_processor_task = None
        
    def _init_redis(self) -> Optional[redis.Redis]:
        """Initialize Redis connection if available"""
        try:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            client = redis.from_url(redis_url, decode_responses=True)
            client.ping()
            logger.info("Connected to Redis for distributed caching")
            return client
        except:
            logger.warning("Redis not available, using in-memory cache only")
            return None
    
    def _cache_key(self, query: str) -> str:
        """Generate cache key for a query"""
        return f"kb_search:{hashlib.md5(query.encode()).hexdigest()}"
    
    async def _get_from_cache(self, query: str) -> Optional[Dict[str, Any]]:
        """Get result from cache (memory first, then Redis)"""
        cache_key = self._cache_key(query)
        
        # Check memory cache
        if cache_key in self.memory_cache:
            timestamp = self.cache_timestamps.get(cache_key, 0)
            if time.time() - timestamp < CACHE_TTL:
                kb_cache_hits.inc()
                logger.debug(f"Memory cache hit for: {query[:50]}...")
                return self.memory_cache[cache_key]
        
        # Check Redis cache
        if self.redis_client:
            try:
                cached = self.redis_client.get(cache_key)
                if cached:
                    kb_cache_hits.inc()
                    result = json.loads(cached)
                    # Store in memory cache for faster access
                    self.memory_cache[cache_key] = result
                    self.cache_timestamps[cache_key] = time.time()
                    logger.debug(f"Redis cache hit for: {query[:50]}...")
                    return result
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")
        
        kb_cache_misses.inc()
        return None
    
    async def _set_cache(self, query: str, result: Dict[str, Any]):
        """Set result in cache (both memory and Redis)"""
        cache_key = self._cache_key(query)
        
        # Memory cache
        self.memory_cache[cache_key] = result
        self.cache_timestamps[cache_key] = time.time()
        
        # Redis cache
        if self.redis_client:
            try:
                self.redis_client.setex(
                    cache_key,
                    CACHE_TTL,
                    json.dumps(result)
                )
            except Exception as e:
                logger.warning(f"Redis cache set error: {e}")
    
    @retry(
        stop=stop_after_attempt(2),  # Reduced retries
        wait=wait_exponential(min=0.5, max=2)  # Faster retries
    )
    async def _search_with_client(self, client: OpenAI, query: str, max_results: int) -> Dict[str, Any]:
        """Execute search with a specific client"""
        active_searches.inc()
        try:
            # Use asyncio.wait_for for strict timeout control
            async def _do_search():
                return await asyncio.to_thread(
                    client.responses.create,
                    model="gpt-5-nano",  # Fastest model for search
                    input=f"Search for: {query}",
                    tools=[{
                        "type": "file_search",
                        "vector_store_ids": [self.vector_store_id],
                        "max_num_results": max_results
                    }],
                    reasoning={"effort": "minimal"},
                    text={"verbosity": "low"}
                )
            
            response = await asyncio.wait_for(_do_search(), timeout=TIMEOUT_SECONDS)
            
            # Fast extraction
            results = self._fast_extract_results(response)
            return {
                "success": True,
                "query": query,
                "results": results["formatted"],
                "sources": results["sources"],
                "relevance_scores": results["scores"]
            }
            
        finally:
            active_searches.dec()
    
    def _fast_extract_results(self, response) -> Dict[str, Any]:
        """Fast extraction of search results"""
        results = {
            "formatted": "",
            "sources": [],
            "scores": []
        }
        
        # Quick extraction without complex parsing
        if hasattr(response, 'output_text') and response.output_text:
            results["formatted"] = response.output_text
        elif hasattr(response, 'output') and response.output:
            # Extract from first message content
            for item in response.output:
                if hasattr(item, 'content'):
                    if isinstance(item.content, str):
                        results["formatted"] = item.content
                        break
                    elif isinstance(item.content, list) and item.content:
                        if hasattr(item.content[0], 'text'):
                            results["formatted"] = item.content[0].text
                            break
        
        # Extract source metadata if available
        if hasattr(response, 'citations'):
            for citation in response.citations[:5]:  # Limit to top 5
                results["sources"].append({
                    "title": getattr(citation, 'title', 'Unknown'),
                    "url": getattr(citation, 'url', ''),
                    "score": getattr(citation, 'score', 0.0)
                })
                results["scores"].append(getattr(citation, 'score', 0.0))
        
        return results
    
    async def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Main search method with all optimizations"""
        start_time = time.time()
        
        # Check cache first
        cached = await self._get_from_cache(query)
        if cached:
            return cached
        
        # Circuit breaker check
        if self.circuit_breaker.state == "open":
            kb_search_counter.labels(status='circuit_open').inc()
            return {
                "success": False,
                "query": query,
                "error": "Circuit breaker is open",
                "results": ""
            }
        
        try:
            with kb_search_duration.time():
                # Acquire client from pool
                client = await self.connection_pool.acquire()
                
                try:
                    # Execute search with circuit breaker
                    result = await self.circuit_breaker.call(
                        self._search_with_client,
                        client, query, max_results
                    )
                    
                    # Cache successful result
                    await self._set_cache(query, result)
                    
                    kb_search_counter.labels(status='success').inc()
                    
                    elapsed = time.time() - start_time
                    logger.info(f"KB search completed in {elapsed:.2f}s for: {query[:50]}...")
                    
                    return result
                    
                finally:
                    # Always release client back to pool
                    await self.connection_pool.release(client)
                    
        except Exception as e:
            kb_search_counter.labels(status='error').inc()
            logger.error(f"KB search error: {str(e)}")
            
            # Return degraded response
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "results": self._get_fallback_results(query)
            }
    
    async def batch_search(self, queries: List[str], max_results_per_query: int = 3) -> List[Dict[str, Any]]:
        """Efficient batch search with parallel execution"""
        # Check cache for all queries first
        results = []
        uncached_queries = []
        
        for query in queries:
            cached = await self._get_from_cache(query)
            if cached:
                results.append((query, cached))
            else:
                uncached_queries.append(query)
        
        if uncached_queries:
            # Process uncached queries in parallel with semaphore
            semaphore = asyncio.Semaphore(MAX_CONCURRENT_SEARCHES)
            
            async def _search_with_semaphore(query):
                async with semaphore:
                    return await self.search(query, max_results_per_query)
            
            # Execute searches in parallel
            search_tasks = [
                _search_with_semaphore(query) 
                for query in uncached_queries
            ]
            
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Combine results
            for query, result in zip(uncached_queries, search_results):
                if isinstance(result, Exception):
                    result = {
                        "success": False,
                        "query": query,
                        "error": str(result),
                        "results": ""
                    }
                results.append((query, result))
        
        # Sort results to match original query order
        query_to_result = dict(results)
        return [query_to_result[q] for q in queries]
    
    def _get_fallback_results(self, query: str) -> str:
        """Fast fallback results for degraded mode"""
        # Quick keyword matching against known topics
        keywords = query.lower().split()
        
        fallback_topics = {
            "family office": "Dakota has extensive resources on family offices including geographic guides and investment trends.",
            "private equity": "See Dakota's PE fund databases and regional firm rankings.",
            "ria": "Explore Dakota's RIA databases and top firm rankings by metro area.",
            "venture capital": "Dakota covers VC trends, emerging managers, and fund databases.",
            "hedge fund": "Dakota provides hedge fund databases and allocation insights."
        }
        
        for keyword, response in fallback_topics.items():
            if any(kw in keyword for kw in keywords):
                return response
        
        return "Please check Dakota's Learning Center for relevant articles."
    
    async def start_batch_processor(self):
        """Start background batch processor for optimal throughput"""
        if self.batch_processor_task is None:
            self.batch_processor_task = asyncio.create_task(self._batch_processor())
            logger.info("Started batch processor for KB searches")
    
    async def _batch_processor(self):
        """Process searches in batches for efficiency"""
        while True:
            batch = []
            
            # Collect up to BATCH_SIZE queries or wait up to 100ms
            try:
                for _ in range(BATCH_SIZE):
                    query = await asyncio.wait_for(
                        self.batch_queue.get(),
                        timeout=0.1
                    )
                    batch.append(query)
            except asyncio.TimeoutError:
                pass
            
            if batch:
                # Process batch
                results = await self.batch_search([q[0] for q in batch])
                
                # Store results
                for (query, result_future), result in zip(batch, results):
                    result_future.set_result(result)
    
    async def enqueue_search(self, query: str) -> Dict[str, Any]:
        """Add search to batch queue for processing"""
        result_future = asyncio.Future()
        await self.batch_queue.put((query, result_future))
        return await result_future


# Global instance with lazy initialization
_searcher = None
_initialization_lock = asyncio.Lock()


async def get_production_kb_searcher() -> ProductionKBSearchV2:
    """Get or create production searcher instance"""
    global _searcher
    
    if _searcher is None:
        async with _initialization_lock:
            if _searcher is None:
                _searcher = ProductionKBSearchV2()
                await _searcher.connection_pool.initialize()
                await _searcher.start_batch_processor()
    
    return _searcher


async def search_kb_production_v2(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Production KB search with all optimizations"""
    searcher = await get_production_kb_searcher()
    return await searcher.search(query, max_results)


async def batch_search_kb_production_v2(queries: List[str], max_results_per_query: int = 3) -> List[Dict[str, Any]]:
    """Batch KB search for multiple queries"""
    searcher = await get_production_kb_searcher()
    return await searcher.batch_search(queries, max_results_per_query)