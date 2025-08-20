# Dakota Learning Center Article Generation System - Architecture

## Project Overview
This is an AI-powered article generation system for Dakota's Learning Center that creates high-quality investment education content with zero compromise on accuracy. It uses OpenAI's Chat Completions API with a sophisticated multi-agent architecture. Dakota has raised $40+ billion since 2006 and serves 6,000+ fundraisers across 1,400+ investment firms.

## Core Mission
Generate institutional-quality investment articles that:
- Meet Dakota's educational standards with 100% current data
- Contain verified facts with credible, dated sources
- Provide actionable insights for fundraisers and allocators
- Focus on "What Matters Most" for investment sales professionals
- Include real allocation data and RFP activity

## System Architecture

### 1. **Technology Stack**
- **API**: OpenAI Responses API (Chat Completions) - NOT the deprecated Assistants API
- **Models**: GPT-5 and GPT-4.1 (released models in production)
- **Language**: Python 3.8+ with asyncio
- **Vector Store**: OpenAI vector store (ID: vs_68980892144c8191a36a383ff1d5dc15)
- **Knowledge Base**: 397 files (395 Learning Center + 2 Dakota Way)
- **Execution**: Parallel agent orchestration
- **Data Validation**: Real-time freshness checking
- **Metadata**: Comprehensive tracking with real data extraction
- **Cost**: ~$1.67 per standard article

### 2. **Agent System (13 Specialized Agents)**
```
Research Phase (Parallel):
├── Web Researcher - Searches for current allocation data, RFP activity
└── KB Researcher - Searches Dakota Way content and knowledge base

Synthesis Phase:
└── Research Synthesizer - Combines findings with fundraising focus

Content Phase:
├── Content Writer - Creates article with dated citations
└── Evidence Packager - Creates verification proof pack

Enhancement Phase (Parallel):
├── SEO Specialist - Metadata and keywords
└── Metrics Analyzer - Quality metrics and data freshness

Validation Phase:
├── Fact Checker - Verifies facts, sources, and data currency
├── Claim Checker - Validates accuracy and dates
└── Iteration Manager - Fixes issues including outdated data

Distribution Phase (Parallel) - After Approval Only:
├── Summary Writer - Executive summary from fact-checked article
└── Social Promoter - Social media content from verified facts

Metadata Phase:
└── Metadata Generator - Comprehensive metrics and SEO data
```

### 3. **Quality Standards**
- **Minimum Credibility**: 80% overall score
- **Fact Accuracy**: 90% verified facts
- **Data Freshness**: 100% current data required
  - Market data: Within 30 days
  - Allocation data: Within 90 days
  - General data: Within 180 days
- **Word Count**: Configurable (default 2000+)
- **Sources**: Configurable (default 12+)
- **Dakota References**: Minimum 2 internal links
- **Max Iterations**: 3 attempts to meet quality

### 4. **Source Credibility Hierarchy**
```
10/10: Government (.gov), Central banks, SEC, Federal Reserve
9/10:  Academic journals, NBER, JSTOR
8/10:  Bloomberg, Reuters, WSJ, FT, Morningstar
7/10:  Industry organizations (CFA Institute)
6/10:  CNBC, MarketWatch, established media
3-4/10: Blogs, Medium, SeekingAlpha
2/10:  Forums, Reddit, social media (avoided)
```

### 5. **Target Audience (Dakota's Database)**
- RIAs (Registered Investment Advisors)
- Family Offices & Multi-Family Offices
- Public & Corporate Pension Funds
- Endowments & Foundations
- OCIOs & Institutional Consultants
- Insurance Companies
- Fund of Funds
- Healthcare Systems
- Bank Trusts & Broker Dealers

## Key Features

### 1. **Configurable Generation**
- `--quick`: 500-word briefs
- `--words N`: Custom word count
- `--auto`: AI-generated topics with KB awareness
- `--no-kb`: Skip knowledge base

### 2. **Parallel Execution**
- Research: Web + KB simultaneously
- Enhancement: SEO + Metrics together
- Distribution: Summary + Social in parallel (after approval)
- ~40% faster than sequential

### 3. **Data Freshness Validation**
- Automated date extraction and parsing
- Contextual freshness rules by data type
- Real-time validation during fact-checking
- Rejection of outdated information
- Specific recommendations for updates

### 4. **Dakota-Specific Features**
- Focus on allocation data and investor activity
- Integration with Dakota Way principles
- Fundraising application insights
- RFP and search tracking
- Fee and terms intelligence

### 5. **Output Package**
```
output/Learning Center Articles/[YYYY-MM-DD]-[topic-slug]/
├── [topic-slug].md          # Main article with dated citations
├── metadata.md              # Consolidated metrics, SEO, sources, quality scores
├── summary.md               # Executive summary (post-approval)
└── social.md                # Social media content (post-approval)
```

