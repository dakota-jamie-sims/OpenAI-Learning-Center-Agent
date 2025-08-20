# Adding Articles to Learning Center Knowledge Base

## Overview
The Learning Center articles are stored in the `knowledge_base/learning_center/` directory. These articles serve as reference material for the AI system when generating new content, helping it understand Dakota's style, focus areas, and existing coverage.

## Methods to Add Learning Center Articles

### Method 1: Add Individual Article Files
If you have new articles as separate files:

```bash
# Add specific article files
python update_knowledge_base.py add path/to/new-article1.md path/to/new-article2.md

# Example:
python update_knowledge_base.py add ~/Downloads/2025-01-pe-trends.md ~/Downloads/2025-01-ria-outlook.md
```

### Method 2: Add Articles from a Directory
If you have multiple articles in a folder:

```bash
# Add all markdown files from a directory
python update_knowledge_base.py add-dir ~/Downloads/new-articles/

# Add only .md files (if directory has other formats)
python update_knowledge_base.py add-dir ~/Downloads/articles/ --extensions .md
```

### Method 3: Place Files Directly in Knowledge Base
1. Copy your article files to the Learning Center directory:
```bash
# Copy individual files
cp new-article.md knowledge_base/learning_center/

# Copy multiple files
cp ~/Downloads/january-2025-articles/*.md knowledge_base/learning_center/
```

2. Then update the vector store:
```bash
# Add the entire learning_center directory (including new files)
python update_knowledge_base.py add-dir knowledge_base/learning_center/
```

## Article Format Requirements

### Recommended Structure
Articles should follow this format for best results:

```markdown
# Article Title

Published: January 9, 2025
Author: Dakota Research Team
Category: Private Equity / RIA Channel / Market Intelligence

## Key Takeaways
- Bullet point 1
- Bullet point 2
- Bullet point 3

## Introduction
Brief introduction paragraph...

## Main Content Sections
### Section 1
Content...

### Section 2
Content...

## Conclusion
Summary and call to action...

## Sources
- [Source 1 Title, Date](URL)
- [Source 2 Title, Date](URL)

---
Tags: private-equity, allocations, ria, family-offices
```

### File Naming Convention
Use descriptive, dated filenames:
- `2025-01-09-private-equity-allocation-trends.md`
- `2025-01-ria-ma-activity-report.md`
- `2025-q1-family-office-investment-preferences.md`

## Bulk Import from Article Generation

If you've been generating articles with the system and want to add them back to the knowledge base:

```bash
# Find all generated articles
find runs/ -name "*-article.md" -type f

# Copy them to a staging directory
mkdir article_import/
find runs/ -name "*-article.md" -exec cp {} article_import/ \;

# Review and clean filenames
cd article_import/
# Rename files to remove timestamps if needed

# Add all to knowledge base
cd ..
python update_knowledge_base.py add-dir article_import/
```

## JSON Article Format
The existing articles are in JSON format. To add new JSON articles:

1. Create JSON file with this structure:
```json
{
  "title": "Your Article Title",
  "published_date": "2025-01-09",
  "author": "Dakota Team",
  "category": "Private Equity",
  "content": {
    "introduction": "...",
    "sections": [
      {
        "heading": "Section Title",
        "content": "..."
      }
    ],
    "conclusion": "...",
    "key_takeaways": ["Point 1", "Point 2"],
    "sources": [
      {"title": "Source Name", "url": "https://..."}
    ]
  },
  "tags": ["private-equity", "allocations"],
  "meta": {
    "word_count": 2500,
    "reading_time": "10 minutes"
  }
}
```

2. Save with sequential numbering:
```bash
# Find the highest article number
ls knowledge_base/learning_center/article_*.json | tail -1

# Save your new article with next number
cp new_article.json knowledge_base/learning_center/article_397_your-title.json
```

3. Update vector store:
```bash
python update_knowledge_base.py add knowledge_base/learning_center/article_397_your-title.json
```

## Best Practices

### 1. **Content Quality**
- Ensure articles are final, edited versions
- Include publication dates
- Verify all statistics and sources
- Remove any internal/confidential information

### 2. **Avoid Duplicates**
- Check if similar articles already exist
- Update existing articles rather than adding near-duplicates
- Use descriptive titles to prevent confusion

### 3. **Categorization**
Include clear categories in your articles:
- Private Equity
- RIA Channel
- Family Offices
- Market Intelligence
- Fundraising Strategy
- Alternative Investments

### 4. **Metadata**
Always include:
- Publication date
- Author/source
- Key takeaways
- Relevant tags

## Verification

After adding articles, verify they're accessible:

```bash
# List vector store contents
python update_knowledge_base.py list

# Test with related topic generation
python main_chat.py generate "Topic related to your new article"

# Check if the new content is referenced
# Look in the evidence-pack.json for your article citations
```

## Maintenance

### Regular Updates
- **Monthly**: Add new market reports and insights
- **Quarterly**: Review and update existing articles
- **Annually**: Archive outdated content

### Archive Old Content
Instead of deleting, move outdated articles to an archive:
```bash
mkdir knowledge_base/archive/
mv knowledge_base/learning_center/old-article.md knowledge_base/archive/
```

## Quick Reference Commands

```bash
# Add single article
python update_knowledge_base.py add article.md

# Add multiple articles
python update_knowledge_base.py add article1.md article2.md article3.md

# Add directory of articles
python update_knowledge_base.py add-dir new_articles/

# Add to specific subfolder then update
cp *.md knowledge_base/learning_center/
python update_knowledge_base.py add-dir knowledge_base/learning_center/

# Check what's in vector store
python update_knowledge_base.py list | grep -i "learning center"
```

## Important Notes

1. **No Need to Recreate**: The update script adds to the existing vector store without recreating it
2. **Automatic Indexing**: New content is automatically indexed and searchable
3. **Immediate Availability**: Articles are available for reference as soon as they're added
4. **Quality Matters**: The AI learns from these articles, so ensure high quality

Last Updated: 2025-01-09