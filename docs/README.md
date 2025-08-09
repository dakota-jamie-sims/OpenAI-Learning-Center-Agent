# Dakota Learning Center Documentation

Comprehensive documentation for the AI-powered article generation system.

## 📚 Documentation Structure

```
docs/
├── README.md                    # You are here
├── QUICKSTART.md               # Get started in 5 minutes
├── ARCHITECTURE.md             # System design and components
├── DEVELOPMENT.md              # Development guidelines
├── POST-COMPACT-RECOVERY.md    # Recovery after auto-compaction
│
├── features/                   # Feature-specific docs
│   ├── fact-checking.md       # 100% accuracy system
│   ├── vector-store.md        # Knowledge base integration
│   ├── parallel-execution.md  # Async performance
│   ├── auto-topics.md         # Topic generation
│   └── quality-iteration.md   # Automatic fixes
│
├── guides/                     # How-to guides
│   ├── LOCAL_TESTING_GUIDE.md
│   └── IMPLEMENTATION_GUIDE.md
│
├── setup/                      # Setup documentation
│   └── GPT5_COMPATIBILITY.md
│
├── reference/                  # Technical reference
│   └── (configuration, APIs, etc.)
│
└── claude-code-reference/      # Claude Code documentation
```

## 🚀 Start Here

### New Users
1. **[QUICKSTART.md](QUICKSTART.md)** - Get running in 5 minutes
2. **[ARCHITECTURE.md](ARCHITECTURE.md)** - Understand the system
3. **Run your first article** - `python main_chat.py generate --auto`

### Returning After Break
1. **[POST-COMPACT-RECOVERY.md](POST-COMPACT-RECOVERY.md)** - Quick recovery steps
2. **Check current status** - `python main_chat.py config`
3. **Review relevant feature docs** based on current work

### Developers
1. **[DEVELOPMENT.md](DEVELOPMENT.md)** - Coding guidelines
2. **[features/](features/)** - Deep dive into capabilities
3. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System internals

## 📖 Key Documents

### Core Documentation
- **[QUICKSTART.md](QUICKSTART.md)** - Installation and basic usage
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Complete system overview, agents, quality standards
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - How to work with the codebase
- **[POST-COMPACT-RECOVERY.md](POST-COMPACT-RECOVERY.md)** - Recover context quickly

### Feature Documentation
- **[fact-checking.md](features/fact-checking.md)** - How 100% accuracy is ensured
- **[vector-store.md](features/vector-store.md)** - Knowledge base search system
- **[parallel-execution.md](features/parallel-execution.md)** - Performance optimization
- **[auto-topics.md](features/auto-topics.md)** - Automatic topic generation
- **[quality-iteration.md](features/quality-iteration.md)** - Self-correcting quality

## 🔧 Common Tasks

### Generate Articles
```bash
# Standard article
python main_chat.py generate "Your topic"

# Quick 500-word brief
python main_chat.py generate "Topic" --quick

# Auto-generate topic
python main_chat.py generate --auto

# Custom length
python main_chat.py generate "Topic" --words 1000
```

### System Management
```bash
# Check configuration
python main_chat.py config

# Set up vector store
python setup_vector_store.py

# Run tests
python main_chat.py test

# Get topic ideas
python main_chat.py topics
```

## 🏗️ System Overview

### Technology Stack
- **API**: OpenAI Chat Completions (not Assistants)
- **Language**: Python with asyncio
- **Storage**: OpenAI vector store for knowledge base
- **Architecture**: 12 specialized agents with parallel execution

### Quality Standards
- **Minimum 80%** credibility score
- **90%** fact accuracy required
- **All facts** must have credible citations
- **Automatic iteration** up to 3 times

### Key Features
- ✅ Configurable word counts (500-5000+)
- ✅ Parallel agent execution
- ✅ Comprehensive fact-checking
- ✅ Vector store knowledge base
- ✅ Automatic quality improvement
- ✅ Multiple output formats
- ✅ Token/cost tracking

## 📋 Quick Reference

### File Locations
- **Main entry**: `main_chat.py`
- **Pipeline**: `src/pipeline/chat_orchestrator.py`
- **Configuration**: `src/config_enhanced.py`
- **Agent prompts**: `src/prompts/dakota-*.md`
- **Fact checker**: `src/tools/fact_verification.py`

### Environment Variables
```bash
OPENAI_API_KEY=sk-...        # Required
VECTOR_STORE_ID=vs_...       # Created by setup_vector_store.py
```

### Output Structure
```
runs/[timestamp]-[topic]/
├── article.md               # Main article
├── quality-report.md        # Performance metrics
├── fact-check-report.md     # Verification details
├── executive-summary.md     # Brief summary
├── social-media.md         # Social posts
└── evidence-pack.json      # Source verification
```

## 🛠️ Troubleshooting

### Common Issues
- **"No vector store"** → Run `python setup_vector_store.py`
- **"API key missing"** → Add to `.env` file
- **"Import errors"** → Activate venv, install requirements

### Getting Help
1. Check relevant feature documentation
2. Run with `--debug` flag for details
3. Review `article_generation.log`
4. See [POST-COMPACT-RECOVERY.md](POST-COMPACT-RECOVERY.md) if context lost

## 📈 Best Practices

1. **Always use the pipeline** - Don't generate content manually
2. **Trust the quality system** - It will iterate to fix issues
3. **Check costs** - Review token usage in reports
4. **Update docs** - Keep documentation current with changes

## 🔄 Maintenance

- Review docs quarterly
- Update after major changes
- Add new feature docs as needed
- Keep examples current

---

*Last Updated: 2024-01-09*