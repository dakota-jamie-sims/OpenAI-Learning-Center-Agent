# Dakota Learning Center - Feature Summary

## System Overview
AI-powered article generation system for Dakota's Learning Center that creates institutional-quality investment education content with zero compromise on accuracy. Built with OpenAI's Chat Completions API and sophisticated multi-agent architecture.

## Core Features

### 1. **Multi-Agent Architecture**
- 12 specialized agents working in parallel phases
- Chat Completions API for speed and control
- Configurable models: GPT-5 for complex tasks, GPT-4.1 for efficient operations
- Token tracking for cost transparency

### 2. **100% Data Freshness Guarantee**
- **Multi-Layer Validation System**
  - Research phase: Mandates current data searches
  - Writing phase: Requires timestamps on all data
  - Validation phase: Automated date extraction and checking
  - Final check: Rejects if missing current year data
- **Configurable Freshness Rules**
  - Market data: Within 30 days
  - Allocation data: Within 90 days
  - Regulatory data: Within 60 days
  - General data: Within 180 days
- **DataFreshnessValidator Class**
  - Extracts dates from text
  - Categorizes by data type
  - Provides specific recommendations

### 3. **Dakota-Specific Enhancements**
- **Target Audience Focus**
  - RIAs, Family Offices, Pension Funds
  - Endowments, Foundations, OCIOs
  - Insurance Companies, Healthcare Systems
- **Content Requirements**
  - Real allocation amounts with dates
  - RFP and search activity tracking
  - Investor preference insights
  - Fundraising application takeaways
- **Dakota Way Integration**
  - "Focus on What Matters Most" principle
  - Minimum 2 Dakota internal links
  - Practical sales applications

### 4. **Knowledge Base Integration**
- OpenAI vector store with Dakota content
- 397 Learning Center articles indexed
- Dakota Way chapters embedded
- KB-aware topic generation to avoid duplicates
- Semantic search for relevant content

### 5. **GPT's Built-in Web Search**
- Web researcher uses GPT's native search capabilities
- No separate web_search tool implementation
- Automatic searches for:
  - Current allocation data
  - Recent RFP activity
  - Market trends with dates
  - Fundraising intelligence

### 6. **Enhanced Topic Generation**
- **EnhancedTopicGenerator Class**
  - Analyzes existing KB content
  - Identifies content gaps
  - Avoids topic duplication
  - Aligns with Dakota's focus areas
- **Auto-generation Command**
  - `python main_chat.py generate --auto`
  - KB-aware unique topic selection

### 7. **Quality Enforcement**
- **Minimum Standards**
  - 2000+ words (configurable)
  - 12+ credible sources
  - 80% credibility score
  - 90% fact accuracy
- **Source Credibility Hierarchy**
  - Government/Official: 10/10
  - Academic/Research: 9/10
  - Major Financial Media: 8/10
  - Industry Organizations: 7/10
- **Automatic Iteration**
  - Up to 3 attempts to meet quality
  - Specific fix instructions provided

### 8. **Parallel Execution**
- **Concurrent Phases**
  - Research: Web + KB simultaneously
  - Enhancement: SEO + Metrics together
  - Distribution: Summary + Social in parallel
- **Performance Benefits**
  - ~40% faster than sequential
  - Efficient resource utilization
  - Asyncio-based orchestration

### 9. **Comprehensive Validation**
- **Fact Verification**
  - Every claim must have citation
  - URL accessibility testing
  - Source credibility scoring
  - Date validation for all data
- **Structure Compliance**
  - Required sections enforcement
  - Forbidden sections blocking
  - Template adherence checking

### 10. **Output Package**
Each generation creates:
```
runs/[timestamp]-[topic]/
├── [slug]-article.md         # Main article with dated citations
├── evidence-pack.json        # Source verification with dates
├── quality-report.md         # Performance & freshness metrics
├── fact-check-report.md      # Detailed verification & dates
├── executive-summary.md      # Summary for fundraisers
├── social-media.md          # Social posts
└── seo-metadata.json        # SEO data
```

## Command Reference

### Article Generation
```bash
# Standard article (2000+ words)
python main_chat.py generate "Your topic"

# Quick brief (500 words)
python main_chat.py generate "Your topic" --quick

# Custom word count
python main_chat.py generate "Your topic" --words 1500

# Auto-generate topic (KB-aware)
python main_chat.py generate --auto

# Skip knowledge base
python main_chat.py generate "Your topic" --no-kb
```

### System Commands
```bash
# Setup vector store
python setup_vector_store.py

# Check configuration
python main_chat.py config

# Get topic suggestions
python main_chat.py topics

# Test generation
python main_chat.py test
```

## Key Innovations

1. **Zero-Compromise Quality**: Automatic enforcement of Dakota's standards
2. **Current Data Only**: Multi-layer freshness validation system
3. **Fundraising Focus**: Every article includes practical applications
4. **Efficiency**: Parallel execution reduces generation time by 40%
5. **Transparency**: Complete source tracking and verification reports
6. **Intelligence**: KB-aware to avoid content duplication
7. **Flexibility**: Configurable for various content types and lengths

## Configuration Highlights
- Models: GPT-5 (complex), GPT-4.1 (efficient)
- Quality: 80% credibility, 90% fact accuracy
- Freshness: 30-day market data, 90-day allocation data
- Output: 2000+ words, 12+ sources minimum
- Iteration: Up to 3 attempts for quality

## Recent Updates
- Integrated GPT's built-in web search
- Added multi-layer data freshness validation
- Enhanced with Dakota-specific requirements
- Implemented KB-aware topic generation
- Updated all prompts for current data focus

Last Updated: 2025-01-09