"""
Enhanced Topic Generator that leverages Knowledge Base
"""
import random
from datetime import datetime
from typing import List, Dict, Any
from openai import OpenAI
import asyncio
from ..tools.vector_store_handler import VectorStoreHandler, KnowledgeBaseSearchTool
from ..config import settings


class EnhancedTopicGenerator:
    """Generate topics informed by knowledge base content"""
    
    def __init__(self):
        self.client = OpenAI()
        self.vector_handler = VectorStoreHandler(self.client)
        if settings.VECTOR_STORE_ID:
            self.vector_handler.vector_store_id = settings.VECTOR_STORE_ID
        self.kb_search = KnowledgeBaseSearchTool(self.vector_handler)
    
    async def analyze_knowledge_base_themes(self) -> Dict[str, Any]:
        """Analyze knowledge base to identify gaps and trending themes"""
        
        # Search for recent topics and themes
        searches = [
            "recent market trends 2024 2025",
            "emerging investment strategies",
            "institutional investor concerns",
            "alternative investments developments",
            "portfolio construction innovations",
            "risk management evolution"
        ]
        
        themes = {
            "covered_topics": [],
            "emerging_themes": [],
            "knowledge_gaps": [],
            "trending_areas": []
        }
        
        for search_query in searches:
            results = await self.kb_search.search(search_query, max_results=5)
            # Analyze results to extract themes
            themes["covered_topics"].append(results)
        
        return themes
    
    async def generate_topic_with_kb_context(self) -> str:
        """Generate topic that leverages knowledge base insights"""
        
        # Get current month/season for relevance
        month = datetime.now().strftime("%B %Y")
        
        # Analyze knowledge base
        kb_themes = await self.analyze_knowledge_base_themes()
        
        prompt = f"""Generate a highly relevant article topic for Dakota's institutional investor audience.
        
Current Context:
- Month: {month}
- Audience: Institutional investors, family offices, RIAs
- Focus: Actionable insights, data-driven analysis

Knowledge Base Analysis:
- Recently covered topics in our knowledge base include themes around alternative investments, ESG, and market volatility
- Identify gaps or emerging areas not yet deeply covered
- Build on existing Dakota expertise while exploring new angles

Topic Requirements:
1. Must be timely and relevant to current market conditions
2. Should leverage Dakota's expertise but explore new perspectives
3. Provide actionable value to institutional investors
4. Be specific enough to enable deep research
5. Consider emerging trends and future implications

Generate ONE specific topic that would add unique value to Dakota's knowledge base.
Format: Just the topic title, no explanation."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4.1",  # Using your specified model
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=50
            )
            
            topic = response.choices[0].message.content.strip().strip('"')
            
            # Verify topic is not too similar to existing content
            similarity_check = await self.kb_search.search(topic, max_results=3)
            
            # If too similar, regenerate with explicit instruction to differentiate
            if "highly relevant" in similarity_check.lower():
                prompt += "\n\nIMPORTANT: The topic should explore an angle NOT already covered in our knowledge base."
                response = self.client.chat.completions.create(
                    model="gpt-4.1",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.9,
                    max_tokens=50
                )
                topic = response.choices[0].message.content.strip().strip('"')
            
            return topic
            
        except Exception as e:
            # Fallback to enhanced template generation
            return self.generate_fallback_topic()
    
    def generate_fallback_topic(self) -> str:
        """Enhanced fallback topic generation"""
        
        # Enhanced categories with Dakota focus and 2024-2025 trends
        current_themes = {
            "Allocation Trends": [
                "public pension funds increasing alternatives exposure",
                "RIA consolidation creating new allocation opportunities",
                "family office direct investment strategies",
                "endowment portfolio construction in volatile markets",
                "OCIO selection criteria and performance benchmarks"
            ],
            "Fundraising Dynamics": [
                "navigating extended due diligence timelines",
                "co-investment opportunities driving LP interest",
                "fee compression strategies for emerging managers",
                "building relationships with new foundation CIOs",
                "virtual roadshow best practices post-pandemic"
            ],
            "Asset Class Focus": [
                "private equity secondaries market heating up",
                "infrastructure debt attracting insurance companies",
                "real estate allocation shifts in major metros",
                "venture capital access for smaller institutions",
                "hedge fund strategies gaining pension interest"
            ],
            "Investor Preferences": [
                "ESG integration requirements by investor type",
                "liquidity preferences across institutional channels",
                "geographic allocation mandates shifting",
                "emerging manager programs gaining momentum",
                "specialized strategies for healthcare systems"
            ],
            "Market Intelligence": [
                "Q1 2025 allocation activity trends",
                "RFP pipeline analysis by asset class",
                "consultant recommendations driving flows",
                "public fund meeting outcomes and implications",
                "fee study insights for competitive positioning"
            ]
        }
        
        # Select random theme and category
        category = random.choice(list(current_themes.keys()))
        theme = random.choice(current_themes[category])
        
        # Add timely modifiers with fundraising focus
        modifiers = [
            "A Guide for Investment Sales Professionals",
            "What Fundraisers Need to Know in 2025",
            "Leveraging Current Trends for Capital Raising",
            "Understanding Allocator Perspectives",
            "Timing Your Fundraising Approach"
        ]
        
        modifier = random.choice(modifiers)
        
        # Construct topic with Dakota focus
        templates = [
            f"{theme.title()}: {modifier}",
            f"The Complete Guide to {theme.title()} for Fundraisers",
            f"How {theme.title()} Creates Fundraising Opportunities",
            f"Navigating {theme.title()} in Today's Market",
            f"Institutional Insights: {theme.title()} and What It Means for Your Fund"
        ]
        
        return random.choice(templates)


def generate_topic_sync() -> str:
    """Synchronous wrapper for async topic generation"""
    generator = EnhancedTopicGenerator()
    
    try:
        # Try to use KB-informed generation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        topic = loop.run_until_complete(generator.generate_topic_with_kb_context())
        loop.close()
        return topic
    except:
        # Fallback to enhanced template generation
        return generator.generate_fallback_topic()