# API Integration Guide

This guide explains how to integrate real APIs for production use.

## Current Status

The Dakota Learning Center system is configured to use GPT-5 and GPT-4.1 models with built-in capabilities. Most functionality is handled natively by these models.

**Important**: The system uses the OpenAI Responses API (Chat Completions endpoint), NOT the deprecated Assistants API. All agent interactions use the `/v1/chat/completions` endpoint.

## Web Search

### Built-in GPT Search (Recommended)
The system is configured to use GPT's native web search capabilities:
- **Web Researcher Agent** uses GPT's built-in search
- No additional API keys required
- Automatically searches when instructed in prompts

### External Search APIs (Optional)
If you need external search for other agents:

#### Google Custom Search
```python
# In .env
GOOGLE_API_KEY=your_api_key
GOOGLE_CSE_ID=your_custom_search_engine_id

# In chat_orchestrator.py
async def _handle_web_search(self, query: str, num_results: int = 10):
    import aiohttp
    
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": os.getenv("GOOGLE_API_KEY"),
        "cx": os.getenv("GOOGLE_CSE_ID"),
        "q": query,
        "num": num_results
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            data = await response.json()
            
    return {
        "query": query,
        "results": [
            {
                "title": item["title"],
                "url": item["link"],
                "snippet": item["snippet"],
                "source": item["displayLink"]
            }
            for item in data.get("items", [])
        ]
    }
```

#### Bing Search API
```python
# In .env
BING_SEARCH_KEY=your_subscription_key

# Implementation similar to Google
```

## URL Verification

The system already includes real URL verification using aiohttp:
```python
async def _handle_verify_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
    # Real HTTP HEAD requests with timeout
    # Returns actual status codes
```

## Vector Store

The system uses OpenAI's vector store for knowledge base:
- Created by `setup_vector_store.py`
- Stores Dakota's proprietary content
- Used by KB Researcher agent

## File Operations

Real file operations are already implemented:
- `write_file` - Writes to filesystem
- `read_file` - Reads from filesystem
- `validate_article` - Real validation logic

## Authentication

All API keys should be stored in `.env`:
```bash
# Required
OPENAI_API_KEY=sk-...

# Optional (if using external search)
GOOGLE_API_KEY=...
GOOGLE_CSE_ID=...
BING_SEARCH_KEY=...
SERP_API_KEY=...
```

## Best Practices

1. **Use Built-in Capabilities**: GPT-5 and GPT-4.1 have many built-in features
2. **Async Operations**: All API calls should be async for performance
3. **Error Handling**: Always include timeout and error handling
4. **Rate Limiting**: Implement rate limiting for external APIs
5. **Caching**: Consider caching search results to reduce API calls

## Testing APIs

To test if APIs are working:
```bash
# Test article generation
python main_chat.py test

# Generate with real search
python main_chat.py generate "Current market trends" --debug
```

## Monitoring

Track API usage in quality reports:
- Token usage per agent
- API call counts
- Error rates
- Response times

## Cost Optimization

1. Use GPT's built-in search when possible (no extra cost)
2. Cache frequent searches
3. Use appropriate models for each task
4. Monitor token usage in reports