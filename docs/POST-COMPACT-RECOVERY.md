# Post-Compaction Recovery Checklist

## Immediate Actions
1. **Read Core Documentation**
   ```bash
   # Read in this order:
   Read /docs/ARCHITECTURE.md          # System overview
   Read /docs/DEVELOPMENT.md           # Development guidelines
   Read /docs/POST-COMPACT-RECOVERY.md # This file
   ```

2. **Check System Status**
   ```bash
   # Verify configuration
   python main_chat.py config
   
   # Check if vector store exists
   cat .env | grep VECTOR_STORE_ID
   
   # Run test generation
   python main_chat.py test
   ```

3. **Review Current Work**
   - Check todo list for in-progress tasks
   - Look for recent changes in git
   - Review any WIP feature docs

## Common Context Loss Areas

### 1. **Pipeline Flow**
Remember the system has 9 phases:
- Phase 2: Parallel Research (Web + KB)
- Phase 2.5: Evidence Package
- Phase 3: Synthesis
- Phase 4: Content Creation
- Phase 5: Parallel Enhancement (SEO + Metrics)
- Phase 6: Validation (Fact + Claim check + Data Freshness)
- Phase 6.5: Iteration (if needed)
- Phase 7: Distribution (Summary + Social)

### 2. **Quality Requirements**
- 80% minimum credibility score
- 90% fact accuracy rate
- All facts must have citations
- Sources must score 6+ credibility
- Automatic iteration up to 3 times
- 100% data freshness enforcement
- Must have current year (2025) data

### 3. **Key Commands Often Forgotten**
```bash
# Generate with auto topic (KB-aware)
python main_chat.py generate --auto

# Quick 500-word brief
python main_chat.py generate "topic" --quick

# Custom word count
python main_chat.py generate "topic" --words 1000

# Get topic suggestions
python main_chat.py topics
```

### 4. **Architecture Reminders**
- Using Chat Completions API (NOT Assistants)
- Agents defined by .md prompts in src/prompts/
- Parallel execution via asyncio.gather()
- Vector store for KB search
- Token tracking per agent (~$1.67 per article)
- GPT-5 for complex tasks, GPT-4.1 for efficient ops (production models)
- GPT's built-in web search (no web_search tool)
- Data freshness validation integrated
- No "I" statements, limited "we/our"
- Dakota CTAs at article end

## Feature Documentation
Check these based on what you were working on:
- `/docs/features/fact-checking.md` - Fact verification system
- `/docs/features/vector-store.md` - Knowledge base integration
- `/docs/features/parallel-execution.md` - Async orchestration
- `/docs/features/auto-topics.md` - Topic generation
- `/docs/features/quality-iteration.md` - Automatic fixes
- `/docs/DATA_FRESHNESS_GUARANTEE.md` - Data freshness system
- `/docs/METADATA_SPECIFICATION.md` - Metadata structure and extraction
- `/docs/PIPELINE_ACCURACY_FLOW.md` - Post-approval distribution
- `/docs/UPDATING_KNOWLEDGE_BASE.md` - KB update procedures
- `/docs/ADDING_LEARNING_CENTER_ARTICLES.md` - Article addition guide
- `/src/tools/data_freshness_validator.py` - Freshness validation
- `/src/utils/topic_generator.py` - KB-aware topic generation
- `/src/prompts/dakota-metadata-generator.md` - Metadata prompt

## Quick Diagnostic Commands
```bash
# List all agents
ls src/prompts/dakota-*.md

# Check pipeline phases
grep -n "async def phase" src/pipeline/chat_orchestrator.py

# View fact-checking logic
grep -A5 "verify_article" src/tools/fact_verification.py

# See parallel execution
grep -B2 -A2 "gather" src/pipeline/chat_orchestrator.py
```

## Common Issues After Compaction

1. **"How does fact-checking work?"**
   - Read `/docs/features/fact-checking.md`
   - Check `src/tools/fact_verification.py`

2. **"What's the difference from Assistants API?"**
   - We use Chat Completions for speed
   - Only vector store uses Assistants temporarily

3. **"How to add new features?"**
   - Follow existing patterns
   - Document in `/docs/features/`
   - Keep it simple

4. **"Where are the agents defined?"**
   - Prompts in `src/prompts/dakota-*.md`
   - Logic in `src/pipeline/chat_orchestrator.py`

## Recent Enhancements

### 1. **Data Freshness Validation**
- Automated date extraction and validation
- Multi-layer enforcement (research → writing → validation)
- Rejects articles without current year data
- Specific freshness rules by data type

### 2. **Dakota-Specific Features**
- Focus on real allocation data
- RFP and search activity tracking
- Target investor types (RIAs, Family Offices, etc.)
- Fundraising application insights
- Dakota Way integration

### 3. **KB-Aware Topic Generation**
- Analyzes existing content to avoid duplicates
- Identifies content gaps
- Aligns with Dakota's focus areas

### 4. **GPT's Built-in Search**
- Web researcher uses GPT's native search
- No separate web_search tool needed
- Automatic current data searches

### 5. **Comprehensive Metadata**
- Real data extraction (no mock values)
- SEO optimization data
- Cost tracking and analytics
- Content relationship mapping
- Generation metrics

### 6. **Post-Approval Distribution**
- Summary/social only after fact-checking
- Uses verified content only
- Cannot introduce new claims
- 100% accuracy maintained

### 7. **Knowledge Base Tools**
- `update_knowledge_base.py` for adding content
- Incremental updates without recreation
- Support for individual files or directories

### 8. **Writing & Cost Updates**
- No "I" or "my" in content
- Use "we/our" sparingly
- Dakota CTAs at article end
- Strategic emojis in social media
- GPT-5 and GPT-4.1 in production
- ~$1.67 per standard article

### 9. **Output Structure Updates**
- Files save to: `output/Learning Center Articles/YYYY-MM-DD-[topic]/`
- Simplified to 4 files: article.md, metadata.md, summary.md, social.md
- All outputs in markdown format
- Short topic-based filenames
- Consolidated metadata includes SEO, quality, sources, and costs

### 10. **Knowledge Base Status**
- 407 files loaded in vector store
- 397 Learning Center articles
- 9 Dakota Way chapters
- Fully operational for semantic search

## Remember
- The system is already sophisticated
- Don't rebuild what exists
- Check feature docs before implementing
- Simplicity over complexity
- Quality is non-negotiable
- Data must be 100% current
- Focus on fundraising applications