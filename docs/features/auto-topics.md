# Feature: Auto Topic Generation

## Overview
The system can automatically generate relevant article topics based on current trends and Dakota's focus areas.

## Implementation Details

### 1. **Topic Generation Function**
Location: `main_chat.py`

```python
def generate_topic():
    # Primary: Uses GPT-4 for intelligent generation
    # Fallback: Template-based combination
```

### 2. **AI-Powered Generation**
```python
# Considers:
- Current month/season
- Dakota's audience (institutional investors)
- Focus areas (alternatives, portfolio construction)
- Timeliness and relevance

# Example prompt to GPT-4:
"Generate a highly relevant article topic for Dakota's institutional investor audience.
Consider: Current month: January 2024..."
```

### 3. **Fallback Template System**
Categories:
```python
categories = {
    "Market Trends": ["impact of", "opportunities in", ...],
    "Investment Strategies": ["optimizing", "risk management", ...],
    "Asset Classes": ["private equity", "hedge funds", ...],
    "Current Themes": ["AI in investing", "climate risk", ...]
}

# Generates combinations like:
"The Impact of Rising Interest Rates on Private Equity"
"How AI is Reshaping ESG Investing Strategies"
```

## Usage

### 1. **Auto Topic Generation**
```bash
# Generate article with auto topic
python main_chat.py generate --auto

# With other options
python main_chat.py generate --auto --quick
python main_chat.py generate --auto --words 1000
```

### 2. **Topic Suggestions**
```bash
# Get 5 topic suggestions
python main_chat.py topics

# Output:
1. Private Equity Deployment in Rising Rate Environments
2. Navigating Geopolitical Risk Through Alternatives
3. The Role of AI in Portfolio Construction
4. Infrastructure as an Inflation Hedge
5. ESG Integration in Multi-Asset Strategies
```

### 3. **No Topic Provided**
```bash
# This shows error and examples
python main_chat.py generate

# Error: Please provide a topic or use --auto flag
# Examples:
#   python main_chat.py generate "Your topic"
#   python main_chat.py generate --auto
```

## Topic Categories

### Market Trends
- Impact of rising interest rates
- Navigating volatility
- Future outlooks
- Institutional perspectives

### Investment Strategies  
- Portfolio optimization
- Risk management
- Alpha generation
- Strategy evaluation

### Asset Classes
- Private equity
- Hedge funds
- Real estate (REITs)
- Infrastructure
- ESG investing
- Factor-based strategies

### Current Themes
- Artificial intelligence
- Climate risk
- Geopolitical factors
- Digital assets
- Inflation hedging

## Integration Points

### 1. **Command Line Interface**
```python
@click.argument('topic', required=False)
@click.option('--auto', is_flag=True)

if not topic and not auto:
    # Show error
elif auto or not topic:
    topic = generate_topic()
```

### 2. **Topic Quality**
Generated topics are:
- Specific and actionable
- Relevant to current market
- Aligned with Dakota expertise
- Suitable for target audience

## Examples of Generated Topics

### Timely Topics (January 2024)
- "Strategic Asset Allocation for 2024: Navigating Rate Uncertainty"
- "Private Credit Opportunities in a Higher-for-Longer Environment"
- "The Evolution of ESG Integration in Alternative Investments"

### Evergreen Topics
- "Building Resilient Portfolios with Alternative Assets"
- "The Role of Infrastructure in Institutional Portfolios"
- "Hedge Fund Selection in Modern Portfolio Construction"

## Configuration

### Customizing Categories
Edit in `main_chat.py`:
```python
categories = {
    "Your Category": ["prefixes..."],
    "Asset Classes": ["your assets..."],
    "Themes": ["your themes..."]
}
```

### Adjusting AI Prompt
Modify the prompt to focus on specific areas:
```python
prompt = f"""Generate topic for Dakota...
Focus specifically on: private markets, alternatives
Avoid: retail investing, crypto speculation
"""
```

## Best Practices

### 1. **Review Generated Topics**
- AI suggestions are usually good
- But always review for appropriateness
- Ensure alignment with Dakota values

### 2. **Seasonal Relevance**
Topics consider current month:
- Q1: Year ahead outlooks
- Q2: Mid-year adjustments
- Q3: Positioning for year-end
- Q4: Tax and planning topics

### 3. **Audience Alignment**
All topics target:
- Institutional investors
- Family offices
- RIAs
- Sophisticated advisors

## Troubleshooting

### "Topics seem generic"
- Check if OpenAI API is accessible
- Fallback templates may be active
- Try running multiple times

### "Want specific focus area"
Currently auto-generation is broad. For specific areas:
```bash
# Manually specify
python main_chat.py generate "Private Equity Secondary Markets"
```

## Future Enhancements
- Topic categories configuration
- Historical topic tracking
- Trend analysis integration
- User preference learning
- Seasonal topic queues