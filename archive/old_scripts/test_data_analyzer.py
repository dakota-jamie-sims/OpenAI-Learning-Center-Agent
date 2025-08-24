#!/usr/bin/env python3
"""
Test data analyzer agent in isolation
"""

import asyncio
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.dakota_agents.data_analyzer import DakotaDataAnalyzer
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def test_data_analyzer():
    """Test the data analyzer with sample CSV"""
    
    print("\n📊 Testing Data Analyzer Agent")
    print("=" * 60)
    
    # Initialize agent
    analyzer = DakotaDataAnalyzer()
    
    # Test task
    task = {
        "data_file": "sample_data/infrastructure_performance_2025.csv",
        "topic": "Infrastructure Fund Performance Q3 2025",
        "analysis_type": "performance"
    }
    
    print(f"Data file: {task['data_file']}")
    print(f"Topic: {task['topic']}")
    print(f"Analysis type: {task['analysis_type']}")
    print("\nRunning analysis...")
    
    try:
        result = await analyzer.execute(task)
        
        if result.get("success"):
            data = result.get("data", {})
            print("\n✅ Analysis successful!")
            print(f"Rows analyzed: {data.get('row_count', 0)}")
            print(f"Columns: {data.get('column_count', 0)}")
            print(f"\nColumns found: {', '.join(data.get('columns', []))}")
            
            print(f"\n📈 Insights ({len(data.get('insights', []))}):")
            for i, insight in enumerate(data.get('insights', []), 1):
                print(f"{i}. {insight}")
            
            print(f"\n📊 Key Metrics:")
            for metric, values in list(data.get('metrics', {}).items())[:3]:
                print(f"- {metric}: {values}")
            
            print(f"\n🔑 Key Findings:")
            for finding in data.get('key_findings', []):
                print(f"- {finding}")
                
        else:
            print(f"\n❌ Analysis failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Test error: {e}")
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_data_analyzer())