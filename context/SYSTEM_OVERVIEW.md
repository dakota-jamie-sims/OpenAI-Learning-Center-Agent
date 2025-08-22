# OpenAI Learning Center Agent - System Overview

## Project Status (2025-08-21)

This system generates high-quality investment content for Dakota's Learning Center using multiple approaches:

1. **Working Multi-Agent Orchestrator V2** - Simplified system that works reliably
2. **Dakota Agent System** - Full replication of the Learning Center Agent architecture
3. **Production Scripts** - Multiple versions for different use cases

## Key Achievements

### 1. Fixed Multi-Agent System Issues
- **Temperature Parameter Fix**: GPT-5 models don't support temperature, now conditionally added only for non-GPT-5 models
- **Response Extraction**: Fixed text extraction from OpenAI Responses API format
- **Simplified Architecture**: Removed complex async message brokers in favor of direct orchestration
- **Timeout Prevention**: Streamlined communication to prevent cascading timeouts

### 2. 4-File Output Generation
All systems now generate 4 separate files in a dedicated subfolder:
- `article.md` - Main article with proper formatting
- `metadata.md` - SEO and performance metrics
- `social-media.md` - Multi-platform social content
- `summary.md` - Executive summary

### 3. Dakota Agent System (NEW)
Complete replication of the Learning Center Agent functionality with 11 specialized agents:

#### Agents
- **DakotaOrchestrator** - Coordinates all phases with mandatory validation
- **DakotaKBResearcher** - Searches Dakota knowledge base
- **DakotaWebResearcher** - Gathers current market intelligence
- **DakotaResearchSynthesizer** - Combines research into strategy
- **DakotaContentWriter** - Creates high-quality articles
- **DakotaMetricsAnalyzer** - Analyzes objective quality metrics
- **DakotaSEOSpecialist** - Creates metadata with verified sources
- **DakotaFactChecker** - MANDATORY verification of all data
- **DakotaIterationManager** - Fixes issues found by fact checker
- **DakotaSocialPromoter** - Creates multi-platform social content
- **DakotaSummaryWriter** - Creates executive summaries

#### 7-Phase Workflow
1. **Setup** - Topic analysis and directory creation
2. **Research (parallel)** - KB and web research run simultaneously
3. **Synthesis** - Combine research into outline
4. **Content Creation** - Write article
5. **Analysis (parallel)** - Metrics and SEO run simultaneously
6. **MANDATORY Validation** - Template check + fact checking
7. **Distribution** - Social and summary (only if approved)

## Available Scripts

### Production Scripts
1. `generate_article_production_v3.py` - Single file output (working)
2. `generate_article_production_v4.py` - 4-file output using working orchestrator
3. `generate_dakota_article.py` - Full Dakota agent system with mandatory verification

### Test Scripts
- `test_working_orchestrator.py` - Test the simplified system
- `test_simple_llm.py` - Debug individual components
- `test_multi_agent_system.py` - Original test script

## API Configuration

### Required Environment Variables (.env)
```
OPENAI_API_KEY=your_key_here
SERPER_API_KEY=your_key_here
VECTOR_STORE_ID=vs_68a5f4c60c388191b9eac33b272461c5
```

### Model Configuration
All systems use GPT-5 models exclusively:
- Default: `gpt-5`
- Researchers/Analyzers: `gpt-5-mini`
- Fast operations: `gpt-5-nano`

## Key Features

### Verification & Quality Control
- Mandatory fact-checking (no exceptions)
- Template validation before fact-checking
- URL testing and verification
- Minimum 10 sources required
- Automatic iteration for rejected articles (max 2 attempts)
- Related article URL validation

### Performance Optimizations
- Parallel execution for research and analysis phases
- Simplified communication architecture
- Direct agent orchestration (no message brokers)
- Proper error handling and timeouts
- Caching for expensive operations

### Output Quality
- 4 separate files matching Dakota templates
- SEO-optimized metadata
- Multi-platform social content
- Executive summaries
- Proper citations and source attribution

## Usage Examples

### Dakota Agent System (Recommended for Full Verification)
```bash
# Health check
python scripts/generate_dakota_article.py --health-check

# Generate article with full verification
python scripts/generate_dakota_article.py --topic "private equity trends 2025" --word-count 1750 --metrics
```

### Working Orchestrator V2 (Fast & Reliable)
```bash
# Generate with 4-file output
python scripts/generate_article_production_v4.py --topic "ESG investing strategies" --word-count 1500 --metrics
```

## Recent Updates (2025-08-21)

1. **Created Dakota Agent System** - Full replication of Learning Center Agent with 11 specialized agents
2. **Fixed Temperature Issues** - All agents now properly handle GPT-5 model parameters
3. **Implemented Phase Tracking** - Clear announcements for each phase completion
4. **Added Mandatory Fact-Checking** - No article proceeds without fact-checker approval
5. **Created Iteration Manager** - Automatically fixes issues found by fact-checker

## Known Working Configuration

- Python 3.11+
- OpenAI API with GPT-5 access
- Serper API for web search
- Dakota vector store (397 files)
- All dependencies in requirements.txt

## Troubleshooting

Common issues and solutions:

1. **Timeout errors**: Use the working orchestrator (v4) or Dakota agent system
2. **Temperature errors**: Fixed - GPT-5 models don't use temperature parameter
3. **Import errors**: Ensure all dependencies installed with `pip install -r requirements.txt`
4. **KB search failures**: Verify vector store ID in .env file

## Next Steps

The system is now production-ready with multiple options:
- Use Dakota agent system for maximum verification and quality control
- Use working orchestrator v4 for fast, reliable generation with 4-file output
- All systems use GPT-5 models exclusively with proper parameter handling