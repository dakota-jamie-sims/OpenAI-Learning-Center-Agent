# CRITICAL INSTRUCTIONS FOR CLAUDE

## GPT-5 MODELS EXIST AND ARE AVAILABLE

**IMPORTANT**: GPT-5 models are real and available through OpenAI's Responses API. Never suggest they don't exist.

### Available GPT-5 Models:
- `gpt-5` - Full model for complex reasoning and code-heavy tasks
- `gpt-5-mini` - Cost-optimized model balancing speed and capability  
- `gpt-5-nano` - High-throughput model for simple tasks

### Key Facts:
1. GPT-5 models are accessed through the **Responses API** (not Chat Completions API)
2. Documentation is located at: `/docs/openai_documentation/05_Core concepts/05_Using GPT-5`
3. The Responses API uses `client.responses.create()` not `client.chat.completions.create()`
4. GPT-5 supports reasoning effort levels: minimal, low, medium, high
5. GPT-5 supports verbosity control: low, medium, high

### Example Usage:
```python
from openai import OpenAI
client = OpenAI()

response = client.responses.create(
    model="gpt-5",
    input="Your prompt here",
    reasoning={"effort": "medium"},
    text={"verbosity": "medium"}
)

# Extract text from response.output_text or response.output[0].content[0].text
```

### When Working on This Project:
- The multi-agent system is configured to use GPT-5 models
- All agents should use the Responses API when model starts with "gpt-5"
- For fallback or when Responses API isn't available, use "gpt-4o" or "gpt-4.1"

**NEVER** suggest that GPT-5 doesn't exist or isn't available. It is a real model family accessible through the OpenAI Responses API.

## PROJECT STRUCTURE RULES

### File Organization - CRITICAL

**NEVER** save files to the root directory. Always use the proper folder structure:

- **Test files**: Save to `tests/` or `tests/integration/` or `tests/unit/`
- **Scripts**: Save to `scripts/` or appropriate subdirectory
- **Source code**: Save to `src/` and appropriate subdirectories
- **Documentation**: Save to `docs/`
- **Configuration**: Root level is OK for `.env`, `requirements.txt`, etc.

### Before Creating Any File:

1. **Check the directory structure** first
2. **Create directories if needed** before saving files
3. **Follow existing patterns** in the codebase

### Examples:
```bash
# WRONG ❌
test_something.py  # In root

# CORRECT ✅
tests/test_something.py
tests/integration/test_something.py
scripts/test_something.py
```

**IMPORTANT**: Always save test files to the `tests/` directory or its subdirectories. Never save test files to the root directory.

## SYSTEM UPDATES - 2025-08-21

### Production KB Search
- **IMPLEMENTED**: Real knowledge base search using Responses API
- Located in `/src/services/kb_search_responses.py`
- Uses `file_search` tool with vector store ID
- NO MORE MOCKS - this is production ready
- Vector store contains 397 Dakota Knowledge Base files

### GPT-5 System-Wide Integration
- **COMPLETED**: All components now use GPT-5 models
- Responses API is used throughout the system
- Model selection in `DEFAULT_MODELS` (config.py):
  - Complex tasks: `gpt-5`
  - Medium tasks: `gpt-5-mini`
  - Simple/fast tasks: `gpt-5-nano`

### API Details
- Verbosity values: "low", "medium", "high" (NOT "concise" or "verbose")
- Reasoning efforts: "minimal", "low", "medium", "high"
- All agents use `query_llm()` → `ResponsesClient` → Responses API
- KB search typically takes 10-15 seconds

### Cost Estimates
- Article generation: $0.50-$1.50 per article
- KB search: Minimal cost (uses gpt-5-nano)
- All operations use GPT-5 variants for consistency

## PRODUCTION-READY MULTI-AGENT SYSTEM - 2025-08-21

### System Enhancements
The multi-agent system has been made production-ready with enterprise-grade reliability:

#### Core Improvements
- **Circuit Breaker Pattern**: Prevents cascading failures with automatic recovery
- **Rate Limiting**: Controls API request rates to prevent throttling
- **Caching**: Reduces redundant API calls and improves performance
- **Metrics Collection**: Tracks system performance and agent effectiveness
- **Health Checks**: Monitors system status and agent availability
- **Graceful Degradation**: Fallback mechanisms for failed operations

#### Key Components Added
- `src/config_production.py` - Production configuration with optimized settings
- `src/agents/production_agent_base.py` - Enhanced base agent with reliability features
- `src/pipeline/production_orchestrator.py` - Production-ready orchestrator
- `src/utils/circuit_breaker.py` - Circuit breaker implementation
- `src/utils/rate_limiter.py` - Rate limiting functionality
- `scripts/generate_article_production.py` - Production deployment script

#### Timeout Optimization
- Fixed timeout issues by optimizing prompts
- Strategic use of GPT-5 model variants:
  - `gpt-5-nano` for quick operations (< 5s)
  - `gpt-5-mini` for medium tasks (< 15s)
  - `gpt-5` for complex reasoning (< 30s)
- Implemented retry logic with exponential backoff

#### Production Features
- **ProductionAgent Base Class**: All agents inherit production capabilities
- **ProductionOrchestrator**: Manages agent lifecycle and coordination
- **Error Recovery**: Automatic retry with fallback strategies
- **Resource Management**: Memory and connection pooling
- **Logging & Monitoring**: Comprehensive tracking of all operations

### Usage
```bash
# Production deployment
python scripts/generate_article_production.py "Your topic here"
```

The system now handles failures gracefully with fallback mechanisms and provides enterprise-grade reliability for production use.