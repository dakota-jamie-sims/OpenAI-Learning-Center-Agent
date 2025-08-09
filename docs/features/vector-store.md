# Feature: Vector Store Knowledge Base Integration

## Overview
The system uses OpenAI's vector store to provide semantic search over Dakota's knowledge base materials, enabling the KB Researcher agent to find relevant content.

## Implementation Details

### 1. **Setup Process**
Location: `setup_vector_store.py`

```python
# One-time setup:
1. Creates vector store in OpenAI
2. Uploads all .md/.txt files from knowledge_base/
3. Saves VECTOR_STORE_ID to .env
4. Tests search functionality
```

### 2. **Vector Store Handler**
Location: `src/tools/vector_store_handler.py`

Key methods:
- `create_or_get_vector_store()` - Creates new or retrieves existing
- `upload_knowledge_base()` - Uploads files with embeddings
- `search_knowledge_base()` - Semantic search using Assistants API

### 3. **KB Researcher Integration**
The KB Researcher agent uses vector search instead of file reading:

```python
# In chat_orchestrator.py
kb_tool_def = self.kb_search_tool.get_tool_definition()

# Agent configuration
{
    "name": "kb_researcher",
    "tools": [kb_tool_def],  # search_knowledge_base function
}
```

### 4. **Search Process**
```python
# When KB Researcher calls search_knowledge_base("query"):
1. Function call intercepted
2. Vector store handler creates temporary Assistant
3. Performs semantic search
4. Returns relevant passages
5. Temporary Assistant deleted
```

## Usage

### Initial Setup
```bash
# First time only
python setup_vector_store.py

# This will:
- Create vector store
- Upload knowledge base files
- Save ID to .env
- Test search
```

### In Pipeline
```python
# Automatic during Phase 2 (Research)
("kb_researcher", "Search Dakota knowledge for: [topic]")

# KB Researcher can make multiple searches:
- "Dakota investment philosophy"
- "Alternative investments approach"
- "Risk management framework"
```

## Configuration

### Environment Variable
```bash
# .env file
VECTOR_STORE_ID=vs_abc123...
```

### Knowledge Base Location
```python
# src/config_enhanced.py
KNOWLEDGE_BASE_DIR = PROJECT_ROOT / "knowledge_base"
```

## Integration Points

### 1. **Orchestrator Initialization**
```python
# Checks for existing vector store
vector_store_id = self.vector_handler.create_or_get_vector_store()

# Uploads files if new
if not os.getenv("VECTOR_STORE_ID"):
    kb_files = self.vector_handler.upload_knowledge_base(...)
```

### 2. **KB Search Tool**
```python
# Function definition for agent
{
    "type": "function",
    "function": {
        "name": "search_knowledge_base",
        "description": "Search Dakota's knowledge base",
        "parameters": {
            "query": {"type": "string"},
            "max_results": {"type": "integer", "default": 6}
        }
    }
}
```

## Troubleshooting

### "No vector store configured"
```bash
# Check if ID exists
cat .env | grep VECTOR_STORE_ID

# If missing, run setup
python setup_vector_store.py
```

### "Search not returning results"
1. Verify files exist in knowledge_base/
2. Check vector store in OpenAI dashboard
3. Test with broader search terms

### "Want to skip KB search"
```bash
# Use --no-kb flag
python main_chat.py generate "topic" --no-kb
```

## Benefits
- **Semantic Search**: Finds conceptually related content
- **Scalability**: Handles thousands of documents
- **Speed**: Pre-computed embeddings
- **Accuracy**: Better than keyword matching

## Limitations
- Requires Assistants API temporarily (for search only)
- One-time setup needed
- Limited to 100 files currently
- No real-time updates (requires re-upload)

## Future Enhancements
- Automatic knowledge base updates
- Multiple vector stores for different domains
- Hybrid search (semantic + keyword)
- Relevance feedback loop