# Project Structure Guidelines

## Directory Organization

### `/src/` - Source Code
- `/src/agents/` - Multi-agent system components
- `/src/pipeline/` - Orchestrators for article generation
- `/src/services/` - Service modules (API clients, search, etc.)
- `/src/tools/` - Utility tools and handlers
- `/src/utils/` - Helper functions and utilities
- `/src/prompts/` - Agent prompt templates
- `/src/config.py` - Configuration settings

### `/scripts/` - Executable Scripts
- Article generation scripts (`generate_*.py`)
- Utility scripts in `/scripts/utilities/`
- One-time setup or migration scripts

### `/tests/` - Test Files
- `/tests/integration/` - Integration tests
- `/tests/unit/` - Unit tests (if added)
- Test files should be named `test_*.py`

### `/docs/` - Documentation
- `/docs/architecture/` - Architecture documentation
- `/docs/guides/` - User guides and tutorials
- `/docs/commands/` - Command reference files
- `/docs/reference/` - API and technical reference
- Project documentation (`.md` files)

### `/data/` - Data Files
- `/data/knowledge_base/` - Dakota knowledge base articles
- `/data/templates/` - Document templates (if any)
- Static data files

### `/output/` - Generated Output
- Article output directories (timestamped)
- Each article gets its own subdirectory

### `/context/` - Context Management
- `JOURNAL.md` - Project journal
- `TODO.md` - Task tracking
- Context status files

### Root Directory Files
- Configuration files (`.env`, `.gitignore`)
- `README.md`
- `requirements.txt`
- `activate_context.sh`
- Important user-facing command files (e.g., `TEST_ARTICLE_GENERATION.txt`)

## File Placement Rules

1. **Source Code**: All Python modules go in `/src/` with appropriate subdirectory
2. **Scripts**: Executable scripts go in `/scripts/`
3. **Tests**: All test files go in `/tests/` with `test_` prefix
4. **Documentation**: All docs, guides, and command references go in `/docs/`
5. **Temporary Files**: Should go in `/tmp/` or be cleaned up after use
6. **Configuration**: Project-wide configs stay in root, module configs in `/config/`

## Naming Conventions

- Python files: `lowercase_with_underscores.py`
- Test files: `test_<module_name>.py`
- Documentation: `UPPERCASE_TITLE.md` or `lowercase-with-hyphens.md`
- Scripts: Descriptive names like `generate_article.py`