"""
Sophisticated article matching algorithm for finding related Learning Center articles
"""

import json
import os
from typing import Dict, List, Tuple, Set
from difflib import SequenceMatcher
import re


class ArticleMatcher:
    """Matches articles based on multiple relevance factors"""
    
    def __init__(self):
        self.enhanced_index = self._load_enhanced_index()
        self.weights = {
            "asset_class": 0.3,
            "investor_type": 0.25,
            "content_type": 0.15,
            "geography": 0.15,
            "topics": 0.15
        }
    
    def _load_enhanced_index(self) -> Dict[str, Dict]:
        """Load the enhanced article index with categories"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            index_path = os.path.join(project_root, "data", "knowledge_base", "article_index_enhanced.json")
            
            if os.path.exists(index_path):
                with open(index_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Fallback to regular index
                index_path = os.path.join(project_root, "data", "knowledge_base", "article_index.json")
                if os.path.exists(index_path):
                    with open(index_path, 'r', encoding='utf-8') as f:
                        basic_index = json.load(f)
                        # Convert to enhanced format
                        return {
                            title: {
                                **info,
                                "categories": {
                                    "asset_class": [],
                                    "investor_type": [],
                                    "content_type": [],
                                    "geography": [],
                                    "topics": []
                                }
                            }
                            for title, info in basic_index.items()
                        }
        except Exception as e:
            print(f"Error loading enhanced index: {e}")
            return {}
    
    def extract_topic_features(self, topic: str) -> Dict[str, Set[str]]:
        """Extract features from a topic string"""
        topic_lower = topic.lower()
        features = {
            "asset_class": set(),
            "investor_type": set(),
            "content_type": set(),
            "geography": set(),
            "topics": set()
        }
        
        # Asset class detection
        asset_keywords = {
            "private_equity": ["private equity", "pe ", "buyout", "lbo"],
            "hedge_funds": ["hedge fund", "hf "],
            "private_credit": ["private credit", "private debt", "direct lending"],
            "real_estate": ["real estate", "reit", "property"],
            "venture_capital": ["venture capital", "vc ", "startup"],
            "infrastructure": ["infrastructure"],
            "commodities": ["commodit", "natural resources"]
        }
        
        for asset, keywords in asset_keywords.items():
            if any(kw in topic_lower for kw in keywords):
                features["asset_class"].add(asset)
        
        # Investor type detection
        investor_keywords = {
            "family_office": ["family office", "fo "],
            "ria": ["ria", "registered investment", "advisor"],
            "pension": ["pension", "public plan", "retirement"],
            "endowment": ["endowment"],
            "foundation": ["foundation"],
            "insurance": ["insurance", "insurer"],
            "sovereign_wealth": ["sovereign wealth", "swf"],
            "ocio": ["ocio", "outsourced chief"]
        }
        
        for investor, keywords in investor_keywords.items():
            if any(kw in topic_lower for kw in keywords):
                features["investor_type"].add(investor)
        
        # Content type hints
        if any(word in topic_lower for word in ["trend", "outlook", "forecast", "analysis"]):
            features["content_type"].add("market_analysis")
        if any(word in topic_lower for word in ["guide", "how to", "strategy"]):
            features["content_type"].add("how_to")
        if any(word in topic_lower for word in ["database", "tool", "platform"]):
            features["content_type"].add("database_guide")
        
        # Geographic detection
        if "emerging market" in topic_lower or "em " in topic_lower:
            features["geography"].add("global")
        if any(word in topic_lower for word in ["us", "america", "united states"]):
            features["geography"].add("us_general")
        
        # Topic keywords
        if "manager" in topic_lower:
            features["topics"].add("manager_selection")
        if "allocation" in topic_lower or "portfolio" in topic_lower:
            features["topics"].add("allocations")
        if "trend" in topic_lower or "2025" in topic or "2024" in topic:
            features["topics"].add("market_trends")
        
        return features
    
    def calculate_similarity_score(self, features1: Dict[str, Set[str]], 
                                 features2: Dict[str, List[str]]) -> float:
        """Calculate weighted similarity score between topic features and article categories"""
        total_score = 0.0
        
        for category, weight in self.weights.items():
            set1 = features1.get(category, set())
            list2 = features2.get(category, [])
            set2 = set(list2)
            
            if set1 and set2:
                # Calculate Jaccard similarity
                intersection = len(set1 & set2)
                union = len(set1 | set2)
                similarity = intersection / union if union > 0 else 0
                total_score += similarity * weight
            elif not set1 and not set2:
                # Both empty - neutral match
                total_score += 0.5 * weight
        
        return total_score
    
    def find_related_articles(self, topic: str, exclude_title: str = None, 
                            max_results: int = 5) -> List[Dict[str, any]]:
        """Find related articles for a given topic"""
        
        # Extract features from the topic
        topic_features = self.extract_topic_features(topic)
        
        # Score all articles
        article_scores = []
        
        for title, info in self.enhanced_index.items():
            # Skip if it's the article we're finding related articles for
            if exclude_title and title == exclude_title:
                continue
            
            # Get article categories
            article_categories = info.get("categories", {})
            
            # Calculate similarity score
            similarity_score = self.calculate_similarity_score(
                topic_features, article_categories
            )
            
            # Add title similarity bonus
            title_similarity = SequenceMatcher(None, topic.lower(), title.lower()).ratio()
            combined_score = similarity_score * 0.7 + title_similarity * 0.3
            
            article_scores.append({
                "title": title,
                "url": info.get("url", ""),
                "description": info.get("description", "")[:150] + "...",
                "score": combined_score,
                "matching_categories": {
                    cat: list(set(topic_features.get(cat, set())) & 
                             set(article_categories.get(cat, [])))
                    for cat in self.weights.keys()
                }
            })
        
        # Sort by score and return top results
        article_scores.sort(key=lambda x: x["score"], reverse=True)
        
        # Filter to ensure diversity in results
        selected = []
        seen_patterns = set()
        
        for article in article_scores:
            # Create a pattern from the article's main features
            pattern = tuple(sorted([
                cat for cat, matches in article["matching_categories"].items() 
                if matches
            ]))
            
            # Skip if we've seen this exact pattern unless we need more results
            if pattern in seen_patterns and len(selected) >= 3:
                continue
            
            selected.append(article)
            seen_patterns.add(pattern)
            
            if len(selected) >= max_results:
                break
        
        return selected
    
    def get_topic_recommendations(self, current_market_trends: List[str] = None) -> List[Dict[str, str]]:
        """Generate topic recommendations based on content gaps and market trends"""
        
        # Analyze current coverage
        coverage_analysis = self._analyze_coverage_gaps()
        
        # Generate recommendations
        recommendations = []
        
        # Gap-based recommendations
        for gap in coverage_analysis["gaps"][:5]:
            recommendations.append({
                "topic": gap["suggested_topic"],
                "rationale": gap["rationale"],
                "priority": "high",
                "category": gap["category"]
            })
        
        # Trend-based recommendations if provided
        if current_market_trends:
            for trend in current_market_trends[:3]:
                recommendations.append({
                    "topic": f"{trend} - Implications for Institutional Investors",
                    "rationale": f"Current market focus on {trend}",
                    "priority": "high",
                    "category": "market_analysis"
                })
        
        # Seasonal/timely recommendations
        import datetime
        current_month = datetime.datetime.now().month
        current_year = datetime.datetime.now().year
        
        if current_month in [1, 2]:
            recommendations.append({
                "topic": f"{current_year} Investment Outlook - Key Themes for Allocators",
                "rationale": "Annual outlook content for new year planning",
                "priority": "high",
                "category": "market_analysis"
            })
        elif current_month in [11, 12]:
            recommendations.append({
                "topic": f"Year-End Tax Strategies for Family Offices and RIAs",
                "rationale": "Timely tax planning content",
                "priority": "medium",
                "category": "how_to"
            })
        
        return recommendations
    
    def _analyze_coverage_gaps(self) -> Dict[str, List[Dict[str, str]]]:
        """Analyze content gaps in current article coverage"""
        
        # Count current coverage
        asset_coverage = {}
        investor_coverage = {}
        combo_coverage = {}
        
        for title, info in self.enhanced_index.items():
            cats = info.get("categories", {})
            
            # Count asset classes
            for asset in cats.get("asset_class", []):
                asset_coverage[asset] = asset_coverage.get(asset, 0) + 1
            
            # Count investor types
            for investor in cats.get("investor_type", []):
                investor_coverage[investor] = investor_coverage.get(investor, 0) + 1
            
            # Count combinations
            for asset in cats.get("asset_class", []):
                for investor in cats.get("investor_type", []):
                    combo = f"{asset}_{investor}"
                    combo_coverage[combo] = combo_coverage.get(combo, 0) + 1
        
        # Identify gaps
        gaps = []
        
        # Asset class gaps
        all_assets = ["private_equity", "hedge_funds", "private_credit", 
                      "real_estate", "venture_capital", "infrastructure"]
        for asset in all_assets:
            if asset_coverage.get(asset, 0) < 5:  # Threshold for "under-covered"
                gaps.append({
                    "category": "asset_class",
                    "gap": asset,
                    "current_coverage": asset_coverage.get(asset, 0),
                    "suggested_topic": f"{asset.replace('_', ' ').title()} Strategies for 2025",
                    "rationale": f"Only {asset_coverage.get(asset, 0)} articles on {asset.replace('_', ' ')}"
                })
        
        # Investor type gaps
        all_investors = ["family_office", "ria", "pension", "endowment", 
                        "foundation", "insurance", "sovereign_wealth", "ocio"]
        for investor in all_investors:
            if investor_coverage.get(investor, 0) < 10:
                gaps.append({
                    "category": "investor_type",
                    "gap": investor,
                    "current_coverage": investor_coverage.get(investor, 0),
                    "suggested_topic": f"Top {investor.replace('_', ' ').title()} Investment Trends",
                    "rationale": f"Limited coverage of {investor.replace('_', ' ')} perspectives"
                })
        
        # Sort gaps by severity (least coverage first)
        gaps.sort(key=lambda x: x["current_coverage"])
        
        return {"gaps": gaps, "combo_coverage": combo_coverage}


# Example usage
if __name__ == "__main__":
    matcher = ArticleMatcher()
    
    # Test finding related articles
    test_topic = "private credit emerging managers"
    related = matcher.find_related_articles(test_topic, max_results=3)
    
    print(f"\nRelated articles for '{test_topic}':")
    for i, article in enumerate(related, 1):
        print(f"\n{i}. {article['title']}")
        print(f"   Score: {article['score']:.3f}")
        print(f"   URL: {article['url']}")
        print(f"   Matching: {article['matching_categories']}")
    
    # Test topic recommendations
    print("\n\nTopic Recommendations:")
    recommendations = matcher.get_topic_recommendations(
        current_market_trends=["AI in Investment Management", "ESG Integration"]
    )
    
    for i, rec in enumerate(recommendations[:5], 1):
        print(f"\n{i}. {rec['topic']}")
        print(f"   Rationale: {rec['rationale']}")
        print(f"   Priority: {rec['priority']}")
        print(f"   Category: {rec['category']}")