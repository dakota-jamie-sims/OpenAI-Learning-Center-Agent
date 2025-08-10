#!/usr/bin/env python3
"""
Create a clean vector store with exactly the files from knowledge_base
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def create_clean_vector_store():
    """Create a new vector store with only the knowledge_base files"""
    client = OpenAI()
    
    # Create new vector store
    print("Creating new clean vector store...")
    vector_store = client.vector_stores.create(
        name="Dakota Knowledge Base - Clean (404 files)"
    )
    vector_store_id = vector_store.id
    print(f"Created vector store: {vector_store_id}")
    
    # Get all JSON files from knowledge_base
    kb_path = Path("knowledge_base")
    json_files = sorted(kb_path.rglob("*.json"))
    
    print(f"\nFound {len(json_files)} JSON files in knowledge_base")
    
    # Upload files in batches
    batch_size = 20
    uploaded_count = 0
    failed_files = []
    
    for i in range(0, len(json_files), batch_size):
        batch = json_files[i:i+batch_size]
        batch_file_ids = []
        
        print(f"\nUploading batch {i//batch_size + 1}/{(len(json_files) + batch_size - 1)//batch_size}")
        
        for json_path in batch:
            try:
                # Read JSON and convert to formatted text
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Create formatted text with all fields
                text_content = f"Title: {data.get('title', 'Untitled')}\n"
                text_content += f"URL: {data.get('url', '')}\n"
                text_content += f"Date: {data.get('date', '')}\n"
                text_content += f"Author: {data.get('author', '')}\n"
                if data.get('topics'):
                    text_content += f"Topics: {', '.join(data.get('topics', []))}\n"
                text_content += f"\n{data.get('content', '')}"
                
                # Upload as text file
                file_obj = client.files.create(
                    file=(f"{json_path.stem}.txt", text_content.encode('utf-8')),
                    purpose='assistants'
                )
                
                batch_file_ids.append(file_obj.id)
                uploaded_count += 1
                
            except Exception as e:
                print(f"  ✗ Failed: {json_path.name} - {e}")
                failed_files.append(str(json_path))
        
        # Add batch to vector store
        if batch_file_ids:
            try:
                client.vector_stores.file_batches.create(
                    vector_store_id=vector_store_id,
                    file_ids=batch_file_ids
                )
                print(f"  ✓ Added {len(batch_file_ids)} files to vector store")
            except Exception as e:
                print(f"  ✗ Failed to add batch: {e}")
    
    # Check final status
    store = client.vector_stores.retrieve(vector_store_id)
    
    print(f"\n{'='*60}")
    print(f"Vector Store Creation Complete!")
    print(f"- Vector Store ID: {vector_store_id}")
    print(f"- Files in knowledge_base: {len(json_files)}")
    print(f"- Successfully uploaded: {uploaded_count}")
    print(f"- Failed uploads: {len(failed_files)}")
    print(f"- Vector store status: {store.status}")
    print(f"- Vector store file counts: {store.file_counts}")
    
    if failed_files:
        print(f"\nFailed files:")
        for f in failed_files[:5]:
            print(f"  - {f}")
        if len(failed_files) > 5:
            print(f"  ... and {len(failed_files) - 5} more")
    
    # Update .env
    print(f"\n{'='*60}")
    print(f"To use this new vector store, update your .env file:")
    print(f"VECTOR_STORE_ID={vector_store_id}")
    
    return vector_store_id

if __name__ == "__main__":
    create_clean_vector_store()