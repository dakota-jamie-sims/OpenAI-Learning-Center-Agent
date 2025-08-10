#!/usr/bin/env python3
"""
Upload files directly to a vector store
"""
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import os
import time

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def create_vector_store_with_files():
    """Create a new vector store and upload files to it"""
    
    # Get all local files
    kb_dir = Path("knowledge_base_markdown")
    local_files = list(kb_dir.rglob("*.md"))
    print(f"Found {len(local_files)} files to upload")
    
    # Create vector store
    print("\nCreating vector store...")
    vector_store = client.vector_stores.create(
        name="Dakota Knowledge Base"
    )
    print(f"Created vector store: {vector_store.id}")
    
    # Upload files in batches
    batch_size = 20
    file_ids = []
    
    print(f"\nUploading files in batches of {batch_size}...")
    
    for i in range(0, len(local_files), batch_size):
        batch = local_files[i:i+batch_size]
        print(f"\nBatch {i//batch_size + 1}/{(len(local_files) + batch_size - 1)//batch_size}")
        
        # Upload batch
        for file_path in batch:
            try:
                with open(file_path, 'rb') as f:
                    file_obj = client.files.create(
                        file=f,
                        purpose='assistants'
                    )
                    file_ids.append(file_obj.id)
                    print(f"  ✅ {file_path.name}")
            except Exception as e:
                print(f"  ❌ {file_path.name}: {e}")
        
        # Add files to vector store
        if file_ids:
            print(f"  Adding {len(file_ids)} files to vector store...")
            try:
                client.vector_stores.files.create_batch(
                    vector_store_id=vector_store.id,
                    file_ids=file_ids
                )
                print(f"  ✅ Added batch to vector store")
            except Exception as e:
                print(f"  ❌ Failed to add batch: {e}")
            
            file_ids = []  # Reset for next batch
        
        # Brief pause
        time.sleep(1)
    
    print(f"\n{'='*60}")
    print(f"UPLOAD COMPLETE!")
    print(f"Vector Store ID: {vector_store.id}")
    print(f"\nAdd this to your .env file:")
    print(f"OPENAI_VECTOR_STORE_ID={vector_store.id}")
    
    # Check vector store status
    vs = client.vector_stores.retrieve(vector_store.id)
    print(f"\nVector store status: {vs.status}")
    print(f"File counts: {vs.file_counts}")

if __name__ == "__main__":
    create_vector_store_with_files()