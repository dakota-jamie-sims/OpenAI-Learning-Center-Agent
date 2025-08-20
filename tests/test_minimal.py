#!/usr/bin/env python3
"""
Minimal test to verify chat completions API works
"""
import os

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI


def test_openai_connection():
    """Test basic OpenAI connection"""
    print("Testing OpenAI Connection...")
    
    try:
        client = OpenAI()
        
        # Simple test
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say 'Hello, Dakota Learning Center!' in 5 words or less"}
            ],
            max_tokens=20
        )
        
        result = response.choices[0].message.content
        print(f"✅ Success! Response: {result}")
        print(f"Model used: {response.model}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def test_vector_store():
    """Test vector store access"""
    print("\nTesting Vector Store...")
    
    vector_store_id = os.getenv("VECTOR_STORE_ID")
    if not vector_store_id:
        print("⚠️  No VECTOR_STORE_ID found in environment")
        return False
        
    try:
        client = OpenAI()
        
        # Try to retrieve the vector store
        vector_store = client.beta.vector_stores.retrieve(vector_store_id)
        print(f"✅ Vector store found: {vector_store.name}")
        print(f"   File counts: {vector_store.file_counts}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error accessing vector store: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("Dakota Learning Center - System Test")
    print("=" * 50)
    
    # Test 1: OpenAI Connection
    openai_ok = test_openai_connection()
    
    # Test 2: Vector Store
    vector_ok = test_vector_store()
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print(f"OpenAI Connection: {'✅ PASS' if openai_ok else '❌ FAIL'}")
    print(f"Vector Store: {'✅ PASS' if vector_ok else '❌ FAIL'}")
    print("=" * 50)