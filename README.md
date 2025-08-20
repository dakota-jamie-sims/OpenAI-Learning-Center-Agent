# Dakota Learning Center Article Generation System

An automated system for generating high-quality learning center articles using OpenAI's API with Dakota-specific knowledge and context.

## Quick Start

1. Set up your environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configure OpenAI API:
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

3. Activate context system:
   ```bash
   source ./activate_context.sh
   ```

4. Generate an article:
   ```bash
   python scripts/generate_complete_article.py --topic "private equity trends"
   ```

5. (Optional) Configure logging level:
   ```bash
   export LOG_LEVEL=DEBUG  # INFO by default
   ```

## Project Structure

```
├── src/                    # Source code
│   ├── core/              # Core functionality
│   ├── pipeline/          # Article generation pipelines
│   ├── models/            # Data models
│   ├── services/          # External services
│   └── utils/             # Utilities
├── scripts/               # Executable scripts
├── docs/                  # Documentation
│   ├── openai_documentation/
│   ├── architecture/
│   ├── guides/
│   └── reference/
├── context/               # Auto-generated context
├── tests/                 # Test files
├── data/                  # Knowledge base
├── output/                # Generated articles
└── config/                # Configuration
```

## Features

- **Multiple Generation Pipelines**: Simple, Enhanced, and Strict modes
- **Automated Context Tracking**: Monitors and logs all activities
- **Dakota-Specific Knowledge**: Integrated Dakota Way methodology
- **Quality Assurance**: Built-in validation and iteration
- **Parallel Processing**: Efficient multi-step generation

## Logging

Logging uses the helper in `src/utils/logging.py`. Set the `LOG_LEVEL` environment
variable (`DEBUG`, `INFO`, etc.) to control verbosity. Use `LOG_FORMAT=json` for
JSON-formatted logs.

## Documentation

- [Quick Start Guide](docs/guides/QUICKSTART.md)
- [Architecture Overview](docs/architecture/ARCHITECTURE.md)
- [Development Guide](docs/guides/DEVELOPMENT.md)
- [Adding Articles](docs/guides/ADDING_LEARNING_CENTER_ARTICLES.md)

## Context System Commands

- `auto_generate` - Run article generation with auto-context
- `view_context` - View recent context and status
- `status_update` - Manual status update
- `monitor_context` - Start background monitoring
