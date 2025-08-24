"""
Global OpenAI Connection Pool Manager
Provides thread-safe connection pooling for all OpenAI API calls
"""
import asyncio
import time
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager
import logging
from dataclasses import dataclass
from datetime import datetime

from openai import OpenAI
from prometheus_client import Gauge, Counter, Histogram

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Metrics
pool_size_gauge = Gauge('openai_pool_size', 'Size of connection pool', ['pool_name'])
pool_available_gauge = Gauge('openai_pool_available', 'Available connections', ['pool_name'])
pool_wait_time = Histogram('openai_pool_wait_seconds', 'Time waiting for connection', ['pool_name'])
pool_errors = Counter('openai_pool_errors_total', 'Connection pool errors', ['pool_name', 'error_type'])


@dataclass
class PooledClient:
    """Wrapper for a pooled OpenAI client"""
    client: OpenAI
    created_at: float
    last_used: float
    request_count: int = 0
    error_count: int = 0
    pool_name: str = "default"


class GlobalConnectionPool:
    """Singleton connection pool for OpenAI clients"""
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.pools: Dict[str, asyncio.Queue] = {}
            self.pool_configs: Dict[str, Dict[str, Any]] = {}
            self.semaphores: Dict[str, asyncio.Semaphore] = {}
            self._initialized = True
            logger.info("Initialized global connection pool manager")
    
    async def create_pool(
        self,
        pool_name: str = "default",
        pool_size: int = 10,
        max_requests_per_client: int = 1000,
        client_ttl: int = 3600  # 1 hour
    ):
        """Create a named connection pool"""
        if pool_name in self.pools:
            logger.warning(f"Pool {pool_name} already exists")
            return
        
        self.pools[pool_name] = asyncio.Queue(maxsize=pool_size)
        self.semaphores[pool_name] = asyncio.Semaphore(pool_size)
        self.pool_configs[pool_name] = {
            "size": pool_size,
            "max_requests": max_requests_per_client,
            "ttl": client_ttl
        }
        
        # Initialize pool with clients
        for _ in range(pool_size):
            client = PooledClient(
                client=OpenAI(),
                created_at=time.time(),
                last_used=time.time(),
                pool_name=pool_name
            )
            await self.pools[pool_name].put(client)
        
        # Update metrics
        pool_size_gauge.labels(pool_name=pool_name).set(pool_size)
        pool_available_gauge.labels(pool_name=pool_name).set(pool_size)
        
        logger.info(f"Created connection pool '{pool_name}' with {pool_size} clients")
    
    @asynccontextmanager
    async def acquire_client(self, pool_name: str = "default", timeout: float = 30.0):
        """Acquire a client from the pool with context manager"""
        if pool_name not in self.pools:
            # Auto-create default pool if needed
            await self.create_pool(pool_name)
        
        pool = self.pools[pool_name]
        semaphore = self.semaphores[pool_name]
        config = self.pool_configs[pool_name]
        
        start_time = time.time()
        pooled_client = None
        
        try:
            # Wait for available connection
            async with semaphore:
                with pool_wait_time.labels(pool_name=pool_name).time():
                    pooled_client = await asyncio.wait_for(
                        pool.get(),
                        timeout=timeout
                    )
                
                pool_available_gauge.labels(pool_name=pool_name).dec()
                
                # Check if client needs refresh
                current_time = time.time()
                if (pooled_client.request_count >= config["max_requests"] or
                    current_time - pooled_client.created_at > config["ttl"]):
                    
                    logger.info(f"Refreshing client in pool '{pool_name}'")
                    pooled_client = PooledClient(
                        client=OpenAI(),
                        created_at=current_time,
                        last_used=current_time,
                        pool_name=pool_name
                    )
                
                pooled_client.last_used = current_time
                pooled_client.request_count += 1
                
                yield pooled_client.client
                
        except asyncio.TimeoutError:
            pool_errors.labels(pool_name=pool_name, error_type="timeout").inc()
            raise TimeoutError(f"Timeout waiting for client from pool '{pool_name}'")
            
        except Exception as e:
            pool_errors.labels(pool_name=pool_name, error_type="acquire").inc()
            if pooled_client:
                pooled_client.error_count += 1
            raise
            
        finally:
            # Return client to pool
            if pooled_client and pool_name in self.pools:
                await pool.put(pooled_client)
                pool_available_gauge.labels(pool_name=pool_name).inc()
    
    async def get_pool_stats(self, pool_name: str = "default") -> Dict[str, Any]:
        """Get statistics for a connection pool"""
        if pool_name not in self.pools:
            return {"error": f"Pool '{pool_name}' not found"}
        
        pool = self.pools[pool_name]
        config = self.pool_configs[pool_name]
        
        # Calculate stats
        total_clients = config["size"]
        available_clients = pool.qsize()
        
        return {
            "pool_name": pool_name,
            "total_clients": total_clients,
            "available_clients": available_clients,
            "busy_clients": total_clients - available_clients,
            "utilization": (total_clients - available_clients) / total_clients,
            "config": config
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all connection pools"""
        health = {
            "status": "healthy",
            "pools": {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for pool_name in self.pools:
            stats = await self.get_pool_stats(pool_name)
            health["pools"][pool_name] = stats
            
            # Mark unhealthy if utilization is too high
            if stats.get("utilization", 0) > 0.9:
                health["status"] = "degraded"
                health["warnings"] = health.get("warnings", [])
                health["warnings"].append(f"Pool '{pool_name}' at {stats['utilization']*100:.1f}% utilization")
        
        return health
    
    async def shutdown(self):
        """Gracefully shutdown all connection pools"""
        logger.info("Shutting down connection pools...")
        
        for pool_name, pool in self.pools.items():
            # Drain the pool
            while not pool.empty():
                try:
                    pooled_client = await pool.get_nowait()
                    # Could close clients here if needed
                except asyncio.QueueEmpty:
                    break
            
            logger.info(f"Shutdown pool '{pool_name}'")
        
        self.pools.clear()
        self.semaphores.clear()
        self.pool_configs.clear()


# Global instance
_global_pool = GlobalConnectionPool()


async def get_connection_pool() -> GlobalConnectionPool:
    """Get the global connection pool instance"""
    return _global_pool


async def acquire_openai_client(pool_name: str = "default", timeout: float = 30.0):
    """Convenience function to acquire a client from the global pool"""
    pool = await get_connection_pool()
    return pool.acquire_client(pool_name, timeout)


# Specialized pools for different agent types
async def initialize_agent_pools():
    """Initialize specialized connection pools for different agent types"""
    pool = await get_connection_pool()
    
    # High-throughput pool for KB/Web searches
    await pool.create_pool(
        pool_name="search",
        pool_size=15,
        max_requests_per_client=2000,
        client_ttl=1800  # 30 minutes
    )
    
    # Standard pool for content generation
    await pool.create_pool(
        pool_name="content",
        pool_size=8,
        max_requests_per_client=500,
        client_ttl=3600  # 1 hour
    )
    
    # Small pool for orchestration/coordination
    await pool.create_pool(
        pool_name="orchestrator",
        pool_size=3,
        max_requests_per_client=1000,
        client_ttl=3600
    )
    
    # Analysis pool for metrics/fact-checking
    await pool.create_pool(
        pool_name="analysis",
        pool_size=5,
        max_requests_per_client=1000,
        client_ttl=3600
    )
    
    logger.info("Initialized all agent-specific connection pools")