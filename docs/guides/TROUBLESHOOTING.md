# Troubleshooting Guide for Dakota OpenAI Agents

## Current Issue: Short Article Generation

### Problem
The content writer is generating articles that are too short (200-850 words) instead of the required 1,750+ words.

### Identified Issues

1. **Model Output Limitations**: The OpenAI models may have output length constraints
2. **Token Budget Conflicts**: The orchestrator was overriding prompts with token limits
3. **Prompt Following**: Models aren't strictly following the detailed template

### Solutions Implemented

1. **Enhanced Prompts**: Updated all agent prompts with explicit requirements
2. **Removed Token Caps**: Modified orchestrator to emphasize word count over token limits
3. **Fixed File Writing**: Resolved issue with write_text function for paths without directories
4. **Mandatory Validation**: Fact-checking now rejects articles under 1,750 words

### Recommended Next Steps

1. **Use GPT-4 Turbo or GPT-4o**:
   ```bash
   export WRITER_MODEL=gpt-4-turbo-preview
   # or
   export WRITER_MODEL=gpt-4o
   ```

2. **Increase Output Token Limit**:
   ```bash
   export WRITER_MAX_TOKENS=8000
   ```

3. **Split Article Generation**:
   - Consider generating article in sections
   - Use continuation prompts to reach word count
   - Implement a multi-pass approach

4. **Test Different Models**:
   ```python
   # In .env or environment
   WRITER_MODEL=gpt-4-turbo-2024-04-09
   WRITER_MODEL=gpt-4o
   WRITER_MODEL=gpt-4-0125-preview
   ```

5. **Enable Debug Mode**:
   - Add logging to see exact prompts sent
   - Track token usage per agent
   - Monitor rejection reasons

### Quick Test

To test if a model can generate long content:
```bash
# Create test script
python test_content_writer.py

# Or modify run.py to use a specific model
WRITER_MODEL=gpt-4-turbo python run.py "your topic"
```

### Alternative Approach

If models consistently produce short content, implement a continuation system:
1. Generate initial article section
2. Use continuation prompt to add more sections
3. Merge sections while maintaining coherence
4. Validate final combined article

### Model Recommendations

For best results with long-form content:
- **GPT-4 Turbo**: Best balance of quality and length
- **GPT-4o**: Good for following complex instructions
- **Claude 3 Opus**: If switching platforms is an option

### Validation Checklist

Before running:
- [ ] Verify WRITER_MODEL is set to a capable model
- [ ] Confirm WRITER_MAX_TOKENS is 8000+
- [ ] Check that prompts emphasize word count
- [ ] Ensure file paths are absolute
- [ ] Test with a simple topic first

### Contact Support

If issues persist:
1. Check OpenAI API limits
2. Verify model availability in your region
3. Consider implementing streaming responses
4. Review API response for specific errors