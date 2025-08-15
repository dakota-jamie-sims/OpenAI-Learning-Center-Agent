#!/usr/bin/env python3
"""
Test the system without OpenAI API calls
Creates a mock article with proper sources to verify the system works
"""
import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "src"))

from src.utils.files import run_dir_for_topic, write_text
from src.tools.fact_verification import EnhancedFactChecker
import asyncio
from datetime import datetime

async def test_system_without_api():
    """Test the validation system with a mock article"""
    
    topic = "Top Family Offices in Texas | 2025 Investment Guide"
    run_dir, slug = run_dir_for_topic("output", topic)
    article_path = os.path.join(run_dir, f"{slug[:30]}.md" if len(slug) > 30 else f"{slug}.md")
    
    # Create a mock article with proper citations
    mock_article = """---
title: Top Family Offices in Texas | 2025 Investment Guide
date: 2025-08-09
word_count: 2150
reading_time: 10 minutes
---

# Top Family Offices in Texas | 2025 Investment Guide

Texas has emerged as a powerhouse for family office formation and growth, with the state now home to over 450 family offices managing collective assets exceeding $312 billion ([Texas Finance Commission, January 2025](https://www.tfc.state.tx.us/family-office-report-2025.pdf)). This remarkable growth represents a 28% increase from 2023, driven by favorable tax policies, a thriving business environment, and an influx of ultra-high-net-worth individuals relocating from higher-tax states.

The Lone Star State's family office ecosystem has evolved dramatically, with sophisticated investment strategies and increasing allocations to alternative assets. According to recent data from Preqin ([Preqin Texas Family Office Study, Q1 2025](https://www.preqin.com/insights/research/reports/texas-family-office-q1-2025)), Texas family offices allocated an average of 42% of their portfolios to alternatives in 2024, compared to the national average of 35%.

## Key Insights at a Glance
- Texas family offices manage over $312 billion in collective assets ([Texas Finance Commission, January 2025](https://www.tfc.state.tx.us/family-office-report-2025.pdf))
- Average portfolio allocation to alternatives: 42% vs 35% national average ([Preqin, Q1 2025](https://www.preqin.com/insights/research/reports/texas-family-office-q1-2025))
- 187 new family offices established in Texas in 2024 ([Bloomberg, December 2024](https://www.bloomberg.com/news/articles/2024-12-28/texas-family-office-boom))
- Energy transition investments account for 18% of Texas family office portfolios ([PitchBook, January 2025](https://pitchbook.com/news/reports/2025-01-texas-energy-transition))

## The Top 10 Family Offices Reshaping Texas Wealth Management

### 1. Hunt Family Office (Dallas)
The Hunt family, with roots in oil and real estate, manages approximately $15 billion through their sophisticated multi-family office structure ([Forbes Billionaires List, 2025](https://www.forbes.com/billionaires-2025/hunt-family)). Their recent pivot toward renewable energy investments has caught industry attention, with $2.3 billion allocated to solar and wind projects in 2024 alone ([Reuters, January 2025](https://www.reuters.com/business/energy/hunt-family-renewable-push-2025-01-10/)).

### 2. Dell Family Office (Austin) 
Michael Dell's family office, MSD Capital, continues to be one of the most active investors in the technology and real estate sectors. With assets under management exceeding $16 billion ([SEC Form ADV, March 2025](https://www.sec.gov/Archives/edgar/data/msd-capital/000119312525012345/form-adv.htm)), MSD has increasingly focused on early-stage technology investments, participating in 47 funding rounds in 2024.

### Investment Strategies and Allocation Trends

Texas family offices have demonstrated a sophisticated approach to portfolio construction, with a notable shift toward alternative investments. The average allocation breakdown reveals:
- Private equity: 22% ([Cambridge Associates, Q4 2024](https://www.cambridgeassociates.com/insight/texas-family-office-allocation-study-q4-2024/))
- Real estate: 18% (including significant energy infrastructure exposure)
- Hedge funds: 12% 
- Venture capital: 8%
- Traditional equities: 28%
- Fixed income: 12%

This allocation strategy has yielded impressive results, with Texas family offices reporting average returns of 14.7% in 2024, outperforming the S&P 500's 11.2% return ([Texas Family Office Association Annual Report, February 2025](https://www.texasfamilyoffices.org/2025-annual-report)).

### Regulatory Environment and Tax Advantages

The favorable regulatory environment in Texas continues to attract family offices from across the nation. With no state income tax and business-friendly policies, Texas offers significant advantages for wealth preservation. The recent passage of House Bill 1842 in January 2025 ([Texas Legislature, HB 1842](https://capitol.texas.gov/BillLookup/History.aspx?LegSess=89R&Bill=HB1842)) further enhanced privacy protections for family offices, making the state even more attractive for ultra-high-net-worth families.

### Ready to Connect with Texas Family Offices?

**Unlock Access to Elite Investment Opportunities**
Dakota's comprehensive database includes detailed profiles on over 450 Texas family offices, complete with investment preferences, contact information, and recent allocation data. Join 1,400+ investment firms already leveraging Dakota's intelligence.
[Explore Dakota Marketplace →]

### Related Dakota Learning Center Articles
*For more insights on this topic, explore these related articles:*
- [Top 10 Family Offices in California](https://dakota.com/learning-center/top-10-family-offices-in-california) - Compare West Coast family office strategies
- [The Growth of Family Offices](https://dakota.com/learning-center/the-growth-of-family-offices) - Understand the macro trends driving family office formation
- [Family Office Investment Strategies](https://dakota.com/learning-center/family-office-investment-strategies-2025) - Deep dive into allocation models
"""
    
    # Write the mock article
    write_text(article_path, mock_article)
    print(f"✅ Created mock article at: {article_path}")
    
    # Test the validation system
    print("\n🔍 Testing enhanced fact verification...")
    print(f"Topic: {topic}")
    fact_checker = EnhancedFactChecker(topic, 2150)  # Use actual word count
    print(f"Detected config type: {'LOCATION_BASED' if 'top' in topic.lower() else 'OTHER'}")
    print(f"Validation config: {fact_checker.validation_config}")
    result = await fact_checker.verify_article(mock_article)
    
    print(f"\n📊 Validation Results:")
    print(f"- Approved: {'✅ YES' if result['approved'] else '❌ NO'}")
    print(f"- Credibility Score: {result['credibility_score']:.2%}")
    print(f"- Fact Accuracy: {result['fact_accuracy']:.2%}")
    print(f"- Total Facts Checked: {result['total_facts_checked']}")
    print(f"- Verified Facts: {result['verified_facts']}")
    print(f"- Source Quality: {result['source_quality']:.1f}/10")
    
    # Debug: print fact details
    if 'detailed_results' in result and 'verification_details' in result['detailed_results']:
        print(f"\n🔍 Facts Analyzed:")
        for i, fact_result in enumerate(result['detailed_results']['verification_details'][:3]):
            fact = fact_result['fact']
            print(f"{i+1}. Type: {fact['type']}, Claim: {fact['claim']}")
            print(f"   Has Citation: {fact['has_citation']}, Verified: {fact_result['verified']}")
    
    # Debug: print source analysis
    if 'source_analysis' in result:
        print(f"\n📊 Source Analysis:")
        print(f"- Total sources: {result['source_analysis']['total_sources']}")
        print(f"- Average credibility: {result['source_analysis']['average_credibility']:.1f}")
        if 'domain_distribution' in result['source_analysis']:
            print(f"- Domains found: {list(result['source_analysis']['domain_distribution'].keys())}")
    
    if result['issues']:
        print(f"\n⚠️ Issues Found:")
        for issue in result['issues']:
            print(f"  - {issue}")
    else:
        print(f"\n✨ No issues found! Article passes all validation checks.")
    
    # Debug approval logic
    print(f"\n🔍 Approval Logic Debug:")
    print(f"- Min credibility required: 60%")
    print(f"- Min fact accuracy required: 75%")
    print(f"- Has recent data: {result.get('data_freshness', {}).get('has_recent_data', False)}")
    print(f"- Freshness check passed: {not fact_checker.validation_config['require_current_year_data'] or result.get('data_freshness', {}).get('has_recent_data', True)}")
    print(f"- Validation config: {fact_checker.validation_config['require_current_year_data']}")
    
    # Create metadata
    metadata_path = os.path.join(run_dir, "metadata.md")
    metadata = f"""# Article Metadata

## Generation Details
- **Topic**: {topic}
- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Generation Time**: 0.1 seconds (mock)
- **Iterations**: 0 (mock article)

## Related Dakota Learning Center Articles
- **Total Related Articles**: 3
- **Related Articles**:
  1. Top 10 Family Offices in California - https://dakota.com/learning-center/top-10-family-offices-in-california
     - **Relevance**: Comparison of family office landscapes across major states
     - **Key Connection**: Investment strategy similarities and differences
  2. The Growth of Family Offices - https://dakota.com/learning-center/the-growth-of-family-offices
     - **Relevance**: Context for Texas family office growth trends
     - **Key Connection**: National trends reflected in Texas market
  3. Family Office Investment Strategies - https://dakota.com/learning-center/family-office-investment-strategies-2025
     - **Relevance**: Deep dive into allocation strategies used by Texas offices
     - **Key Connection**: Alternative investment approaches

## Content Metrics
- **Word Count**: 2,150
- **Sources**: 15
- **Reading Time**: 10 minutes
"""
    
    write_text(metadata_path, metadata)
    print(f"\n📄 Created metadata at: {metadata_path}")
    
    # Create social media content with Instagram
    social_path = os.path.join(run_dir, "social.md")
    social_content = """# Social Media Promotion Pack

## LinkedIn Posts (3 Variations)

### Professional Insight Version
Texas family offices now manage over $312 billion in assets, with 42% allocated to alternatives. 📊

Our latest analysis reveals how 187 new family offices established in Texas last year are reshaping wealth management through sophisticated strategies and energy transition investments.

Key finding: Texas family offices outperformed the S&P 500 by 3.5% in 2024.

Read our comprehensive guide: Top 10 Family Offices in Texas →

#FamilyOffices #TexasInvesting #AlternativeInvestments #WealthManagement

## Instagram Posts (3)

### Post 1: Hero Statistic
**Visual**: Eye-catching graphic with "$312 BILLION" prominently displayed
**Caption**: 
Texas family offices manage a staggering $312 billion in assets! 📊

That's more than the GDP of many countries. Our new report reveals how these ultra-wealthy families are investing differently than traditional institutions.

42% in alternatives vs. 35% national average? There's a Texas-sized opportunity here.

🔗 Full analysis in bio
.
.
.
#FamilyOffices #TexasWealth #AlternativeAssets #InstitutionalInvesting #WealthManagement #PrivateEquity #InvestmentStrategy #HighNetWorth

### Post 2: Key Insights Carousel
**Visual**: 5-slide carousel
- Slide 1: "Top 10 Texas Family Offices"
- Slides 2-4: Key statistics and insights
- Slide 5: CTA to read full article

**Caption**:
What makes Texas the fastest-growing family office hub in America? 🎯

Here's what institutional investors need to know:

1️⃣ 187 new family offices in 2024 alone
2️⃣ 18% allocated to energy transition investments  
3️⃣ Average returns of 14.7% (vs S&P 500's 11.2%)

The Texas advantage isn't just about taxes anymore.

👉 Swipe for insights | Full article link in bio

#AlternativeInvestments #FamilyOfficeInvesting #TexasBusiness #EnergyTransition #InvestmentTrends

### Post 3: Takeaway Quote
**Visual**: Branded quote card
**Caption**:
"Texas family offices allocated 42% to alternatives in 2024, compared to 35% nationally" 💡

This isn't just a statistic - it's a blueprint for sophisticated wealth management.

What's driving this allocation gap? Our latest research uncovers the strategies behind Texas's outperformance.

Ready to learn from the best? Drop a 🤠 below!

📖 Read the complete analysis (link in bio)

#InvestmentWisdom #MarketInsights #FamilyOfficeStrategy #TexasInvesting #DakotaLearningCenter
"""
    
    write_text(social_path, social_content)
    print(f"📱 Created social media content (with Instagram) at: {social_path}")
    
    print(f"\n✅ Complete test successful! All files created in: {run_dir}")
    return result['approved']

if __name__ == "__main__":
    success = asyncio.run(test_system_without_api())
    if success:
        print("\n🎉 System validation PASSED! The article meets all requirements.")
    else:
        print("\n❌ System validation FAILED. Check the issues above.")