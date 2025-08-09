# Migration Guide: New File Structure

## Overview
The Dakota OpenAI Agents project has been reorganized for clarity and maintainability. This guide helps you transition to the new structure.

## New Directory Structure

```
dakota-openai-agents/
├── docs/                     # All documentation
│   ├── README.md            # Main project documentation
│   ├── IMPLEMENTATION.md    # Implementation details
│   ├── SETUP.md            # Setup instructions
│   ├── TROUBLESHOOTING.md  # Common issues and solutions
│   └── guides/             # Additional guides
├── src/                     # Source code
│   ├── agents/             # Agent definitions
│   ├── pipeline/           # Orchestration logic
│   ├── prompts/            # Agent prompts
│   ├── tools/              # Utility functions
│   ├── config.py           # Configuration
│   └── run.py              # Main entry point
├── knowledge_base/          # Reference materials
│   ├── dakota_way/         # Dakota Way content
│   └── learning_center/    # Learning Center articles
├── templates/              # Output templates
├── output/                 # Generated content
│   └── Dakota Learning Center Articles/
└── tests/                  # Test scripts

```

## What Changed

### 1. Consolidated Documentation
- **Before**: Documentation scattered across multiple directories
- **After**: All docs in `/docs` folder
- **Action**: Update bookmarks and references

### 2. Simplified Source Code
- **Before**: Nested dakota_openai_agents/src structure
- **After**: Direct `/src` folder
- **Action**: Update import paths if needed

### 3. Clear Output Directory
- **Before**: Mixed with source files
- **After**: Dedicated `/output` folder
- **Action**: Update output path configuration

### 4. Organized Knowledge Base
- **Before**: Deep nesting with confusing structure
- **After**: Clean `/knowledge_base` folder
- **Action**: Update vector store paths

## Migration Steps

### Step 1: Update Configuration
```bash
# Update .env file
DAKOTA_OUTPUT_DIR=./output/Dakota Learning Center Articles
VECTOR_STORE_ID=your_vector_store_id
```

### Step 2: Update Import Paths
If you have custom scripts, update imports:
```python
# Old
from dakota_openai_agents.src.agents import content_writer

# New
from src.agents import content_writer
```

### Step 3: Run from New Location
```bash
# Navigate to project root
cd dakota-openai-agents

# Run the agent
python src/run.py "your topic here"
```

### Step 4: Verify Output
Check that articles are generated in:
```
output/Dakota Learning Center Articles/YYYY-MM-DD-topic/
```

## Quick Start Commands

```bash
# 1. Clone or move to new structure
cd dakota-openai-agents

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your settings

# 4. Test the system
python src/run.py "test article about index funds"

# 5. Check output
ls output/Dakota\ Learning\ Center\ Articles/
```

## Troubleshooting

### Import Errors
- Ensure you're running from the project root
- Check Python path includes the src directory

### Output Not Found
- Verify DAKOTA_OUTPUT_DIR in .env
- Check write permissions on output directory

### Knowledge Base Issues
- Update VECTOR_STORE_ID if using OpenAI file search
- Ensure knowledge_base path is correct

## Benefits of New Structure

1. **Clarity**: Each directory has a single, clear purpose
2. **Maintainability**: Easier to find and update files
3. **Scalability**: Structure supports project growth
4. **Standards**: Follows Python project best practices
5. **Documentation**: All docs in one searchable location

## Need Help?

- Check `/docs/TROUBLESHOOTING.md` for common issues
- Review `/docs/README.md` for project overview
- See `/docs/IMPLEMENTATION.md` for technical details

The new structure makes the Dakota OpenAI Agents project more professional and easier to work with!