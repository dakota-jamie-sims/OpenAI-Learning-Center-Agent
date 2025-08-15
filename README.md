# Learning Center Agent - OpenAI

An AI-powered content generation system for creating educational articles for the Dakota Learning Center.

## 🚀 Quick Start - Working Solution

The simplest way to generate articles that work 100% of the time:

```bash
# Activate virtual environment
source venv/bin/activate

# Generate an article
python generate_article.py "Your Article Topic" [word_count]

# Examples:
python generate_article.py "Top Private Equity Strategies for 2025"
python generate_article.py "Understanding Alternative Investments" 2000
```

This will generate a complete content package in `output/Learning Center Articles/` including:
- 📄 Main article with proper citations
- 📋 Executive summary  
- 📱 Social media content
- 📊 Metadata

## Overview

This project uses OpenAI's GPT models to create high-quality educational content aligned with Dakota's values and pedagogical approach. The system employs a multi-agent architecture with specialized agents for research, outlining, writing, and review.

## Project Structure

```
learning-center-agent-open-ai/
├── src/                          # Source code
│   ├── agents/                   # Agent implementations
│   │   ├── researcher_agent.py
│   │   ├── outliner_agent.py
│   │   ├── content_writer.py
│   │   └── reviewer_agent.py
│   ├── pipeline/                 # Orchestration
│   │   └── orchestrator.py
│   ├── prompts/                  # Agent prompts
│   ├── tools/                    # Utilities
│   ├── config.py                 # Configuration
│   └── run.py                    # Main entry point
├── knowledge_base/               # Dakota knowledge resources
│   ├── dakota_way/
│   └── learning_center/
├── tests/                        # Test files
├── output/                       # Generated articles
│   └── articles/
├── docs/                         # Documentation
│   ├── setup/
│   └── guides/
├── templates/                    # Article templates
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env` and add your OpenAI API key:
   ```bash
   cp .env.example .env
   ```

## Usage

Generate an article:
```bash
python src/run.py --topic "Your Topic Here"
```

Run tests:
```bash
python tests/test_minimal.py
```

## Documentation

- [Setup Guide](docs/setup/SETUP_GPT5.md)
- [Implementation Guide](docs/guides/IMPLEMENTATION_GUIDE.md)
- [Troubleshooting](docs/guides/TROUBLESHOOTING.md)
- [Local Testing Guide](docs/setup/LOCAL_TESTING_GUIDE.md)

## Key Features

- Multi-agent architecture for comprehensive content generation
- Integration with Dakota's knowledge base
- Automated review and fact-checking
- GPT-5 compatibility
- Configurable output formats

## Contributing

Please read the implementation guide before contributing. Ensure all agents maintain alignment with Dakota's educational philosophy and values.