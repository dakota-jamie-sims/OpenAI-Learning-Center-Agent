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
- Phase 6: Validation (Fact + Claim check)
- Phase 6.5: Iteration (if needed)
- Phase 7: Distribution (Summary + Social)

### 2. **Quality Requirements**
- 80% minimum credibility score
- 90% fact accuracy rate
- All facts must have citations
- Sources must score 6+ credibility
- Automatic iteration up to 3 times

### 3. **Key Commands Often Forgotten**
```bash
# Generate with auto topic
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
- Token tracking per agent

## Feature Documentation
Check these based on what you were working on:
- `/docs/features/fact-checking.md` - Fact verification system
- `/docs/features/vector-store.md` - Knowledge base integration
- `/docs/features/parallel-execution.md` - Async orchestration
- `/docs/features/auto-topics.md` - Topic generation
- `/docs/features/quality-iteration.md` - Automatic fixes

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

## Remember
- The system is already sophisticated
- Don't rebuild what exists
- Check feature docs before implementing
- Simplicity over complexity
- Quality is non-negotiable