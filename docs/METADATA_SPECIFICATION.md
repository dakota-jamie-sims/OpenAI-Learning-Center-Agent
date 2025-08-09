# Metadata Specification

## Overview
Every generated article includes a comprehensive `metadata.json` file with real, calculated metrics. This file contains NO mock data - every value is extracted or calculated from actual generation results.

## File Location
```
runs/[timestamp]-[topic]/metadata.json
```

## Data Structure

### 1. Generation Details
```json
{
  "generation": {
    "timestamp": "2025-01-09T14:30:00Z",
    "topic": "Private Equity Allocation Trends",
    "generation_time_seconds": 145.3,
    "iterations": 1,
    "model_configuration": {
      "writer": "gpt-5",
      "fact_checker": "gpt-5",
      "researchers": "gpt-4.1"
    }
  }
}
```

### 2. SEO Information
All SEO data is extracted from the actual article content:
```json
{
  "seo": {
    "title": "2025 Private Equity Allocation Trends: RIAs Lead Growth",
    "description": "Discover how RIAs increased PE allocations by 45% in 2025, with family offices committing $12.3B to growth equity funds.",
    "keywords": {
      "primary": "private equity allocation",
      "secondary": ["RIA investments", "PE allocation trends", "family office PE", "institutional allocations"],
      "related": ["alternative investments", "portfolio allocation", "LP commitments", "fundraising", "Dakota"],
      "long_tail": ["private equity allocation trends 2025", "RIA private equity investments", "family office PE allocation strategy"]
    },
    "slug": "2025-private-equity-allocation-trends-rias-lead-growth",
    "canonical_url": "https://dakota.com/learning-center/2025-private-equity-allocation-trends-rias-lead-growth"
  }
}
```

### 3. Content Metrics
Actual counts from the article:
```json
{
  "content_metrics": {
    "word_count": 2547,
    "character_count": 15234,
    "paragraph_count": 42,
    "sentence_count": 156,
    "reading_time_minutes": 11,
    "reading_level": "professional",
    "sections": {
      "total": 8,
      "h2_count": 6,
      "h3_count": 12
    }
  }
}
```

### 4. Quality Scores
From actual validation results:
```json
{
  "quality_scores": {
    "overall_credibility": 0.92,
    "fact_accuracy": 0.95,
    "source_quality": 8.7,
    "data_freshness": 0.98,
    "readability_score": 45,
    "passive_voice_percentage": 12,
    "average_sentence_length": 16
  }
}
```

### 5. Data Metrics
Counted from article content:
```json
{
  "data_metrics": {
    "statistics_count": 24,
    "citations_count": 18,
    "external_links": 15,
    "internal_links": 3,
    "dakota_references": 3,
    "charts_and_tables": 2,
    "current_year_data_points": 12,
    "average_data_age_days": 22
  }
}
```

### 6. Source Analysis
Parsed from actual citations:
```json
{
  "source_summary": {
    "total_sources": 18,
    "tier_1_sources": 6,
    "tier_2_sources": 9,
    "tier_3_sources": 3,
    "government_sources": 2,
    "academic_sources": 1,
    "industry_sources": 8,
    "unique_domains": 14
  }
}
```

### 7. Cost Analytics
Calculated from actual token usage:
```json
{
  "cost_analytics": {
    "total_tokens": 45678,
    "input_tokens": 32456,
    "output_tokens": 13222,
    "estimated_cost_usd": 1.28,
    "tokens_by_agent": {
      "web_researcher": 8234,
      "kb_researcher": 6543,
      "synthesizer": 9876,
      "writer": 12345,
      "fact_checker": 5432,
      "seo_specialist": 2134,
      "summary_writer": 1114
    }
  }
}
```

### 8. Related Content
Extracted Dakota article references:
```json
{
  "related_content": {
    "dakota_articles": [
      {
        "title": "Q3 2024 Private Equity Commitments",
        "url": "https://dakota.com/learning-center/q3-2024-pe-commitments",
        "relevance_score": 0.9,
        "relationship": "Previous quarter comparison data"
      },
      {
        "title": "Family Office Investment Preferences 2025",
        "url": "https://dakota.com/learning-center/family-office-preferences-2025",
        "relevance_score": 0.85,
        "relationship": "Overlapping investor segment analysis"
      }
    ],
    "topic_clusters": ["private-equity", "allocations", "institutional-investors"],
    "content_series": "Quarterly Allocation Reports"
  }
}
```

## Key Guarantees

### 1. **No Mock Data**
- Every number is calculated from real data
- All URLs are extracted from actual content
- Keywords come from article text analysis
- Dates are parsed from real mentions

### 2. **Accuracy Requirements**
- Word counts exclude markdown formatting
- Token costs use actual API pricing
- Source tiers based on domain analysis
- Reading time includes image/chart allowances

### 3. **Extraction Methods**
- **URLs**: Regex pattern `\[([^\]]+)\]\(([^)]+)\)`
- **Dates**: Multiple format parsing (YYYY-MM-DD, Month DD YYYY, etc.)
- **Keywords**: Frequency analysis and co-occurrence
- **Sections**: Markdown header parsing (`#`, `##`, `###`)

### 4. **Validation Checks**
The metadata generator performs these checks:
- All counts > 0 for required fields
- No placeholder URLs (example.com, etc.)
- Valid JSON structure
- Timestamp formatting
- Cost calculations match token usage

## Usage Examples

### Analytics Dashboard
```python
import json
with open('metadata.json') as f:
    meta = json.load(f)
    
# Track performance metrics
print(f"Generation cost: ${meta['cost_analytics']['estimated_cost_usd']}")
print(f"Quality score: {meta['quality_scores']['overall_credibility']}")
print(f"Data freshness: {meta['quality_scores']['data_freshness']}")
```

### SEO Implementation
```python
# Extract SEO data for CMS
seo = meta['seo']
cms.create_article(
    title=seo['title'],
    description=seo['description'],
    keywords=seo['keywords']['secondary'],
    slug=seo['slug']
)
```

### Content Network Building
```python
# Find related articles
for article in meta['related_content']['dakota_articles']:
    if article['relevance_score'] > 0.8:
        create_internal_link(article['url'], article['relationship'])
```

## Continuous Improvement

The metadata enables:
1. **Cost Optimization**: Track which agents use most tokens
2. **Quality Trends**: Monitor credibility scores over time
3. **SEO Performance**: A/B test different keyword strategies
4. **Content Gaps**: Identify under-connected topic clusters
5. **Efficiency Metrics**: Reduce generation time and iterations

## Integration Points

The metadata.json file is designed for easy integration with:
- Content Management Systems (CMS)
- Analytics platforms
- SEO tools
- Cost tracking systems
- Quality assurance workflows
- Knowledge base updates

Last Updated: 2025-01-09