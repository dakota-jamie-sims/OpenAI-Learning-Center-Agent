# Dakota OpenAI Learning Center Agent

A sophisticated multi-agent content generation system that produces high-quality investment education articles with the same standards as the Claude Code implementation.

## 🚀 Quick Start

```bash
# 1. Setup environment
cd dakota-openai-agents
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Add your OpenAI API key to .env

# 3. Generate an article
python src/run.py "benefits of index fund investing"
```

## 📁 Project Structure

```
dakota-openai-agents/
├── src/                    # Source code
│   ├── agents/            # 12 specialized agents
│   ├── prompts/           # Agent instructions
│   ├── pipeline/          # Orchestration
│   ├── tools/             # Utilities
│   └── run.py            # Entry point
├── knowledge_base/         # 397 reference articles
├── templates/             # Output templates
├── output/                # Generated articles
└── docs/                  # Documentation
```

## 🤖 Agent System

### 12 Specialized Agents
1. **Web Researcher** - Gathers current market data
2. **KB Researcher** - Searches Dakota knowledge base
3. **Evidence Packager** - Creates proof documentation
4. **Research Synthesizer** - Combines research
5. **Content Writer** - Creates main article (1,750+ words)
6. **Fact Checker** - Verifies all claims (MANDATORY)
7. **SEO Specialist** - Optimizes metadata
8. **Metrics Analyzer** - Tracks quality metrics
9. **Summary Writer** - Creates executive summary
10. **Social Promoter** - Generates social content
11. **Iteration Manager** - Fixes rejected articles
12. **Claim Checker** - Validates assertions

### Workflow Phases
1. **Research** (Parallel Web + KB search)
2. **Evidence Packaging** 
3. **Synthesis**
4. **Content Creation**
5. **Enhancement** (SEO + Metrics)
6. **MANDATORY Fact-Checking**
7. **Distribution** (Summary + Social)

## 📋 Quality Standards

### Requirements
- ✅ Minimum 1,750 words
- ✅ 10+ verified sources with URLs
- ✅ 100% URL verification (all must return HTTP 200)
- ✅ Specific template structure
- ✅ No vague references ("studies show")
- ✅ Current data only (<12 months for financials)

### Output Files
Each article generates 4 files:
1. `dakota-article.md` - Main article
2. `dakota-metadata.md` - SEO and metrics
3. `dakota-social.md` - Social media content
4. `dakota-summary.md` - Executive summary

## ⚙️ Configuration

### Environment Variables
```bash
# Required
OPENAI_API_KEY=your-key-here

# Optional - Output location
DAKOTA_OUTPUT_DIR=/custom/output/path

# Quality settings
MIN_WORD_COUNT=1750
MIN_SOURCES=10
MAX_ITERATIONS=2
FACT_CHECK_MANDATORY=true

# Model selection (for better results)
WRITER_MODEL=gpt-4-turbo
WRITER_MAX_TOKENS=8000
```

### Recommended Models
- **GPT-4 Turbo**: Best for long-form content
- **GPT-4o**: Good instruction following
- **GPT-4**: Standard quality

## 🔧 Troubleshooting

### Short Articles
If articles are too short:
```bash
# Use a more capable model
export WRITER_MODEL=gpt-4-turbo
export WRITER_MAX_TOKENS=8000
```

### Validation Failures
Common rejection reasons:
- Missing YAML frontmatter
- Too few words or citations
- Missing required sections
- Broken URLs

### File Writing Issues
Ensure output directory exists and is writable:
```bash
mkdir -p "output/Dakota Learning Center Articles"
chmod 755 output
```

## 📊 Validation Process

The system enforces quality through:

1. **Template Validation**
   - Required sections check
   - Forbidden sections check
   - Structure compliance

2. **Content Validation**
   - Word count verification
   - Citation count check
   - Source URL testing

3. **Iteration System**
   - Automatic fixes for failures
   - Maximum 2 retry attempts
   - Detailed error reporting

## 🎯 Best Practices

1. **Topic Selection**
   - Be specific and focused
   - Include target audience
   - Example: "index fund benefits for institutional investors"

2. **Model Configuration**
   - Use GPT-4 Turbo for best results
   - Increase token limits for long content
   - Monitor API costs

3. **Quality Assurance**
   - Review fact-checker reports
   - Verify all URLs work
   - Check citation accuracy

## 📚 Additional Resources

- **Implementation Details**: See `docs/IMPLEMENTATION.md`
- **Setup Guide**: See `docs/SETUP.md`
- **Troubleshooting**: See `docs/TROUBLESHOOTING.md`
- **Migration Guide**: See `MIGRATION_GUIDE.md`

## 🤝 Support

For issues or questions:
1. Check the troubleshooting guide
2. Review validation reports
3. Verify model configuration
4. Ensure API key is valid

---

Built to match the quality standards of the Claude Code Learning Center Agent while leveraging OpenAI's powerful models.