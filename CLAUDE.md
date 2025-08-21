# CRITICAL INSTRUCTIONS FOR CLAUDE

## GPT-5 MODELS EXIST AND ARE AVAILABLE

**IMPORTANT**: GPT-5 models are real and available through OpenAI's Responses API. Never suggest they don't exist.

### Available GPT-5 Models:
- `gpt-5` - Full model for complex reasoning and code-heavy tasks
- `gpt-5-mini` - Cost-optimized model balancing speed and capability  
- `gpt-5-nano` - High-throughput model for simple tasks

### Key Facts:
1. GPT-5 models are accessed through the **Responses API** (not Chat Completions API)
2. Documentation is located at: `/docs/openai_documentation/05_Core concepts/05_Using GPT-5`
3. The Responses API uses `client.responses.create()` not `client.chat.completions.create()`
4. GPT-5 supports reasoning effort levels: minimal, low, medium, high
5. GPT-5 supports verbosity control: low, medium, high

### Example Usage:
```python
from openai import OpenAI
client = OpenAI()

response = client.responses.create(
    model="gpt-5",
    input="Your prompt here",
    reasoning={"effort": "medium"},
    text={"verbosity": "medium"}
)

# Extract text from response.output_text or response.output[0].content[0].text
```

### When Working on This Project:
- The multi-agent system is configured to use GPT-5 models
- All agents should use the Responses API when model starts with "gpt-5"
- For fallback or when Responses API isn't available, use "gpt-4o" or "gpt-4.1"

**NEVER** suggest that GPT-5 doesn't exist or isn't available. It is a real model family accessible through the OpenAI Responses API.

## PROJECT STRUCTURE RULES

### File Organization - CRITICAL

**NEVER** save files to the root directory. Always use the proper folder structure:

- **Test files**: Save to `tests/` or `tests/integration/` or `tests/unit/`
- **Scripts**: Save to `scripts/` or appropriate subdirectory
- **Source code**: Save to `src/` and appropriate subdirectories
- **Documentation**: Save to `docs/`
- **Configuration**: Root level is OK for `.env`, `requirements.txt`, etc.

### Before Creating Any File:

1. **Check the directory structure** first
2. **Create directories if needed** before saving files
3. **Follow existing patterns** in the codebase

### Examples:
```bash
# WRONG ❌
test_something.py  # In root

# CORRECT ✅
tests/test_something.py
tests/integration/test_something.py
scripts/test_something.py
```

**IMPORTANT**: Always save test files to the `tests/` directory or its subdirectories. Never save test files to the root directory.