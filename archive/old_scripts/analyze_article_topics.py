#!/usr/bin/env python3
"""
Analyze Learning Center articles to understand topic patterns and create categorization
"""

import json
import re
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any
import os


def load_article_index() -> Dict[str, Dict[str, str]]:
    """Load the article index"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    index_path = os.path.join(project_root, "data", "knowledge_base", "article_index.json")
    
    with open(index_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def categorize_articles(articles: Dict[str, Dict[str, str]]) -> Dict[str, List[str]]:
    """Categorize articles by type, asset class, investor type, and geography"""
    
    categories = {
        "asset_class": defaultdict(list),
        "investor_type": defaultdict(list),
        "content_type": defaultdict(list),
        "geography": defaultdict(list),
        "topic": defaultdict(list)
    }
    
    # Asset class patterns
    asset_patterns = {
        "private_equity": r"private equity|PE\s|buyout|LBO",
        "hedge_funds": r"hedge fund|HF\s",
        "private_credit": r"private credit|private debt|direct lending",
        "real_estate": r"real estate|REIT|property",
        "venture_capital": r"venture capital|VC\s|startup",
        "infrastructure": r"infrastructure|infra\s",
        "commodities": r"commodit|natural resources"
    }
    
    # Investor type patterns
    investor_patterns = {
        "family_office": r"family office|FO\s",
        "ria": r"RIA|registered investment|advisor",
        "pension": r"pension|public plan|retirement",
        "endowment": r"endowment",
        "foundation": r"foundation",
        "insurance": r"insurance|insurer",
        "sovereign_wealth": r"sovereign wealth|SWF",
        "ocio": r"OCIO|outsourced chief"
    }
    
    # Content type patterns
    content_patterns = {
        "ranking": r"top\s+\d+|best\s+\w+|largest",
        "database_guide": r"database|data\s+tool|research tool",
        "market_analysis": r"trend|outlook|forecast|analysis",
        "commitment_summary": r"commitment summary|allocation",
        "conference_guide": r"conference|event|summit",
        "how_to": r"how to|guide|strategy|tips",
        "news_update": r"acquisition|merger|move|update",
        "geographic_guide": r"in\s+\w+\s*$|firms in|offices in"
    }
    
    # Geographic patterns
    geo_patterns = {
        "us_northeast": r"Boston|New York|NYC|Philadelphia|Connecticut|Massachusetts",
        "us_midwest": r"Chicago|Cincinnati|Detroit|Cleveland|Milwaukee",
        "us_south": r"Texas|Florida|Atlanta|Miami|Dallas|Houston",
        "us_west": r"California|Los Angeles|San Francisco|Seattle|Denver",
        "europe": r"Europe|London|Paris|France|Germany|Switzerland|Finland",
        "asia": r"Asia|Hong Kong|Singapore|Japan|China",
        "middle_east": r"Middle East|Dubai|UAE|Saudi",
        "global": r"global|international|worldwide"
    }
    
    # Analyze each article
    for title, info in articles.items():
        title_lower = title.lower()
        
        # Categorize by asset class
        for asset_class, pattern in asset_patterns.items():
            if re.search(pattern, title_lower, re.I):
                categories["asset_class"][asset_class].append(title)
        
        # Categorize by investor type
        for investor_type, pattern in investor_patterns.items():
            if re.search(pattern, title_lower, re.I):
                categories["investor_type"][investor_type].append(title)
        
        # Categorize by content type
        for content_type, pattern in content_patterns.items():
            if re.search(pattern, title_lower, re.I):
                categories["content_type"][content_type].append(title)
        
        # Categorize by geography
        for geo, pattern in geo_patterns.items():
            if re.search(pattern, title, re.I):  # Use original case for geography
                categories["geography"][geo].append(title)
        
        # Extract specific topics
        if "database" in title_lower:
            categories["topic"]["databases"].append(title)
        if "commitment" in title_lower or "allocation" in title_lower:
            categories["topic"]["allocations"].append(title)
        if "trend" in title_lower or "outlook" in title_lower:
            categories["topic"]["market_trends"].append(title)
        if "dakota" in title_lower and ("marketplace" in title_lower or "rainmaker" in title_lower):
            categories["topic"]["dakota_products"].append(title)
    
    return categories


def analyze_patterns(categories: Dict[str, Dict[str, List[str]]]) -> Dict[str, Any]:
    """Analyze patterns in categorized articles"""
    
    analysis = {
        "total_articles": 0,
        "category_counts": {},
        "top_combinations": [],
        "insights": []
    }
    
    # Count total unique articles
    all_titles = set()
    for category_type in categories.values():
        for titles in category_type.values():
            all_titles.update(titles)
    analysis["total_articles"] = len(all_titles)
    
    # Count by category
    for category_name, category_data in categories.items():
        analysis["category_counts"][category_name] = {
            subcat: len(titles) for subcat, titles in category_data.items()
        }
    
    # Find common combinations
    asset_investor_combos = []
    for asset in categories["asset_class"]:
        for investor in categories["investor_type"]:
            # Find articles that match both
            asset_titles = set(categories["asset_class"][asset])
            investor_titles = set(categories["investor_type"][investor])
            overlap = asset_titles & investor_titles
            if overlap:
                asset_investor_combos.append({
                    "combination": f"{asset} + {investor}",
                    "count": len(overlap),
                    "examples": list(overlap)[:3]
                })
    
    analysis["top_combinations"] = sorted(
        asset_investor_combos, 
        key=lambda x: x["count"], 
        reverse=True
    )[:10]
    
    # Generate insights
    content_counts = analysis["category_counts"]["content_type"]
    total_content = sum(content_counts.values())
    
    if total_content > 0:
        ranking_pct = (content_counts.get("ranking", 0) / total_content) * 100
        analysis["insights"].append(
            f"Rankings/Top Lists make up {ranking_pct:.0f}% of content"
        )
    
    # Most covered asset classes
    asset_counts = analysis["category_counts"]["asset_class"]
    if asset_counts:
        top_asset = max(asset_counts.items(), key=lambda x: x[1])
        analysis["insights"].append(
            f"Private Equity is the most covered asset class ({top_asset[1]} articles)"
        )
    
    # Geographic distribution
    geo_counts = analysis["category_counts"]["geography"]
    us_total = sum(v for k, v in geo_counts.items() if k.startswith("us_"))
    intl_total = sum(v for k, v in geo_counts.items() if not k.startswith("us_"))
    if us_total + intl_total > 0:
        us_pct = (us_total / (us_total + intl_total)) * 100
        analysis["insights"].append(
            f"US-focused content: {us_pct:.0f}%, International: {100-us_pct:.0f}%"
        )
    
    return analysis


def save_enhanced_index(articles: Dict, categories: Dict) -> None:
    """Save enhanced article index with categories"""
    
    # Create enhanced index
    enhanced_index = {}
    
    for title, info in articles.items():
        enhanced_entry = info.copy()
        enhanced_entry["categories"] = {
            "asset_class": [],
            "investor_type": [],
            "content_type": [],
            "geography": [],
            "topics": []
        }
        
        # Add categories for this article
        for cat_type, cat_data in categories.items():
            for subcat, titles in cat_data.items():
                if title in titles:
                    if cat_type == "topic":
                        enhanced_entry["categories"]["topics"].append(subcat)
                    else:
                        enhanced_entry["categories"][cat_type].append(subcat)
        
        enhanced_index[title] = enhanced_entry
    
    # Save enhanced index
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    output_path = os.path.join(project_root, "data", "knowledge_base", "article_index_enhanced.json")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(enhanced_index, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Enhanced index saved to: {output_path}")


def main():
    """Analyze articles and create enhanced categorization"""
    
    print("Loading article index...")
    articles = load_article_index()
    print(f"Loaded {len(articles)} articles")
    
    print("\nCategorizing articles...")
    categories = categorize_articles(articles)
    
    print("\nAnalyzing patterns...")
    analysis = analyze_patterns(categories)
    
    # Print analysis results
    print("\n" + "="*60)
    print("LEARNING CENTER ANALYSIS RESULTS")
    print("="*60)
    
    print(f"\nTotal Articles: {analysis['total_articles']}")
    
    print("\n📊 Content Type Distribution:")
    for content_type, count in sorted(analysis["category_counts"]["content_type"].items(), 
                                    key=lambda x: x[1], reverse=True):
        print(f"  - {content_type.replace('_', ' ').title()}: {count}")
    
    print("\n💼 Asset Class Coverage:")
    for asset, count in sorted(analysis["category_counts"]["asset_class"].items(), 
                              key=lambda x: x[1], reverse=True):
        print(f"  - {asset.replace('_', ' ').title()}: {count}")
    
    print("\n👥 Investor Type Coverage:")
    for investor, count in sorted(analysis["category_counts"]["investor_type"].items(), 
                                 key=lambda x: x[1], reverse=True):
        print(f"  - {investor.replace('_', ' ').title()}: {count}")
    
    print("\n🌍 Geographic Distribution:")
    for geo, count in sorted(analysis["category_counts"]["geography"].items(), 
                            key=lambda x: x[1], reverse=True):
        print(f"  - {geo.replace('_', ' ').title()}: {count}")
    
    print("\n🔗 Top Asset Class + Investor Type Combinations:")
    for combo in analysis["top_combinations"][:5]:
        print(f"  - {combo['combination']}: {combo['count']} articles")
    
    print("\n💡 Key Insights:")
    for insight in analysis["insights"]:
        print(f"  - {insight}")
    
    # Save enhanced index
    print("\nSaving enhanced index with categories...")
    save_enhanced_index(articles, categories)
    
    # Save analysis report
    report_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "knowledge_base", "content_analysis_report.json"
    )
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False)
    print(f"✅ Analysis report saved to: {report_path}")


if __name__ == "__main__":
    main()