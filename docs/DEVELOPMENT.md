# Dakota Learning Center - OpenAI Article Generation System Instructions

## PRIMARY DIRECTIVE
**ALWAYS use the SIMPLEST solution that works to avoid over-complexity.**

## CONTENT GENERATION ENFORCEMENT
**🚨 CRITICAL: ALL article generation MUST use the established pipeline system. The system uses PARALLEL AGENTS with Chat Completions API.**

**Correct usage:**
```bash
# Generate full article
python main_chat.py generate "Impact of ESG on returns"

# Quick 500-word brief
python main_chat.py generate "Market volatility" --quick

# Custom word count
python main_chat.py generate "Factor investing" --words 1000

# Auto-generate topic (KB-aware)
python main_chat.py generate --auto
```

**NEVER do:**
- Create articles manually without the pipeline
- Skip fact-checking and validation phases
- Generate content outside the quality control system
- Bypass the vector store for knowledge base queries
- Accept outdated data or statistics
- Publish without data freshness validation

## Required References
1. **Always read these files when starting or resuming work:**
   - `/docs/README.md` - Documentation overview
   - `/docs/ARCHITECTURE.md` - System design
   - `/docs/DEVELOPMENT.md` - This file
   - `src/config_enhanced.py` - Quality thresholds

2. **After conversation compaction:**
   - Read `/docs/POST-COMPACT-RECOVERY.md`
   - Review current todo list status
   - Check `python main_chat.py config`
   - Review relevant `/docs/features/*.md`

## Core Architecture

### 1. Agent System (Chat Completions API)
- **13 Specialized Agents**: Each with specific role and prompt (includes metadata generator)
- **Parallel Execution**: Web + KB research, SEO + Metrics, Summary + Social
- **Function Calling**: GPT's built-in search, file operations, URL verification
- **Token Tracking**: Cost transparency per agent (~$1.67 per article)
- **Model Configuration**: GPT-5 for complex tasks, GPT-4.1 for efficient operations (production models)

### 2. Quality Control
- **Minimum Standards**: 2000 words, 12 sources (configurable)
- **Fact Verification**: 80%+ credibility required
- **Data Freshness**: 100% current data enforced
  - Market data: Within 30 days
  - Allocation data: Within 90 days
  - General data: Within 180 days
- **Automatic Iteration**: Up to 3 attempts to meet quality
- **Source Scoring**: Government (10), Academic (9), Financial (8)

### 3. Vector Store Integration
- **Knowledge Base**: Dakota materials in OpenAI vector store
- **Semantic Search**: KB Researcher uses vector similarity
- **Persistent Storage**: VECTOR_STORE_ID saved in .env
- **KB-Aware Topics**: Topic generator analyzes existing content to avoid duplicates

### 4. Dakota-Specific Features
- **Focus Areas**: Real allocation data, RFP activity, fundraising applications
- **Target Investors**: RIAs, Family Offices, Pension Funds, Endowments, etc.
- **Dakota Way Integration**: "Focus on What Matters Most" principle
- **Practical Applications**: Every article includes fundraising takeaways

## Core Principles

### 1. Simplicity First
- Use Chat Completions API for speed and control
- Leverage existing agent prompts in `src/prompts/`
- Trust the parallel orchestration system
- Don't recreate what already exists

### 2. Quality Enforcement
- Every article goes through ALL phases
- No shortcuts on fact-checking
- Sources must be credible (score 6+)
- Automatic fixes for identified issues

### 3. Efficient Execution
- Parallel phases reduce time by 40%
- Async/await throughout the pipeline
- Token usage tracked for cost control
- Vector store for instant KB access

### 4. Zero Compromise
- REJECT articles below 80% credibility
- REQUIRE citations for all facts
- VERIFY all URLs are accessible
- ITERATE until quality met
- ENFORCE 100% data freshness
- VALIDATE all dates and timeframes

