# Updating the Knowledge Base

## Overview
The Dakota Learning Center uses OpenAI's vector store to maintain its knowledge base. This includes Dakota Way content, existing Learning Center articles, and any additional materials you want the system to reference.

## Methods to Update Knowledge Base

### Method 1: Using the Update Script (Recommended)

#### Add Individual Files
```bash
python update_knowledge_base.py add path/to/file1.md path/to/file2.md
```

#### Add Entire Directory
```bash
# Add all .md and .txt files from a directory
python update_knowledge_base.py add-dir path/to/new_content/

# Add specific file types
python update_knowledge_base.py add-dir path/to/docs/ --extensions .md .pdf .docx
```

#### List Current Contents
```bash
python update_knowledge_base.py list
```

### Method 2: Recreate Vector Store
If you have significant changes or want to start fresh:

```bash
# This will prompt to create a new vector store
python setup_vector_store.py
```

### Method 3: Programmatic Updates
```python
from openai import OpenAI
from src.tools.vector_store_handler import VectorStoreHandler

# Initialize
client = OpenAI(api_key="your-key")
handler = VectorStoreHandler(client)

# Upload new files
uploaded = handler.upload_knowledge_base("path/to/new_content/", max_files=50)
```

## Best Practices

### 1. **File Organization**
```
knowledge_base/
├── dakota_way/          # Core Dakota philosophy
├── learning_center/     # Existing articles
├── market_research/     # New market insights
├── case_studies/        # Success stories
└── templates/           # Article templates
```

### 2. **File Naming**
- Use descriptive names: `2025-01-private-equity-allocation-trends.md`
- Include dates for time-sensitive content
- Use consistent formatting

### 3. **Content Guidelines**
- **Markdown Format**: Use .md files for best compatibility
- **Clear Structure**: Use headers, lists, and sections
- **Metadata**: Include publication dates in content
- **Citations**: Include source links

### 4. **Update Frequency**
- **Monthly**: Add new market reports and allocation data
- **Quarterly**: Review and update existing content
- **Annually**: Full knowledge base audit

## What to Add

### High-Value Content
1. **Recent Allocation Data**
   - LP commitment amounts
   - Investor preferences by type
   - Geographic allocation trends

2. **RFP Activity**
   - Recent searches by investor type
   - Popular strategies
   - Fee and terms trends

3. **Market Intelligence**
   - Fundraising statistics
   - Performance benchmarks
   - Industry reports

4. **Dakota Success Stories**
   - Case studies with metrics
   - Client testimonials
   - Best practices

### Content Format Example
```markdown
# Private Equity Allocation Trends Q4 2024

Published: January 5, 2025
Source: Dakota Research Team

## Key Findings

- **Public Pensions**: Increased PE allocation to 15% (up from 12%)
- **Family Offices**: $2.3B committed to growth equity funds
- **RIAs**: Seeking more access to alternative investments

## Allocation by Strategy
- Buyout: 45% of commitments
- Growth Equity: 30%
- Venture Capital: 15%
- Distressed/Special Situations: 10%

## Notable Commitments
- California Public Employees: $500M to XYZ Buyout Fund VI
- Major Endowment: $200M to ABC Growth Partners III

[Source: Dakota Database, January 2025]
```

## Verification

After adding content, verify it's searchable:

```bash
# Test the generation with a related topic
python main_chat.py generate "Latest private equity allocation trends"

# The system should reference your newly added content
```

## Troubleshooting

### Issue: Files not being found in searches
- Ensure files are properly formatted markdown
- Check file size (very large files may be truncated)
- Wait 2-3 minutes for indexing to complete

### Issue: Update script fails
- Verify OPENAI_API_KEY in .env
- Check VECTOR_STORE_ID exists
- Ensure file paths are correct

### Issue: Duplicate content
- The vector store handles duplicates automatically
- Focus on adding new/updated content

## Advanced: Bulk Updates

For large-scale updates, create a staging directory:

```bash
# 1. Create staging area
mkdir kb_staging/

# 2. Copy new content
cp -r new_research/* kb_staging/
cp -r updated_articles/* kb_staging/

# 3. Review content
ls -la kb_staging/

# 4. Add all at once
python update_knowledge_base.py add-dir kb_staging/
```

## Monitoring KB Usage

Check which KB content is being used:

1. Review evidence packs in run outputs
2. Look for "Source: Dakota Knowledge Base" citations
3. Monitor topic generation for KB-aware suggestions

## Remember

- The KB directly impacts article quality and relevance
- Keep content current (especially allocation data)
- Focus on Dakota's target audience needs
- Regular updates ensure competitive advantage

Last Updated: 2025-01-09