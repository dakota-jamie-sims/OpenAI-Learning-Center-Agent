#!/usr/bin/env python3
"""
Setup script for initializing the vector store with knowledge base
Run this once to create and populate the vector store
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from openai import OpenAI
from src.tools.vector_store_handler import VectorStoreHandler
from src.config_enhanced import KNOWLEDGE_BASE_DIR


def main():
    """Initialize vector store with knowledge base files"""
    load_dotenv()
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment")
        print("Please add it to your .env file")
        return
    
    print("🚀 Dakota Learning Center - Vector Store Setup")
    print("=" * 50)
    
    # Initialize client and handler
    client = OpenAI(api_key=api_key)
    handler = VectorStoreHandler(client)
    
    # Check if vector store already exists
    existing_id = os.getenv("VECTOR_STORE_ID")
    if existing_id:
        print(f"ℹ️  Found existing vector store ID: {existing_id}")
        response = input("Do you want to create a new vector store? (y/N): ")
        if response.lower() != 'y':
            print("Using existing vector store.")
            return
    
    # Create vector store
    print("\n📦 Creating new vector store...")
    vector_store_id = handler.create_or_get_vector_store("Dakota Knowledge Base")
    
    # Check knowledge base directory
    kb_path = Path(KNOWLEDGE_BASE_DIR)
    if not kb_path.exists():
        print(f"❌ Error: Knowledge base directory not found: {KNOWLEDGE_BASE_DIR}")
        return
    
    # Count files
    files = list(kb_path.rglob("*.md")) + list(kb_path.rglob("*.txt"))
    print(f"\n📚 Found {len(files)} files in knowledge base")
    
    if not files:
        print("❌ No files found to upload")
        return
    
    # Upload files
    print(f"\n📤 Uploading files to vector store...")
    uploaded = handler.upload_knowledge_base(str(KNOWLEDGE_BASE_DIR), max_files=100)
    
    print(f"\n✅ Successfully uploaded {len(uploaded)} files")
    print(f"✅ Vector Store ID: {vector_store_id}")
    print(f"✅ Saved to .env file")
    
    # Test search
    print("\n🔍 Testing vector store search...")
    test_query = "Dakota investment philosophy"
    
    # Create a simple test
    try:
        assistant = client.beta.assistants.create(
            name="Test Assistant",
            instructions="Search for information",
            model="gpt-4.1",
            tools=[{
                "type": "file_search",
                "file_search": {
                    "vector_store_ids": [vector_store_id]
                }
            }]
        )
        
        thread = client.beta.threads.create()
        message = client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=f"Search for: {test_query}"
        )
        
        run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )
        
        # Wait for completion (simplified)
        import time
        for _ in range(30):  # 30 second timeout
            time.sleep(1)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run.status == 'completed':
                print("✅ Vector store search test successful!")
                break
            elif run.status == 'failed':
                print("❌ Vector store search test failed")
                break
        
        # Cleanup
        client.beta.assistants.delete(assistant.id)
        
    except Exception as e:
        print(f"⚠️  Search test failed: {e}")
    
    print("\n✨ Vector store setup complete!")
    print("You can now run the article generation pipeline.")


if __name__ == "__main__":
    main()