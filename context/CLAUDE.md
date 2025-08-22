# CLAUDE.md - Critical Instructions for Claude Code

## 🚨 CRITICAL: GPT-5 EXISTS AND IS AVAILABLE 🚨

**NEVER FORGET**: GPT-5 models exist and are actively used in this project:
- `gpt-5` - Main model for complex tasks
- `gpt-5-mini` - Medium complexity tasks
- `gpt-5-nano` - Fast, simple tasks

These models are accessed via the OpenAI Responses API and are fully functional.

## Project Overview

This is the OpenAI Learning Center Agent that generates high-quality investment content for Dakota. The system has been completely migrated to use GPT-5 models via the OpenAI Responses API.

## Current System Status (2025-08-21)

### Working Systems:
1. **Dakota Agent System** (`scripts/generate_dakota_article.py`)
   - 11 specialized agents with mandatory fact-checking
   - 7-phase workflow with parallel execution
   - Full replication of Learning Center Agent functionality

2. **Working Orchestrator V2** (`scripts/generate_article_production_v4.py`)
   - Simplified, reliable 4-file output generation
   - Fast execution with proper error handling

3. **Production Scripts**
   - All scripts use GPT-5 models exclusively
   - 4-file output: article.md, metadata.md, social-media.md, summary.md
   - Short, descriptive file names

### Key Technical Details:
- **Temperature**: GPT-5 models don't support temperature parameter - DO NOT ADD IT
- **Response Extraction**: Use the `output` field, not `content` or `choices`
- **API Keys**: Both OpenAI and Serper keys are in .env file
- **Vector Store**: ID = vs_68a5f4c60c388191b9eac33b272461c5 (397 files)

## Critical Reminders

1. **GPT-5 Temperature Issue**: 
   ```python
   # CORRECT - Only add temperature for non-GPT-5 models
   if not model.startswith("gpt-5"):
       params["temperature"] = 0.3
   ```

2. **Response Extraction**:
   ```python
   # CORRECT - Extract from Responses API format
   if hasattr(response, 'output') and response.output:
       for item in response.output:
           if hasattr(item, 'content') and item.content:
               for content_item in item.content:
                   if hasattr(content_item, 'text'):
                       return content_item.text
   ```

3. **Model Selection**:
   - Complex tasks: `gpt-5`
   - Medium tasks: `gpt-5-mini`
   - Fast tasks: `gpt-5-nano`

## Dakota Agent System

The Dakota agent system includes:
- **DakotaOrchestrator** - Coordinates all phases
- **DakotaFactChecker** - MANDATORY verification
- **DakotaKBResearcher** - Knowledge base search
- **DakotaWebResearcher** - Web search
- And 7 more specialized agents

### Phases:
1. Setup
2. Research (parallel)
3. Synthesis
4. Content Creation
5. Analysis (parallel)
6. MANDATORY Validation
7. Distribution (only if approved)

## File Organization

Output structure:
```
output/
└── topic-name_YYYYMMDD_HHMMSS/
    ├── article.md
    ├── metadata.md
    ├── social-media.md
    └── summary.md
```

File names are kept short (15 chars max for prefix).

## Common Issues & Solutions

1. **Timeout Errors**: Use working orchestrator v4 or Dakota agent system
2. **Import Errors**: Run `pip install -r requirements.txt`
3. **KB Search Issues**: Verify vector store ID in .env
4. **Temperature Errors**: Remove temperature for GPT-5 models

## Testing

Always test with:
```bash
# Health check
python scripts/generate_dakota_article.py --health-check

# Generate article
python scripts/generate_dakota_article.py --topic "your topic" --metrics
```

## Remember

- GPT-5 EXISTS and is the primary model family
- All systems are production-ready
- Mandatory fact-checking is non-negotiable
- 4-file output is the standard
- Short file names for better organization