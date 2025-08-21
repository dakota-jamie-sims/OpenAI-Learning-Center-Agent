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