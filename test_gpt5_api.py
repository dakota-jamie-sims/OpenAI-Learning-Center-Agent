#!/usr/bin/env python3
"""
Test GPT-5 API directly
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def test_responses_api():
    """Test GPT-5 with Responses API"""
    client = OpenAI()
    
    print("Testing GPT-5 Responses API...")
    
    try:
        response = client.responses.create(
            model="gpt-5",
            input="What is 2+2? Answer in one word.",
            reasoning={
                "effort": "minimal"
            },
            text={
                "verbosity": "low"
            }
        )
        
        print("✅ Responses API works!")
        print(f"Response: {response}")
        
        # Try to extract text
        if hasattr(response, 'output_text'):
            print(f"Output: {response.output_text}")
        elif hasattr(response, 'output'):
            print(f"Output: {response.output}")
            
    except Exception as e:
        print(f"❌ Responses API error: {e}")
        print("\nFalling back to Chat Completions API...")
        
        # Try chat completions as fallback
        try:
            response = client.chat.completions.create(
                model="gpt-4o",  # Fallback model
                messages=[
                    {"role": "user", "content": "What is 2+2? Answer in one word."}
                ],
                max_tokens=10
            )
            
            print("✅ Chat Completions API works!")
            print(f"Response: {response.choices[0].message.content}")
            
        except Exception as e2:
            print(f"❌ Chat Completions error: {e2}")

def test_models():
    """Test which models are available"""
    client = OpenAI()
    
    print("\nTesting model availability...")
    
    models_to_test = ["gpt-5", "gpt-5-mini", "gpt-5-nano", "gpt-4o", "gpt-4.1"]
    
    for model in models_to_test:
        try:
            # Try a minimal request
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1
            )
            print(f"✅ {model} - Available")
        except Exception as e:
            error_msg = str(e)
            if "model" in error_msg.lower():
                print(f"❌ {model} - Not available")
            else:
                print(f"⚠️  {model} - Error: {error_msg[:50]}...")

if __name__ == "__main__":
    test_responses_api()
    test_models()