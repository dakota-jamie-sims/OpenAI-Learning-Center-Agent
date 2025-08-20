#!/usr/bin/env python3
"""
Test Vector Store Integration
Verifies that the system can properly access and search the Dakota knowledge base
"""
import os
import sys
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()

def test_vector_store_access():
    """Test basic vector store access"""
    print("=== Testing Vector Store Integration ===\n")
    
    # Initialize client
    client = OpenAI()
    vector_store_id = os.getenv("VECTOR_STORE_ID")
    
    if not vector_store_id:
        print("❌ ERROR: VECTOR_STORE_ID not found in environment")
        return False
    
    print(f"✅ Vector Store ID found: {vector_store_id}")
    
    # Get vector store info
    try:
        vector_store = client.vector_stores.retrieve(vector_store_id)
        print(f"✅ Vector Store accessed successfully")
        print(f"   - Name: {vector_store.name}")
        print(f"   - Status: {vector_store.status}")
        print(f"   - File Count: {vector_store.file_counts.total}")
        print(f"   - In Progress: {vector_store.file_counts.in_progress}")
        print(f"   - Completed: {vector_store.file_counts.completed}")
        print(f"   - Failed: {vector_store.file_counts.failed}")
    except Exception as e:
        print(f"❌ ERROR accessing vector store: {str(e)}")
        return False
    
    # Test search functionality
    print(f"\n=== Testing Search Functionality ===")
    test_queries = [
        "private equity firms",
        "Dakota Way",
        "investment sales",
        "city scheduling"
    ]
    
    # Create a test assistant with vector store
    try:
        assistant = client.assistants.create(
            name="Test Vector Store Search",
            model="gpt-4",
            tools=[{"type": "file_search"}],
            tool_resources={
                "file_search": {
                    "vector_store_ids": [vector_store_id]
                }
            }
        )
        print(f"✅ Test assistant created with vector store")
        
        # Test each query
        for query in test_queries:
            print(f"\n📍 Testing query: '{query}'")
            
            # Create thread and message
            thread = client.threads.create()
            message = client.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"Search the knowledge base for information about: {query}"
            )
            
            # Run the assistant
            run = client.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant.id
            )
            
            # Wait for completion
            import time
            while run.status in ['queued', 'in_progress']:
                time.sleep(1)
                run = client.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
            
            if run.status == 'completed':
                # Get the response
                messages = client.threads.messages.list(thread_id=thread.id)
                response = messages.data[0].content[0].text.value
                print(f"   ✅ Search completed")
                print(f"   Response preview: {response[:200]}...")
                
                # Check if file citations were used
                if hasattr(messages.data[0].content[0].text, 'annotations') and messages.data[0].content[0].text.annotations:
                    print(f"   📎 {len(messages.data[0].content[0].text.annotations)} file citations found")
            else:
                print(f"   ❌ Search failed: {run.status}")
        
        # Cleanup
        client.assistants.delete(assistant_id=assistant.id)
        print(f"\n✅ Test assistant cleaned up")
        
    except Exception as e:
        print(f"❌ ERROR during search test: {str(e)}")
        return False
    
    print(f"\n=== Integration Test Complete ===")
    return True

def check_orchestrator_integration():
    """Check if orchestrators are configured for vector store"""
    print(f"\n=== Checking Orchestrator Integration ===")
    
    orchestrator_files = [
        "src/pipeline/simple_orchestrator.py",
        "src/pipeline/enhanced_orchestrator.py",
        "src/pipeline/multi_agent_orchestrator.py"
    ]
    
    for file_path in orchestrator_files:
        if Path(file_path).exists():
            with open(file_path, 'r') as f:
                content = f.read()
                if 'vector_store' in content.lower():
                    print(f"✅ {file_path} - Vector store integration found")
                else:
                    print(f"⚠️  {file_path} - No vector store integration found")
        else:
            print(f"❌ {file_path} - File not found")

if __name__ == "__main__":
    # Test vector store access
    if test_vector_store_access():
        print("\n✅ Vector store is properly integrated and accessible!")
    else:
        print("\n❌ Vector store integration issues detected")
    
    # Check orchestrator integration
    check_orchestrator_integration()