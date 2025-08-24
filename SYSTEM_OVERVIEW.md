# Learning Center Agent System Overview

## System Architecture

This is a multi-agent system for generating high-quality articles for Dakota's Learning Center. The system uses OpenAI's GPT-5 models via the Responses API and integrates with Dakota's Knowledge Base for fact-checking and source verification.

## Core Components

### 1. Multi-Agent System (`src/agents/`)
- **Orchestrator Agent**: Coordinates all other agents and manages the article generation pipeline
- **Research Agents**: Gather information from Dakota's Knowledge Base
- **Writing Agents**: Create article content with proper structure and style
- **Quality Agents**: Ensure article quality through fact-checking and editing

### 2. Dakota Integration (`src/services/`)
- **Knowledge Base Search**: Production-ready KB search using Responses API with vector store (397 Dakota files)
- **Fact Checker v2**: Enhanced fact-checking with true source verification
  - Located in `src/services/fact_checker_v2.py`
  - Actually fetches and verifies source content
  - Validates claims against real Dakota documentation
  - Returns structured verification results with confidence scores

### 3. Pipeline Components (`src/pipeline/`)
- **Dakota Orchestrator**: Production-ready orchestrator with Dakota-specific features
- **Multi-Agent Orchestrator**: Coordinates agent interactions
- **Production Orchestrator**: Enterprise-grade reliability features

## Recent Updates (2025-08-22)

### Enhanced Fact Checker v2
- **True Source Verification**: Now fetches actual content from Dakota KB sources
- **Improved Validation**: Verifies claims against real documentation
- **Structured Results**: Returns detailed verification with confidence scores
- **GPT-5 Integration**: Uses Responses API for intelligent fact-checking

### Key Fixes Implemented
1. **Response Extraction**: Fixed GPT-5 Responses API text extraction
   - Properly handles `response.output_text` structure
   - Graceful fallback for different response formats

2. **KB Search Integration**: Returns structured data with proper metadata
   - Fixed to return dictionaries instead of raw strings
   - Includes source files, relevance scores, and content

3. **Dakota Orchestrator Integration**: Successfully integrated fact_checker_v2
   - Replaces old mock fact-checker
   - Provides real-time source verification

### Current Status
- **Fact-Checking**: ✅ Working with true source verification
- **KB Search**: ✅ Fixed and returning structured data
- **GPT-5 Integration**: ✅ Using Responses API correctly
- **Known Issue**: Articles failing due to missing Key Takeaways/Conclusion sections
  - This is NOT a fact-checking issue
  - Related to article structure validation

## API Configuration

### GPT-5 Models (via Responses API)
- `gpt-5`: Complex reasoning and code-heavy tasks
- `gpt-5-mini`: Balanced speed and capability
- `gpt-5-nano`: High-throughput for simple tasks

### API Usage Pattern
```python
from openai import OpenAI
client = OpenAI()

response = client.responses.create(
    model="gpt-5",
    input="Your prompt here",
    reasoning={"effort": "medium"},
    text={"verbosity": "medium"}
)

# Extract text
text = response.output_text
```

## Production Features

### Reliability
- Circuit Breaker Pattern
- Rate Limiting
- Caching Layer
- Health Checks
- Graceful Degradation

### Monitoring
- Metrics Collection
- Performance Tracking
- Error Logging
- Agent Effectiveness Monitoring

## File Structure
```
/src/
├── agents/          # Multi-agent components
├── services/        # Dakota integrations (KB search, fact-checking)
├── pipeline/        # Orchestration and coordination
├── utils/           # Utilities (circuit breaker, rate limiter)
└── config.py        # Configuration settings

/scripts/
├── generate_article.py              # Basic article generation
├── generate_dakota_article.py       # Dakota-specific generation
└── generate_article_production.py   # Production deployment
```

## Dakota-Specific Features
- Custom prompts for Dakota's voice and style
- Integration with Dakota Knowledge Base (397 files)
- Fact-checking against official Dakota documentation
- Metadata generation for Learning Center
- SEO optimization for Dakota's audience