## Data Freshness System

### Multi-Layer Validation
1. **Research Phase**: Web researcher mandates current data
2. **Writing Phase**: Content writer timestamps all data
3. **Validation Phase**: Fact checker verifies all dates
4. **Final Check**: Rejects if missing current year data

### Automated Tools
- `DataFreshnessValidator`: Extracts and analyzes all dates
- `EnhancedFactChecker`: Integrates freshness validation
- Configuration controls for maximum data age
- Detailed freshness reports with recommendations

## Current State & Capabilities

### ✅ Implemented
- Full Chat Completions API pipeline
- Vector store with Dakota Way content
- Parallel agent execution
- Comprehensive fact-checking with dates
- Data freshness validation system
- Automatic quality iteration
- Token/cost tracking
- KB-aware topic generation
- Real URL verification
- Dakota-specific enhancements
- Comprehensive metadata generation
- Post-approval distribution flow

### 🎯 Optimized For
- Fundraising professionals
- Current market intelligence
- Allocation tracking
- RFP activity monitoring
- Investor preference insights

## Quick Start Commands
```bash
# First time setup
python setup_vector_store.py

# Generate article
python main_chat.py generate "Your topic"

# Quick brief
python main_chat.py generate "Topic" --quick

# Auto topic with KB awareness
python main_chat.py generate --auto

# Get topic suggestions
python main_chat.py topics

# Check config
python main_chat.py config

# Test generation
python main_chat.py test
```

## Project Structure
```
/
├── src/
│   ├── agents/          # Agent implementations
│   ├── pipeline/        # Orchestrators
│   ├── prompts/         # Agent instructions (.md)
│   ├── tools/           # Fact verification, freshness validation
│   ├── utils/           # Topic generator, helpers
│   └── config_enhanced.py
├── knowledge_base/      # Dakota Way & Learning Center content
│   ├── dakota_way/      # The Dakota Way chapters
│   └── learning_center/ # 397 educational articles
├── docs/                # Documentation
├── main_chat.py        # Entry point
└── setup_vector_store.py
```

## Critical Files
- **Pipeline Logic**: `src/pipeline/chat_orchestrator.py`
- **Configuration**: `src/config_enhanced.py`
- **Fact Checking**: `src/tools/fact_verification.py`
- **Data Freshness**: `src/tools/data_freshness_validator.py`
- **Topic Generator**: `src/utils/topic_generator.py`
- **Entry Point**: `main_chat.py`
- **Metadata Generator**: `src/prompts/dakota-metadata-generator.md`
- **Knowledge Base Updates**: `update_knowledge_base.py`

## Recovery Checklist
If returning after break:
1. Read this document
2. Check `python main_chat.py config`
3. Review `/docs/POST-COMPACT-RECOVERY.md`
4. Check current todo list
5. Run `python main_chat.py test`

## Design Philosophy
- **Focus on What Matters Most**: Dakota's core principle
- **Current Data Only**: 100% up-to-date information
- **Fundraising Focus**: Practical applications for sales
- **Quality Without Compromise**: Automated verification
- **Efficiency**: Parallel execution where possible
- **Transparency**: Track all sources, dates, and costs

## Writing Guidelines
- **No "I" Statements**: Never use "I" or "my" - too personal
- **Limited First Person**: Use "we/our" sparingly when necessary
- **Professional Voice**: Maintain Dakota's authority
- **Dakota CTAs**: End articles with appropriate Dakota Marketplace or Research CTAs

## Recent Enhancements
- Dakota-specific content requirements
- Real-time data freshness validation
- KB-aware topic generation
- Enhanced prompts for allocation data
- Automated date extraction and verification
- Fundraising application focus
- Comprehensive metadata generation with real data
- Post-approval distribution flow for accuracy
- Knowledge base update tooling
- No mock data enforcement
- Strategic emoji usage in social media
- Dakota CTA integration in articles
- GPT-5 and GPT-4.1 models in production
- Simplified output structure with date-prefixed folders
- All outputs in markdown format
- Consolidated files (4 instead of 8)
- Short topic-based filenames
- 397 files loaded in knowledge base (395 Learning Center + 2 Dakota Way)
- Vector store ID: vs_68980892144c8191a36a383ff1d5dc15
- File naming: all underscores, no hyphens
- Programmatic upload more reliable than web interface

## Pipeline Accuracy Flow
1. **Research → Writing → Enhancement** (can have errors)
2. **Fact-Checking & Validation** (catches all issues)
3. **Iteration if needed** (fixes problems)
4. **APPROVAL** (only if 100% accurate)
5. **Distribution** (summary/social from approved content)
6. **Metadata** (real metrics from final article)

This ensures summary and social content are as accurate as the main article.

Last Updated: 2025-01-09