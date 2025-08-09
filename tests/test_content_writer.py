#!/usr/bin/env python3
"""Test the content writer agent directly to debug article generation issues."""

import asyncio
from agents import Runner
from src.agents import content_writer
from src.tools.function_tools import write_file

async def test_content_writer():
    """Test the content writer with a focused prompt."""
    
    # Create the agent
    agent = content_writer.create()
    agent.tools.extend([write_file])
    
    # Sample synthesis data
    synthesis = """
    Index funds offer institutional investors significant advantages:
    
    1. Cost Efficiency: Average expense ratio 0.06% vs 0.76% for active funds (Morningstar 2024)
    2. Performance: 90% of active funds underperform their benchmark over 15 years (S&P Dow Jones 2024)
    3. Tax Efficiency: Lower turnover reduces capital gains distributions
    4. Transparency: Holdings are public and updated daily
    5. Scalability: Can invest billions without market impact
    
    Key statistics:
    - $11.8 trillion in index fund assets globally (ICI 2024)
    - 45% of US equity fund assets are now passive (Morningstar)
    - Average annual cost savings: 70 basis points
    
    Dakota articles to reference:
    - "The Rise of Passive Investing" - explores shift from active to passive
    - "Cost Analysis for Institutional Portfolios" - detailed fee comparisons
    - "Building Core Satellite Strategies" - using index funds as portfolio foundation
    """
    
    prompt = f"""You are the Dakota Content Writer. Create a comprehensive Learning Center article.

MANDATORY REQUIREMENTS:
1. Use the EXACT template from your instructions
2. Minimum 1,750 words (this is critical - aim for 2,000+)
3. Include proper YAML frontmatter with ALL fields:
   - title
   - date: 2025-08-09
   - word_count: [actual count]
   - reading_time: [calculate based on 250 words/minute]
4. Include 10+ inline citations using [Source Name](URL) format
5. Follow the section structure EXACTLY as specified

Topic: Benefits of Index Fund Investing for Institutional Investors

Use this research:
{synthesis}

Example URLs to use in citations:
- https://www.morningstar.com/articles/1234567/index-fund-growth
- https://www.spglobal.com/spdji/en/research/article/spiva-us-scorecard
- https://www.ici.org/research/stats/factbook
- https://www.vanguard.com/institutional/insights/index-advantage
- https://www.blackrock.com/institutional/index-investing
- https://www.ssga.com/institutional/etfs/insights/cost-matters
- https://www.fidelity.com/institutional/index-fund-strategies
- https://www.investmentcompany.org/research/passive-trends
- https://www.ft.com/content/institutional-index-adoption
- https://www.wsj.com/articles/index-funds-institutional-growth

Write the COMPLETE article now. Save to: test_article.md"""

    # Run the agent
    print("Testing content writer...")
    result = await Runner.run(agent, prompt)
    
    # Print full output for debugging
    print(f"\nFull agent output:")
    print("=" * 80)
    print(result.final_output)
    print("=" * 80)
    
    # Check the messages for errors
    if result.messages:
        print(f"\nNumber of messages: {len(result.messages)}")
        for i, msg in enumerate(result.messages):
            print(f"\nMessage {i}: {msg.role}")
            if hasattr(msg, 'content') and msg.content:
                print(f"Content preview: {str(msg.content)[:200]}...")
    
    # Check what was written
    import os
    if os.path.exists("test_article.md"):
        with open("test_article.md", "r") as f:
            content = f.read()
            word_count = len(content.split())
            print(f"\nArticle generated:")
            print(f"- Word count: {word_count}")
            print(f"- Has YAML frontmatter: {'---' in content[:10]}")
            print(f"- Has Key Insights: {'Key Insights at a Glance' in content}")
            print(f"- Has Key Takeaways: {'Key Takeaways' in content}")
            print(f"- Citation count: {content.count('](http')}")
    else:
        print("\nNo article file was created!")
        print("Current directory:", os.getcwd())
        print("Files in directory:", os.listdir("."))

if __name__ == "__main__":
    asyncio.run(test_content_writer())