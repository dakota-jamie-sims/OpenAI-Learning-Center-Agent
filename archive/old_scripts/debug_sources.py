#!/usr/bin/env python3
"""Debug sources issue in Dakota system"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from src.agents.dakota_agents.web_researcher import DakotaWebResearcher
from src.agents.dakota_agents.kb_researcher import DakotaKBResearcher

async def test_research():
    """Test research agents to see what sources they return"""
    
    print("Testing Web Researcher...")
    web_researcher = DakotaWebResearcher()
    web_result = await web_researcher.execute({"topic": "private credit emerging managers"})
    
    print(f"\nWeb Research Success: {web_result['success']}")
    if web_result['success']:
        print(f"Sources found: {len(web_result['data'].get('sources', []))}")
        for i, source in enumerate(web_result['data'].get('sources', [])[:5]):
            print(f"\n{i+1}. {source.get('title', 'No title')}")
            print(f"   URL: {source.get('url', 'No URL')}")
    
    print("\n" + "="*60 + "\n")
    
    print("Testing KB Researcher...")
    kb_researcher = DakotaKBResearcher()
    kb_result = await kb_researcher.execute({"topic": "private credit emerging managers"})
    
    print(f"\nKB Research Success: {kb_result['success']}")
    if kb_result['success']:
        print(f"Sources found: {len(kb_result['data'].get('sources', []))}")
        for i, source in enumerate(kb_result['data'].get('sources', [])[:5]):
            print(f"\n{i+1}. {source.get('title', 'No title')}")
            print(f"   URL: {source.get('url', 'No URL')}")

if __name__ == "__main__":
    asyncio.run(test_research())