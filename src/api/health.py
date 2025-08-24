"""
Production Health Check and Monitoring Endpoints
"""
import os
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List
import psutil
import json

from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from src.utils.logging import get_logger
from src.services.openai_connection_pool import get_connection_pool
from src.services.kb_search_production_v2 import get_production_kb_searcher

logger = get_logger(__name__)

app = FastAPI(
    title="Dakota Content System Health",
    description="Health checks and monitoring for the Dakota content generation system",
    version="2.0.0"
)


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint"""
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "dakota-content-system",
        "version": "2.0.0"
    }
    
    # Check system resources
    health["system"] = {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage('/').percent
    }
    
    # Determine overall health
    if health["system"]["cpu_percent"] > 90:
        health["status"] = "degraded"
        health["warnings"] = health.get("warnings", [])
        health["warnings"].append("High CPU usage")
    
    if health["system"]["memory_percent"] > 90:
        health["status"] = "degraded"
        health["warnings"] = health.get("warnings", [])
        health["warnings"].append("High memory usage")
    
    return health


@app.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with component status"""
    start_time = time.time()
    
    health = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {},
        "checks_passed": 0,
        "checks_failed": 0
    }
    
    # Check OpenAI connection pool
    try:
        pool = await get_connection_pool()
        pool_health = await pool.health_check()
        health["components"]["connection_pool"] = {
            "status": pool_health["status"],
            "pools": pool_health["pools"]
        }
        health["checks_passed"] += 1
    except Exception as e:
        health["components"]["connection_pool"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health["checks_failed"] += 1
        health["status"] = "unhealthy"
    
    # Check KB search service
    try:
        kb_searcher = await get_production_kb_searcher()
        # Quick test search
        test_result = await asyncio.wait_for(
            kb_searcher.search("test", max_results=1),
            timeout=5.0
        )
        health["components"]["kb_search"] = {
            "status": "healthy" if test_result.get("success") else "degraded",
            "response_time": test_result.get("search_time", 0),
            "circuit_breaker_state": kb_searcher.circuit_breaker.state
        }
        health["checks_passed"] += 1
    except Exception as e:
        health["components"]["kb_search"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health["checks_failed"] += 1
        health["status"] = "unhealthy"
    
    # Check Redis connection
    try:
        kb_searcher = await get_production_kb_searcher()
        if kb_searcher.redis_client:
            kb_searcher.redis_client.ping()
            health["components"]["redis"] = {"status": "healthy"}
            health["checks_passed"] += 1
        else:
            health["components"]["redis"] = {"status": "not_configured"}
    except Exception as e:
        health["components"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health["checks_failed"] += 1
    
    # Check vector store
    try:
        vector_store_id = os.getenv("OPENAI_VECTOR_STORE_ID")
        if vector_store_id:
            health["components"]["vector_store"] = {
                "status": "configured",
                "id": vector_store_id
            }
            health["checks_passed"] += 1
        else:
            health["components"]["vector_store"] = {"status": "not_configured"}
            health["status"] = "degraded"
    except Exception as e:
        health["components"]["vector_store"] = {
            "status": "error",
            "error": str(e)
        }
        health["checks_failed"] += 1
    
    # Add timing
    health["check_duration_ms"] = int((time.time() - start_time) * 1000)
    
    # Determine overall status
    if health["checks_failed"] > 0:
        health["status"] = "unhealthy"
    elif health["checks_failed"] == 0 and health["status"] != "unhealthy":
        health["status"] = "healthy"
    
    return health


@app.get("/metrics", response_class=PlainTextResponse)
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Kubernetes readiness probe"""
    try:
        # Check if all critical components are ready
        pool = await get_connection_pool()
        pool_stats = await pool.health_check()
        
        # System is ready if at least one pool is available
        ready = any(
            pool_data.get("available_clients", 0) > 0 
            for pool_data in pool_stats["pools"].values()
        )
        
        if ready:
            return {"ready": True, "timestamp": datetime.utcnow().isoformat()}
        else:
            return {"ready": False, "reason": "No available connections"}
            
    except Exception as e:
        return {"ready": False, "reason": str(e)}


@app.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """Kubernetes liveness probe"""
    # Simple check that the service is running
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": time.time() - app.state.start_time if hasattr(app.state, 'start_time') else 0
    }


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    app.state.start_time = time.time()
    
    # Initialize connection pools
    try:
        from src.services.openai_connection_pool import initialize_agent_pools
        await initialize_agent_pools()
        logger.info("Initialized agent connection pools")
    except Exception as e:
        logger.error(f"Failed to initialize connection pools: {e}")
    
    # Start KB search batch processor
    try:
        kb_searcher = await get_production_kb_searcher()
        logger.info("KB search service ready")
    except Exception as e:
        logger.error(f"Failed to initialize KB search: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        pool = await get_connection_pool()
        await pool.shutdown()
        logger.info("Shutdown connection pools")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# Performance monitoring endpoints
@app.get("/performance/agents")
async def agent_performance() -> Dict[str, Any]:
    """Get agent performance metrics"""
    from prometheus_client import REGISTRY
    
    metrics = {
        "timestamp": datetime.utcnow().isoformat(),
        "agents": {}
    }
    
    # Extract metrics from Prometheus registry
    for collector in REGISTRY.collect():
        if collector.name.startswith("agent_"):
            for sample in collector.samples:
                agent_name = sample.labels.get("agent", "unknown")
                metric_type = collector.name.replace("agent_", "")
                
                if agent_name not in metrics["agents"]:
                    metrics["agents"][agent_name] = {}
                
                metrics["agents"][agent_name][metric_type] = sample.value
    
    return metrics


@app.get("/performance/kb-search")
async def kb_search_performance() -> Dict[str, Any]:
    """Get KB search performance metrics"""
    kb_searcher = await get_production_kb_searcher()
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "circuit_breaker": {
            "state": kb_searcher.circuit_breaker.state,
            "failure_count": kb_searcher.circuit_breaker.failure_count,
            "last_failure": kb_searcher.circuit_breaker.last_failure_time
        },
        "cache": {
            "memory_entries": len(kb_searcher.memory_cache),
            "cache_ttl": kb_searcher.cache_ttl
        },
        "active_searches": active_searches._value.get() if 'active_searches' in globals() else 0
    }


# Testing endpoints (disable in production)
if os.getenv("ENVIRONMENT") != "production":
    @app.post("/test/generate-article")
    async def test_generate_article(topic: str, word_count: int = 1000) -> Dict[str, Any]:
        """Test article generation endpoint"""
        from src.agents.dakota_agents.orchestrator_v2 import DakotaOrchestratorV2
        from src.models import ArticleRequest
        
        try:
            orchestrator = DakotaOrchestratorV2()
            request = ArticleRequest(
                topic=topic,
                audience="institutional investors",
                tone="professional",
                word_count=word_count
            )
            
            result = await orchestrator.execute({"request": request})
            
            return {
                "success": result["success"],
                "generation_time": result.get("data", {}).get("generation_time", 0),
                "output_folder": result.get("data", {}).get("output_folder", ""),
                "error": result.get("error")
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }