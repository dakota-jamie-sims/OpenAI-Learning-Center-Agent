#!/usr/bin/env python3
"""
Test Serper API raw response
"""
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_serper_raw():
    """Test Serper API raw response"""
    
    api_key = os.getenv('SERPER_API_KEY')
    if not api_key:
        print("❌ SERPER_API_KEY not found")
        return
    
    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}
    payload = {"q": "AI investment trends Q4 2024", "num": 2}
    
    print("🔍 Testing Serper API directly...")
    print(f"Endpoint: https://google.serper.dev/search")
    print(f"Query: {payload['q']}")
    
    try:
        response = requests.post(
            "https://google.serper.dev/search", 
            headers=headers, 
            json=payload, 
            timeout=10
        )
        
        print(f"\n📡 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n📄 Raw Response Structure:")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_serper_raw()