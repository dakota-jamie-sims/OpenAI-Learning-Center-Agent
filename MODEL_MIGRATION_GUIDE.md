# Model Configuration Migration Guide

## Quick Fix Instructions

The system is currently configured to use non-existent models (GPT-5 and GPT-4.1). Follow these steps to fix:

### Step 1: Update config_enhanced.py

Replace lines 20-34 in `/src/config_enhanced.py` with:

```python
# Model Selection (Using actual OpenAI models)
DEFAULT_MODELS = {
    # Critical quality agents - use GPT-4 Turbo
    "writer": "gpt-4-turbo",           
    "factchecker": "gpt-4-turbo",      
    "synthesizer": "gpt-4-turbo",      
    
    # Research agents - use GPT-4o
    "web_researcher": "gpt-4o",        
    "kb_researcher": "gpt-4o",         
    "evidence": "gpt-4o",              
    "claims": "gpt-4o",                
    "iteration": "gpt-4o",             
    
    # Supporting agents - use GPT-4o-mini
    "summary": "gpt-4o-mini",          
    "metrics": "gpt-4o-mini",          
    
    # Low-complexity agents - use GPT-3.5 Turbo
    "seo": "gpt-3.5-turbo",           
    "social": "gpt-3.5-turbo"         
}
```

### Step 2: Update config.py

Replace lines 9-23 in `/src/config.py` with:

```python
DEFAULT_MODELS = {
    "orchestrator": os.getenv("ORCHESTRATOR_MODEL", "gpt-4o"),
    "web_researcher": os.getenv("WEB_RESEARCHER_MODEL", "gpt-4o"),
    "kb_researcher": os.getenv("KB_RESEARCHER_MODEL", "gpt-4o-mini"),
    "synthesizer": os.getenv("SYNTHESIZER_MODEL", "gpt-4-turbo"),
    "writer": os.getenv("WRITER_MODEL", "gpt-4-turbo"),
    "seo": os.getenv("SEO_MODEL", "gpt-3.5-turbo"),
    "fact_checker": os.getenv("FACT_CHECKER_MODEL", "gpt-4-turbo"),
    "summary": os.getenv("SUMMARY_MODEL", "gpt-4o-mini"),
    "social": os.getenv("SOCIAL_MODEL", "gpt-3.5-turbo"),
    "iteration": os.getenv("ITERATION_MODEL", "gpt-4o"),
    "metrics": os.getenv("METRICS_MODEL", "gpt-4o-mini"),
    "evidence": os.getenv("EVIDENCE_MODEL", "gpt-4o"),
    "claim_checker": os.getenv("CLAIM_CHECKER_MODEL", "gpt-4o-mini"),
}
```

### Step 3: Update run.py

Remove or comment out line 7 in `/src/run.py`:
```python
# Initialize GPT-5 compatibility FIRST  <-- Remove this line
```

### Step 4: Update README files

In `/README.md`, change line 81 from:
```markdown
- GPT-5 compatibility
```
to:
```markdown
- GPT-4 Turbo and GPT-4o optimized configuration
```

### Step 5: Environment Variables (Optional)

If you want to override models via environment variables, add to `.env`:

```bash
# High quality configuration
WRITER_MODEL=gpt-4-turbo
FACT_CHECKER_MODEL=gpt-4-turbo
SYNTHESIZER_MODEL=gpt-4-turbo

# Or cost-optimized configuration
WRITER_MODEL=gpt-4o
FACT_CHECKER_MODEL=gpt-4o
SYNTHESIZER_MODEL=gpt-4o-mini
```

## Testing After Migration

1. Run a test article generation:
   ```bash
   python src/run.py "Test Article: Understanding Private Equity"
   ```

2. Monitor the logs for any model-related errors

3. Verify the output quality meets expectations

## Model Selection Guidelines

### When to use GPT-4 Turbo:
- Content generation (writer agent)
- Fact checking and verification
- Complex synthesis tasks
- When quality is paramount

### When to use GPT-4o:
- Research tasks
- Evidence analysis
- Iteration management
- Good balance of cost/performance

### When to use GPT-4o-mini:
- Metrics calculation
- Summary generation
- Supporting analysis tasks
- When cost optimization is important

### When to use GPT-3.5 Turbo:
- SEO optimization
- Social media content
- Simple formatting tasks
- Maximum cost savings

## Cost Comparison

Estimated cost per article:
- All GPT-4 Turbo: ~$3.50
- Balanced (recommended): ~$2.00
- Cost-optimized: ~$1.00

## Support

If you encounter issues:
1. Check that all model names are spelled correctly
2. Verify your OpenAI API key has access to these models
3. Monitor rate limits for GPT-4 models
4. Consider starting with cost-optimized configuration and upgrading based on quality needs