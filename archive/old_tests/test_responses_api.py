#!/usr/bin/env python3
"""Test the Responses API directly"""

import os
import sys
sys.path.append(os.path.abspath('.'))

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def test_responses_api():
    """Test if the Responses API is available"""
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    print("Testing OpenAI client attributes...")
    print(f"Client type: {type(client)}")
    print(f"Has 'responses' attribute: {hasattr(client, 'responses')}")
    print(f"Has 'chat' attribute: {hasattr(client, 'chat')}")
    
    if hasattr(client, 'responses'):
        print("\n✅ Responses API is available!")
        print(f"Responses type: {type(client.responses)}")
        
        # Test a simple call
        try:
            response = client.responses.create(
                model="gpt-5-mini",
                input="What is 2+2?",
                reasoning={"effort": "minimal"},
                text={"verbosity": "low"}
            )
            print(f"\n✅ Responses API call successful!")
            print(f"Response type: {type(response)}")
            print(f"Has output: {hasattr(response, 'output')}")
            
            if hasattr(response, 'output'):
                print(f"Output length: {len(response.output)}")
                for i, item in enumerate(response.output):
                    print(f"  Item {i}: {type(item).__name__}")
                    
        except Exception as e:
            print(f"\n❌ Responses API call failed: {e}")
            print(f"Error type: {type(e).__name__}")
            
    else:
        print("\n❌ Responses API not available!")
        print("Available attributes:", dir(client)[:10], "...")

if __name__ == "__main__":
    test_responses_api()