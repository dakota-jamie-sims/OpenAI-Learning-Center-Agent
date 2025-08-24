"""
Simple Connection Pool Wrapper for OpenAI Clients
Provides basic connection reuse without complex async management
"""
import os
from typing import Dict, Optional, List
from openai import OpenAI
import threading
import time

from src.utils.logging import get_logger

logger = get_logger(__name__)


class SimpleConnectionPool:
    """Simple thread-safe connection pool for OpenAI clients"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self.clients: Dict[str, List[OpenAI]] = {}
            self.available: Dict[str, List[bool]] = {}
            self.pool_sizes: Dict[str, int] = {
                "default": 3,
                "search": 5,
                "content": 3
            }
            self._initialized = True
            self._init_pools()
    
    def _init_pools(self):
        """Initialize connection pools"""
        for pool_name, size in self.pool_sizes.items():
            self.clients[pool_name] = []
            self.available[pool_name] = []
            
            for _ in range(size):
                client = OpenAI()
                self.clients[pool_name].append(client)
                self.available[pool_name].append(True)
            
            logger.info(f"Initialized pool '{pool_name}' with {size} clients")
    
    def get_client(self, pool_name: str = "default") -> Optional[OpenAI]:
        """Get an available client from the pool"""
        if pool_name not in self.clients:
            pool_name = "default"
        
        with self._lock:
            for i, is_available in enumerate(self.available[pool_name]):
                if is_available:
                    self.available[pool_name][i] = False
                    return self.clients[pool_name][i]
        
        # If no client available, create a new one
        logger.warning(f"No available clients in pool '{pool_name}', creating new one")
        return OpenAI()
    
    def release_client(self, client: OpenAI, pool_name: str = "default"):
        """Release a client back to the pool"""
        if pool_name not in self.clients:
            pool_name = "default"
        
        with self._lock:
            for i, pool_client in enumerate(self.clients[pool_name]):
                if pool_client == client:
                    self.available[pool_name][i] = True
                    return
    
    def get_pool_stats(self) -> Dict[str, Dict[str, int]]:
        """Get statistics for all pools"""
        stats = {}
        with self._lock:
            for pool_name in self.clients:
                available_count = sum(self.available[pool_name])
                stats[pool_name] = {
                    "total": len(self.clients[pool_name]),
                    "available": available_count,
                    "in_use": len(self.clients[pool_name]) - available_count
                }
        return stats


# Global instance
_connection_pool = SimpleConnectionPool()


def get_pooled_client(pool_name: str = "default") -> OpenAI:
    """Get a client from the connection pool"""
    return _connection_pool.get_client(pool_name)


def release_pooled_client(client: OpenAI, pool_name: str = "default"):
    """Release a client back to the pool"""
    _connection_pool.release_client(client, pool_name)


def get_pool_stats() -> Dict[str, Dict[str, int]]:
    """Get connection pool statistics"""
    return _connection_pool.get_pool_stats()


# Context manager for automatic client management
class PooledClient:
    """Context manager for pooled clients"""
    
    def __init__(self, pool_name: str = "default"):
        self.pool_name = pool_name
        self.client = None
    
    def __enter__(self) -> OpenAI:
        self.client = get_pooled_client(self.pool_name)
        return self.client
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            release_pooled_client(self.client, self.pool_name)