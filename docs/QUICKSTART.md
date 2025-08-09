# Quick Start Guide

Get up and running with the Dakota Learning Center Article Generator in 5 minutes.

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- Git (for cloning the repository)

## Installation

### 1. Clone the Repository
```bash
git clone [repository-url]
cd learning-center-agent-open-ai
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure API Key
```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-...
```

### 4. Set Up Knowledge Base (One-time)
```bash
# This creates a vector store with Dakota's knowledge base
python setup_vector_store.py
```

## Basic Usage

### Generate Your First Article
```bash
# Standard 2000+ word article
python main_chat.py generate "The Impact of ESG on Investment Returns"
```

### Quick Commands

**500-word brief:**
```bash
python main_chat.py generate "Market volatility strategies" --quick
```

**Auto-generate topic:**
```bash
python main_chat.py generate --auto
```

**Custom word count:**
```bash
python main_chat.py generate "Factor investing guide" --words 1500
```

**Get topic suggestions:**
```bash
python main_chat.py topics
```

## Output

Articles are saved in `runs/[timestamp]-[topic]/` with:
- `article.md` - The main article
- `quality-report.md` - Generation metrics
- `fact-check-report.md` - Verification details
- `executive-summary.md` - Brief summary
- `social-media.md` - Social posts

## Verify Installation

```bash
# Run test generation
python main_chat.py test

# Check configuration
python main_chat.py config
```

## Common Issues

### "No vector store ID found"
Run `python setup_vector_store.py` first

### "API key not found"
Make sure `.env` file contains `OPENAI_API_KEY=sk-...`

### "Module not found"
Ensure virtual environment is activated and dependencies installed

## Next Steps

- Read [ARCHITECTURE.md](ARCHITECTURE.md) to understand the system
- Check [features/](features/) for specific capabilities
- See [DEVELOPMENT.md](DEVELOPMENT.md) for customization

## Need Help?

- Run `python main_chat.py --help` for all options
- Check [POST-COMPACT-RECOVERY.md](POST-COMPACT-RECOVERY.md) if resuming work
- Review logs in `article_generation.log`