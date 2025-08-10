#!/usr/bin/env python3
"""
Upload all knowledge base files to the vector store
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
import json

# Load environment variables
load_dotenv()

def upload_all_kb_files():
    """Upload all knowledge base files to vector store"""
    client = OpenAI()
    
    # Get or create vector store
    vector_store_id = os.getenv("VECTOR_STORE_ID")
    if not vector_store_id:
        print("Creating new vector store...")
        vector_store = client.vector_stores.create(name="Dakota Knowledge Base Complete")
        vector_store_id = vector_store.id
        print(f"Created vector store: {vector_store_id}")
    else:
        print(f"Using existing vector store: {vector_store_id}")
        # Check if we need to create a new one
        try:
            store = client.vector_stores.retrieve(vector_store_id)
            print(f"Current file counts: {store.file_counts}")
            if store.file_counts.total >= 400:
                print("Vector store already has all files!")
                return
        except Exception as e:
            print(f"Error retrieving vector store: {e}")
            print("Creating new vector store...")
            vector_store = client.vector_stores.create(name="Dakota Knowledge Base Complete")
            vector_store_id = vector_store.id
    
    # Find all KB files
    kb_path = Path("knowledge_base")
    all_files = []
    
    # Get all JSON, TXT, and MD files
    for pattern in ["*.json", "*.txt", "*.md"]:
        all_files.extend(kb_path.rglob(pattern))
    
    print(f"\nFound {len(all_files)} files to upload")
    
    # Upload files in batches
    batch_size = 20
    uploaded_count = 0
    failed_files = []
    
    for i in range(0, len(all_files), batch_size):
        batch = all_files[i:i+batch_size]
        batch_file_ids = []
        
        print(f"\nUploading batch {i//batch_size + 1}/{(len(all_files) + batch_size - 1)//batch_size}")
        
        for file_path in batch:
            try:
                # For JSON files, convert to text first
                if file_path.suffix == '.json':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Convert JSON to readable text
                        text_content = json.dumps(data, indent=2)
                        
                    # Create a temporary text representation
                    file_obj = client.files.create(
                        file=(file_path.name.replace('.json', '.txt'), text_content.encode('utf-8')),
                        purpose='assistants'
                    )
                else:
                    # Upload text/markdown files directly
                    with open(file_path, 'rb') as f:
                        file_obj = client.files.create(
                            file=f,
                            purpose='assistants'
                        )
                
                batch_file_ids.append(file_obj.id)
                uploaded_count += 1
                print(f"  ✓ {file_path.name}")
                
            except Exception as e:
                print(f"  ✗ Failed to upload {file_path}: {e}")
                failed_files.append(str(file_path))
        
        # Add batch to vector store
        if batch_file_ids:
            try:
                client.vector_stores.file_batches.create(
                    vector_store_id=vector_store_id,
                    file_ids=batch_file_ids
                )
                print(f"  → Added {len(batch_file_ids)} files to vector store")
            except Exception as e:
                print(f"  → Failed to add batch to vector store: {e}")
    
    # Final summary
    print(f"\n{'='*50}")
    print(f"Upload Summary:")
    print(f"- Total files found: {len(all_files)}")
    print(f"- Successfully uploaded: {uploaded_count}")
    print(f"- Failed uploads: {len(failed_files)}")
    
    if failed_files:
        print("\nFailed files:")
        for f in failed_files[:10]:  # Show first 10
            print(f"  - {f}")
        if len(failed_files) > 10:
            print(f"  ... and {len(failed_files) - 10} more")
    
    # Save the vector store ID
    if vector_store_id != os.getenv("VECTOR_STORE_ID"):
        print(f"\nUpdating .env with new vector store ID: {vector_store_id}")
        # Update .env file
        env_path = Path(".env")
        lines = []
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
        
        # Update or add VECTOR_STORE_ID
        found = False
        for i, line in enumerate(lines):
            if line.startswith("VECTOR_STORE_ID="):
                lines[i] = f"VECTOR_STORE_ID={vector_store_id}\n"
                found = True
                break
        
        if not found:
            lines.append(f"VECTOR_STORE_ID={vector_store_id}\n")
        
        with open(env_path, 'w') as f:
            f.writelines(lines)
    
    print(f"\n✅ Vector store ready with ID: {vector_store_id}")

if __name__ == "__main__":
    upload_all_kb_files()