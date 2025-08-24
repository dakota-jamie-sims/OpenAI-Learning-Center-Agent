#!/usr/bin/env python3
"""
Test script for production system components
Tests each new component individually
"""
import asyncio
import sys
import os
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Test results
test_results = {
    "passed": [],
    "failed": [],
    "warnings": []
}

def log_result(test_name: str, status: str, message: str = ""):
    """Log test result"""
    if status == "PASS":
        test_results["passed"].append(test_name)
        print(f"✅ {test_name}: PASSED")
    elif status == "FAIL":
        test_results["failed"].append((test_name, message))
        print(f"❌ {test_name}: FAILED - {message}")
    elif status == "WARN":
        test_results["warnings"].append((test_name, message))
        print(f"⚠️  {test_name}: WARNING - {message}")
    
    if message and status == "FAIL":
        print(f"   Error: {message}")


async def test_imports():
    """Test if all modules can be imported"""
    print("\n=== Testing Imports ===")
    
    # Test new production modules
    modules_to_test = [
        ("KB Search V2", "src.services.kb_search_production_v2"),
        ("Connection Pool", "src.services.openai_connection_pool"),
        ("Base Agent V2", "src.agents.dakota_agents.base_agent_v2"),
        ("Orchestrator V2", "src.agents.dakota_agents.orchestrator_v2"),
        ("Health API", "src.api.health"),
    ]
    
    for name, module in modules_to_test:
        try:
            exec(f"import {module}")
            log_result(f"Import {name}", "PASS")
        except ImportError as e:
            log_result(f"Import {name}", "FAIL", str(e))
        except Exception as e:
            log_result(f"Import {name}", "FAIL", f"Unexpected error: {e}")


async def test_connection_pool():
    """Test connection pool functionality"""
    print("\n=== Testing Connection Pool ===")
    
    try:
        from src.services.openai_connection_pool import get_connection_pool, initialize_agent_pools
        
        # Test pool initialization
        try:
            await initialize_agent_pools()
            log_result("Connection Pool Init", "PASS")
        except Exception as e:
            log_result("Connection Pool Init", "FAIL", str(e))
            return
        
        # Test acquiring client
        try:
            pool = await get_connection_pool()
            async with pool.acquire_client("search") as client:
                log_result("Acquire Client", "PASS")
        except Exception as e:
            log_result("Acquire Client", "FAIL", str(e))
        
        # Test pool stats
        try:
            stats = await pool.get_pool_stats("search")
            if stats.get("total_clients", 0) > 0:
                log_result("Pool Stats", "PASS", f"{stats['available_clients']}/{stats['total_clients']} available")
            else:
                log_result("Pool Stats", "FAIL", "No clients in pool")
        except Exception as e:
            log_result("Pool Stats", "FAIL", str(e))
            
    except ImportError as e:
        log_result("Connection Pool Test", "FAIL", f"Cannot import: {e}")


async def test_kb_search_v2():
    """Test KB Search V2 functionality"""
    print("\n=== Testing KB Search V2 ===")
    
    try:
        from src.services.kb_search_production_v2 import search_kb_production_v2, get_production_kb_searcher
        
        # Test searcher initialization
        try:
            searcher = await get_production_kb_searcher()
            log_result("KB Searcher Init", "PASS")
        except Exception as e:
            log_result("KB Searcher Init", "FAIL", str(e))
            return
        
        # Test search
        try:
            result = await search_kb_production_v2("test query", max_results=1)
            if result.get("success"):
                log_result("KB Search", "PASS", f"Search time: {result.get('search_time', 0):.2f}s")
            else:
                log_result("KB Search", "FAIL", result.get("error", "Unknown error"))
        except Exception as e:
            log_result("KB Search", "FAIL", str(e))
        
        # Test cache
        try:
            cache_size = len(searcher.memory_cache)
            log_result("KB Cache", "PASS", f"{cache_size} entries")
        except:
            log_result("KB Cache", "WARN", "Cannot check cache")
            
    except ImportError as e:
        log_result("KB Search V2 Test", "FAIL", f"Cannot import: {e}")


async def test_base_agent_v2():
    """Test Base Agent V2"""
    print("\n=== Testing Base Agent V2 ===")
    
    try:
        from src.agents.dakota_agents.base_agent_v2 import DakotaBaseAgentV2
        
        # Test instantiation
        try:
            agent = DakotaBaseAgentV2("test_agent")
            log_result("Base Agent Init", "PASS", f"Model: {agent.model}, Pool: {agent.pool_name}")
        except Exception as e:
            log_result("Base Agent Init", "FAIL", str(e))
            return
        
        # Test model selection
        if agent.model in ["gpt-5", "gpt-5-mini", "gpt-5-nano"]:
            log_result("Model Selection", "PASS", agent.model)
        else:
            log_result("Model Selection", "WARN", f"Unexpected model: {agent.model}")
            
    except ImportError as e:
        log_result("Base Agent V2 Test", "FAIL", f"Cannot import: {e}")


