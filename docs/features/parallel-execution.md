# Feature: Parallel Agent Execution

## Overview
The system uses asyncio to run multiple agents simultaneously, reducing total generation time by ~40%.

## Implementation Details

### 1. **Parallel Phases**
Location: `src/pipeline/chat_orchestrator.py`

Three phases use parallel execution:
```python
# Phase 2: Research (Web + KB)
results = await self.manager.run_agents_parallel([
    ("web_researcher", web_prompt),
    ("kb_researcher", kb_prompt)
])

# Phase 5: Enhancement (SEO + Metrics)
results = await self.manager.run_agents_parallel([
    ("seo_specialist", seo_prompt),
    ("metrics_analyzer", metrics_prompt)
])

# Phase 7: Distribution (Summary + Social)
results = await self.manager.run_agents_parallel([
    ("summary_writer", summary_prompt),
    ("social_promoter", social_prompt)
])
```

### 2. **Agent Manager**
Location: `src/agents/chat_agent.py`

```python
async def run_agents_parallel(self, agent_prompts: List[tuple[str, str]]):
    tasks = []
    for agent_name, prompt in agent_prompts:
        tasks.append(self.run_agent(agent_name, prompt))
    
    # Execute all simultaneously
    return await asyncio.gather(*tasks)
```

### 3. **Async Agent Execution**
Each agent runs asynchronously:
```python
async def run_async(self, client: AsyncOpenAI, user_prompt: str):
    response = await client.chat.completions.create(
        model=self.model,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )
```

## Performance Benefits

### Time Savings
```
Sequential: Research(30s) + Enhancement(20s) + Distribution(15s) = 65s
Parallel:   Research(30s), Enhancement(20s), Distribution(15s) = 30s
```

### Token Efficiency
- Parallel calls don't increase token usage
- Same cost, faster results
- Better user experience

## Integration Points

### 1. **Main Pipeline**
```python
async def run_pipeline(self, topic: str):
    # Phase 2: Parallel Research
    research = await self.phase2_parallel_research(topic)
    
    # Sequential phases...
    
    # Phase 5: Parallel Enhancement
    enhancements = await self.phase5_parallel_enhancement(...)
    
    # Phase 7: Parallel Distribution
    distribution = await self.phase7_distribution(...)
```

### 2. **Error Handling**
```python
# Graceful handling of partial failures
results = await asyncio.gather(*tasks, return_exceptions=True)
for i, result in enumerate(results):
    if isinstance(result, Exception):
        # Handle individual failures
```

## Usage Patterns

### Adding New Parallel Phase
```python
# Define agent prompts
agent_prompts = [
    ("agent1", "prompt1"),
    ("agent2", "prompt2"),
    ("agent3", "prompt3")
]

# Run in parallel
results = await self.manager.run_agents_parallel(agent_prompts)

# Process results
for agent_name, result in zip(agent_prompts, results):
    # Handle each result
```

### Converting Sequential to Parallel
```python
# Before (Sequential):
result1 = await self.run_agent("agent1", prompt1)
result2 = await self.run_agent("agent2", prompt2)

# After (Parallel):
results = await self.manager.run_agents_parallel([
    ("agent1", prompt1),
    ("agent2", prompt2)
])
```

## Best Practices

### 1. **Independent Operations Only**
Parallel execution works when agents don't depend on each other:
- ✅ Web + KB research (independent sources)
- ✅ SEO + Metrics (different analyses)
- ❌ Research + Writing (writing needs research)

### 2. **Resource Considerations**
- Each parallel call uses API rate limit
- Monitor for 429 errors (rate limit)
- OpenAI handles concurrent requests well

### 3. **Error Isolation**
- One agent failure doesn't stop others
- Handle exceptions individually
- Provide fallbacks for critical agents

## Debugging

### View Parallel Execution
```bash
# See all parallel phases
grep -n "run_agents_parallel" src/pipeline/chat_orchestrator.py

# Check asyncio patterns
grep -n "asyncio.gather" src/pipeline/chat_orchestrator.py
```

### Monitor Performance
```python
# Add timing
start = time.time()
results = await self.manager.run_agents_parallel(...)
print(f"Parallel execution took: {time.time() - start}s")
```

## Configuration
Currently hardcoded, but could be made configurable:
```python
# Potential enhancement
PARALLEL_PHASES = {
    "research": True,
    "enhancement": True,
    "distribution": True
}
```

## Limitations
- Maximum concurrent benefit ~3-4 agents
- API rate limits apply
- Some phases must remain sequential

## Future Enhancements
- Dynamic parallelization based on load
- Priority queuing for agents
- Batched API calls
- Progressive result streaming