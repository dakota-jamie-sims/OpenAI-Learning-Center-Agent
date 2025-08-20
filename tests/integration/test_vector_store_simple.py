#!/usr/bin/env python3
"""
Simple test to verify vector store is working
"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def test_vector_store():
    client = OpenAI()
    vector_store_id = os.getenv("VECTOR_STORE_ID")
    
    print(f"Testing vector store: {vector_store_id}")
    
    # Get vector store info
    store = client.vector_stores.retrieve(vector_store_id)
    print(f"✅ Vector store found: {store.name}")
    print(f"   Files: {store.file_counts.total}")
    print(f"   Status: {store.status}")
    
    # Create test assistant
    assistant = client.assistants.create(
        name="Test Assistant",
        model="gpt-4-turbo",
        tools=[{"type": "file_search"}],
        tool_resources={
            "file_search": {
                "vector_store_ids": [vector_store_id]
            }
        }
    )
    
    # Test search
    thread = client.threads.create()
    message = client.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content="Search for information about private equity secondaries"
    )
    
    run = client.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id
    )
    
    # Wait for completion
    import time
    while run.status in ['queued', 'in_progress']:
        time.sleep(1)
        run = client.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
    
    if run.status == 'completed':
        messages = client.threads.messages.list(thread_id=thread.id)
        response = messages.data[0].content[0].text.value
        print(f"\n✅ Search successful!")
        print(f"Response preview: {response[:200]}...")
    else:
        print(f"❌ Search failed: {run.status}")
    
    # Cleanup
    client.assistants.delete(assistant.id)

if __name__ == "__main__":
    test_vector_store()