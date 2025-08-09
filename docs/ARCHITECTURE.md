# Dakota Learning Center Article Generation System - Main Context

## Project Overview
This is an AI-powered article generation system for Dakota's Learning Center that creates high-quality investment education content with zero compromise on accuracy. It uses OpenAI's Chat Completions API with a sophisticated multi-agent architecture.

## Core Mission
Generate institutional-quality investment articles that:
- Meet Dakota's educational standards
- Contain 100% verified facts with credible sources
- Provide actionable insights for institutional investors
- Maintain consistency with Dakota's investment philosophy

## System Architecture

### 1. **Technology Stack**
- **API**: OpenAI Chat Completions (NOT Assistants API)
- **Language**: Python 3.8+ with asyncio
- **Vector Store**: OpenAI vector store for knowledge base
- **Execution**: Parallel agent orchestration

### 2. **Agent System (12 Specialized Agents)**
```
Research Phase (Parallel):
├── Web Researcher - Searches credible web sources
└── KB Researcher - Searches Dakota knowledge base via vector store

Synthesis Phase:
└── Research Synthesizer - Combines findings

Content Phase:
├── Content Writer - Creates article with citations
└── Evidence Packager - Creates proof pack

Enhancement Phase (Parallel):
├── SEO Specialist - Metadata and keywords
└── Metrics Analyzer - Quality metrics

Validation Phase:
├── Fact Checker - Verifies all facts and sources
├── Claim Checker - Validates accuracy
└── Iteration Manager - Fixes issues

Distribution Phase (Parallel):
├── Summary Writer - Executive summary
└── Social Promoter - Social media content
```

### 3. **Quality Standards**
- **Minimum Credibility**: 80% overall score
- **Fact Accuracy**: 90% verified facts
- **Word Count**: Configurable (default 2000+)
- **Sources**: Configurable (default 12+)
- **Max Iterations**: 3 attempts to meet quality

### 4. **Source Credibility Hierarchy**
```
10/10: Government (.gov), Central banks, IMF, World Bank
9/10:  Academic journals, NBER, JSTOR
8/10:  Bloomberg, Reuters, WSJ, FT, Morningstar
7/10:  Industry organizations (CFA Institute)
6/10:  CNBC, MarketWatch
3-4/10: Blogs, Medium, SeekingAlpha
2/10:  Forums, Reddit (avoided)
```

## Key Features

### 1. **Configurable Generation**
- `--quick`: 500-word briefs
- `--words N`: Custom word count
- `--auto`: AI-generated topics
- `--no-kb`: Skip knowledge base

### 2. **Parallel Execution**
- Research: Web + KB simultaneously
- Enhancement: SEO + Metrics together
- Distribution: Summary + Social in parallel
- ~40% faster than sequential

### 3. **Automatic Quality Control**
- Extracts all factual claims
- Verifies each has credible citation
- Checks URL accessibility
- Iterates to fix issues automatically

### 4. **Output Package**
```
runs/[timestamp]-[topic]/
├── [slug]-article.md         # Main article
├── evidence-pack.json        # Source verification
├── quality-report.md         # Performance metrics
├── fact-check-report.md      # Detailed verification
├── executive-summary.md      # Summary
├── social-media.md          # Social posts
└── seo-metadata.json        # SEO data
```

## Current State & Capabilities

### ✅ Implemented
- Full Chat Completions API pipeline
- Vector store integration
- Parallel agent execution
- Comprehensive fact-checking
- Automatic quality iteration
- Token/cost tracking
- Configurable parameters
- Auto topic generation

### 🚧 Limitations
- Web search currently simulated (needs real API)
- URL verification simulated (needs real HTTP)
- Vector store requires manual setup

## Quick Start Commands
```bash
# First time setup
python setup_vector_store.py

# Generate article
python main_chat.py generate "Your topic"

# Quick brief
python main_chat.py generate "Topic" --quick

# Auto topic
python main_chat.py generate --auto

# Check config
python main_chat.py config
```

## Project Structure
```
/
├── src/
│   ├── agents/          # Agent implementations
│   ├── pipeline/        # Orchestrators
│   ├── prompts/         # Agent instructions (.md)
│   ├── tools/           # Fact verification, vector store
│   └── config_enhanced.py
├── knowledge_base/      # Dakota materials
├── context-docs/        # This documentation
├── main_chat.py        # Entry point
└── setup_vector_store.py
```

## Critical Files
- **Pipeline Logic**: `src/pipeline/chat_orchestrator.py`
- **Configuration**: `src/config_enhanced.py`
- **Fact Checking**: `src/tools/fact_verification.py`
- **Entry Point**: `main_chat.py`

## Recovery Checklist
If returning after break:
1. Read this document
2. Check `python main_chat.py config`
3. Review any feature docs in `/context-docs/features/`
4. Check current todo list
5. Run `python main_chat.py test`

## Design Philosophy
- **Simplicity**: Use existing tools, avoid over-engineering
- **Quality**: No compromises on accuracy
- **Efficiency**: Parallel execution where possible
- **Transparency**: Track all sources and costs
- **Automation**: Self-correcting system

Last Updated: 2024-01-09