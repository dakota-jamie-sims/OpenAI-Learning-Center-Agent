"""Simple test to demonstrate async parallel execution"""
import asyncio
import time


async def simulate_web_search(query: str, delay: float = 2.0):
    """Simulate web search with delay"""
    print(f"[{time.time():.2f}] Web search started: {query}")
    await asyncio.sleep(delay)
    print(f"[{time.time():.2f}] Web search completed")
    return {"source": "web", "results": ["result1", "result2"]}


async def simulate_kb_search(query: str, delay: float = 1.5):
    """Simulate knowledge base search with delay"""
    print(f"[{time.time():.2f}] KB search started: {query}")
    await asyncio.sleep(delay)
    print(f"[{time.time():.2f}] KB search completed")
    return {"source": "kb", "results": ["kb_result1", "kb_result2"]}


async def simulate_dakota_search(query: str, delay: float = 1.0):
    """Simulate Dakota-specific search with delay"""
    print(f"[{time.time():.2f}] Dakota search started: {query}")
    await asyncio.sleep(delay)
    print(f"[{time.time():.2f}] Dakota search completed")
    return {"source": "dakota", "results": ["dakota_insight1"]}


async def parallel_research(query: str):
    """Execute all searches in parallel"""
    print(f"\n=== PARALLEL EXECUTION ===")
    start = time.time()
    
    # Create all tasks - they start immediately
    web_task = asyncio.create_task(simulate_web_search(query))
    kb_task = asyncio.create_task(simulate_kb_search(query))
    dakota_task = asyncio.create_task(simulate_dakota_search(query))
    
    # Wait for all to complete
    web_result, kb_result, dakota_result = await asyncio.gather(
        web_task, kb_task, dakota_task
    )
    
    total_time = time.time() - start
    print(f"\nTotal parallel execution time: {total_time:.2f}s")
    print(f"Expected if sequential: ~4.5s")
    print(f"Expected if parallel: ~2.0s (longest task)")
    
    return web_result, kb_result, dakota_result


def sequential_research(query: str):
    """Execute all searches sequentially for comparison"""
    print(f"\n=== SEQUENTIAL EXECUTION ===")
    start = time.time()
    
    # Run each search one after another
    print(f"[{time.time():.2f}] Web search started: {query}")
    time.sleep(2.0)
    print(f"[{time.time():.2f}] Web search completed")
    web_result = {"source": "web", "results": ["result1", "result2"]}
    
    print(f"[{time.time():.2f}] KB search started: {query}")
    time.sleep(1.5)
    print(f"[{time.time():.2f}] KB search completed")
    kb_result = {"source": "kb", "results": ["kb_result1", "kb_result2"]}
    
    print(f"[{time.time():.2f}] Dakota search started: {query}")
    time.sleep(1.0)
    print(f"[{time.time():.2f}] Dakota search completed")
    dakota_result = {"source": "dakota", "results": ["dakota_insight1"]}
    
    total_time = time.time() - start
    print(f"\nTotal sequential execution time: {total_time:.2f}s")
    
    return web_result, kb_result, dakota_result


async def main():
    query = "private equity trends 2025"
    
    # Show sequential execution
    sequential_research(query)
    
    # Show parallel execution
    await parallel_research(query)
    
    print("\n✅ Parallel execution is ~2.5x faster!")


if __name__ == "__main__":
    asyncio.run(main())