async def test_orchestrator_v2():
    """Test Orchestrator V2"""
    print("\n=== Testing Orchestrator V2 ===")
    
    try:
        from src.agents.dakota_agents.orchestrator_v2 import DakotaOrchestratorV2
        
        # Test instantiation
        try:
            orchestrator = DakotaOrchestratorV2()
            log_result("Orchestrator V2 Init", "PASS")
        except Exception as e:
            log_result("Orchestrator V2 Init", "FAIL", str(e))
            return
        
        # Check for missing V2 agents
        missing_agents = []
        v2_agents = [
            "kb_researcher_v2", "web_researcher_v2", "research_synthesizer_v2",
            "content_writer_v2", "fact_checker_v3", "iteration_manager_v2",
            "social_promoter_v2", "summary_writer_v2"
        ]
        
        for agent in v2_agents:
            try:
                exec(f"from src.agents.dakota_agents.{agent} import *")
            except ImportError:
                missing_agents.append(agent)
        
        if missing_agents:
            log_result("V2 Agent Imports", "FAIL", f"Missing: {', '.join(missing_agents)}")
        else:
            log_result("V2 Agent Imports", "PASS")
            
    except ImportError as e:
        log_result("Orchestrator V2 Test", "FAIL", f"Cannot import: {e}")


async def test_existing_agents_compatibility():
    """Test if existing agents work with new system"""
    print("\n=== Testing Existing Agent Compatibility ===")
    
    existing_agents = [
        "kb_researcher", "web_researcher", "research_synthesizer",
        "content_writer", "fact_checker_v2", "iteration_manager",
        "social_promoter", "summary_writer", "seo_specialist",
        "metrics_analyzer"
    ]
    
    compatible = []
    incompatible = []
    
    for agent in existing_agents:
        try:
            exec(f"from src.agents.dakota_agents.{agent} import *")
            compatible.append(agent)
        except ImportError:
            incompatible.append(agent)
    
    if compatible:
        log_result("Existing Agents Found", "PASS", f"{len(compatible)} agents available")
    
    if incompatible:
        log_result("Missing Agents", "WARN", f"Not found: {', '.join(incompatible)}")


async def test_health_endpoints():
    """Test health check endpoints"""
    print("\n=== Testing Health Endpoints ===")
    
    try:
        from src.api.health import app
        log_result("Health API Import", "PASS")
        
        # Check if FastAPI app is configured
        routes = [route.path for route in app.routes]
        expected_routes = ["/health", "/health/detailed", "/metrics", "/ready", "/live"]
        
        found_routes = [r for r in expected_routes if r in routes]
        missing_routes = [r for r in expected_routes if r not in routes]
        
        if found_routes:
            log_result("Health Routes", "PASS", f"Found {len(found_routes)} routes")
        
        if missing_routes:
            log_result("Missing Routes", "WARN", f"Missing: {', '.join(missing_routes)}")
            
    except ImportError as e:
        log_result("Health API Test", "FAIL", f"Cannot import: {e}")


async def test_environment():
    """Test environment setup"""
    print("\n=== Testing Environment ===")
    
    required_vars = ["OPENAI_API_KEY", "OPENAI_VECTOR_STORE_ID"]
    optional_vars = ["SERPER_API_KEY", "REDIS_URL"]
    
    for var in required_vars:
        if os.getenv(var):
            log_result(f"Env {var}", "PASS", "Set")
        else:
            log_result(f"Env {var}", "FAIL", "Not set")
    
    for var in optional_vars:
        if os.getenv(var):
            log_result(f"Env {var}", "PASS", "Set")
        else:
            log_result(f"Env {var}", "WARN", "Not set (optional)")


async def test_quick_integration():
    """Quick integration test"""
    print("\n=== Quick Integration Test ===")
    
    try:
        # Test if we can create a simple request
        from src.models import ArticleRequest
        request = ArticleRequest(
            topic="test topic",
            audience="test",
            tone="test",
            word_count=100
        )
        log_result("Article Request Model", "PASS")
    except Exception as e:
        log_result("Article Request Model", "FAIL", str(e))


def print_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    total_tests = len(test_results["passed"]) + len(test_results["failed"]) + len(test_results["warnings"])
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"✅ Passed: {len(test_results['passed'])}")
    print(f"❌ Failed: {len(test_results['failed'])}")
    print(f"⚠️  Warnings: {len(test_results['warnings'])}")
    
    if test_results["failed"]:
        print("\n❌ FAILED TESTS:")
        for test, error in test_results["failed"]:
            print(f"  - {test}: {error}")
    
    if test_results["warnings"]:
        print("\n⚠️  WARNINGS:")
        for test, warning in test_results["warnings"]:
            print(f"  - {test}: {warning}")
    
    print("\n" + "="*60)
    
    # Recommendations
    if test_results["failed"]:
        print("\n🔧 RECOMMENDATIONS:")
        
        if any("V2 Agent" in test for test, _ in test_results["failed"]):
            print("\n1. Create V2 agent adapters:")
            print("   - Copy existing agents and update to use base_agent_v2.py")
            print("   - Or create simple wrappers that use existing agents")
        
        if any("Connection Pool" in test for test, _ in test_results["failed"]):
            print("\n2. Fix connection pool issues:")
            print("   - Check OpenAI client compatibility")
            print("   - Verify async context manager implementation")
        
        print("\n3. For quick testing, modify orchestrator_v2.py to use existing agents:")
        print("   - Change imports from '_v2' to existing agent names")
        print("   - This allows testing the parallel architecture immediately")


async def main():
    """Run all tests"""
    print("🧪 TESTING PRODUCTION SYSTEM COMPONENTS")
    print("="*60)
    
    # Run tests in order
    await test_environment()
    await test_imports()
    await test_connection_pool()
    await test_kb_search_v2()
    await test_base_agent_v2()
    await test_orchestrator_v2()
    await test_existing_agents_compatibility()
    await test_health_endpoints()
    await test_quick_integration()
    
    # Print summary
    print_summary()


if __name__ == "__main__":
    asyncio.run(main())