## Quick Reference Commands

### Setup
```bash
# First time - create vector store
python setup_vector_store.py

# Install dependencies
pip install -r requirements.txt

# Check configuration
python main_chat.py config
```

### Generation
```bash
# Standard article (2000+ words)
python main_chat.py generate "Your topic"

# Quick brief (500 words)
python main_chat.py generate "Your topic" --quick

# Custom length
python main_chat.py generate "Your topic" --words 1500

# Auto topic
python main_chat.py generate --auto

# Topic suggestions
python main_chat.py topics
```

### Testing
```bash
# Run test generation
python main_chat.py test

# Debug mode
python main_chat.py generate "Topic" --debug
```

## Pipeline Phases

1. **Initialization**: Load agents, vector store
2. **Research** (Parallel): Web + KB simultaneously
   - Web: Searches for current allocation data, RFP activity
   - KB: Analyzes Dakota Way content and existing articles
3. **Evidence Package**: Create proof pack
4. **Synthesis**: Combine research with fundraising focus
5. **Content Creation**: Write article with dated citations
6. **Enhancement** (Parallel): SEO + Metrics
7. **Validation**: Fact-check + claim-check + data freshness
   - Automated date extraction and validation
   - Rejection if missing current year data
8. **Iteration**: Fix issues if rejected (including outdated data)
9. **APPROVAL**: Article must pass all checks
10. **Distribution** (Parallel): Summary + Social (post-approval only)
    - Summary from fact-checked article
    - Social from verified content
11. **Metadata**: Generate comprehensive metrics with real data

## Decision Framework
When approaching any task:
1. **Can the existing pipeline handle it?** → Use it
2. **Is it a configuration change?** → Update config_enhanced.py
3. **Need a new agent?** → Add prompt in src/prompts/
4. **Complex new feature?** → Document why needed

## Writing Style Guidelines
- **No "I" Statements**: Never use "I" or "my" - too personal
- **Limited First Person**: Use "we/our" sparingly when referring to Dakota
- **Professional Voice**: Maintain authority and objectivity
- **Dakota CTAs**: End articles with relevant Dakota Marketplace or Research CTAs
- **Social Emojis**: Use 1-3 strategic emojis per social post

## Anti-Patterns to Avoid
- Creating articles without the pipeline
- Skipping fact verification
- Using Assistants API (slower) when Chat Completions works
- Adding complexity for hypothetical needs
- Ignoring token usage and costs
- Using first person "I" statements in content

## Key Files Reference
- **Pipeline**: `src/pipeline/chat_orchestrator.py`
- **Agents**: `src/agents/chat_agent.py`
- **Config**: `src/config_enhanced.py`
- **Fact Check**: `src/tools/fact_verification.py`
- **Data Freshness**: `src/tools/data_freshness_validator.py`
- **Topic Generator**: `src/utils/topic_generator.py`
- **Vector Store**: `src/tools/vector_store_handler.py`
- **Main Entry**: `main_chat.py`

## Remember
- The system already handles complex orchestration
- Quality control is automatic and mandatory
- Parallel execution is built-in
- Vector store provides instant KB access
- Every article includes fact-check report
- Token usage is tracked for cost control

## Current Capabilities
- ✅ Configurable word counts (500-5000+)
- ✅ Auto topic generation (KB-aware)
- ✅ Vector store KB search
- ✅ Parallel agent execution
- ✅ Automatic quality iteration
- ✅ Comprehensive fact-checking
- ✅ Distribution asset creation (post-approval)
- ✅ Token/cost tracking
- ✅ 100% data freshness validation
- ✅ Dakota-specific content focus
- ✅ Real allocation data integration
- ✅ GPT's built-in web search
- ✅ Fundraising application insights
- ✅ Comprehensive metadata generation
- ✅ Knowledge base update tools
- ✅ No mock data enforcement
- ✅ Post-approval accuracy guarantee