#!/usr/bin/env python3
"""
Check upload status and create vector store
"""
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import os
import time

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("VECTOR STORE CREATION PROCESS")
print("="*60)

# Check current upload status
print("\nChecking current file status...")
uploaded_files = list(client.files.list())
uploaded_names = set(f.filename for f in uploaded_files)
print(f"Files currently uploaded: {len(uploaded_files)}")

# Check local files
kb_dir = Path("knowledge_base_markdown")
local_files = list(kb_dir.rglob("*.md"))
local_names = set(f.name for f in local_files)
print(f"Total local files: {len(local_files)}")

# Find missing files
missing = local_names - uploaded_names
if missing:
    print(f"\nFiles still missing: {len(missing)}")
    print("Uploading missing files first...")
    
    for filename in missing:
        # Find the file path
        file_path = next((f for f in local_files if f.name == filename), None)
        if file_path:
            try:
                with open(file_path, 'rb') as f:
                    client.files.create(file=f, purpose='assistants')
                print(f"  ✅ {filename}")
            except Exception as e:
                print(f"  ❌ {filename}: {e}")
    
    # Re-check
    uploaded_files = list(client.files.list())
    print(f"\nFiles after upload: {len(uploaded_files)}")

# Create vector store
print("\nCreating vector store...")
try:
    vector_store = client.vector_stores.create(
        name="Dakota Knowledge Base",
        description="Dakota Learning Center articles and Dakota Way content"
    )
    print(f"✅ Created vector store: {vector_store.id}")
    
    # Get file IDs
    print("\nAdding files to vector store...")
    file_ids = [f.id for f in uploaded_files]
    
    # Add files in batches
    batch_size = 100
    for i in range(0, len(file_ids), batch_size):
        batch = file_ids[i:i+batch_size]
        print(f"  Adding batch {i//batch_size + 1}...")
        
        try:
            client.vector_stores.files.create_batch(
                vector_store_id=vector_store.id,
                file_ids=batch
            )
            print(f"  ✅ Added {len(batch)} files")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
        
        time.sleep(1)  # Brief pause between batches
    
    # Wait for processing
    print("\nWaiting for vector store to process files...")
    for i in range(30):  # Check for up to 5 minutes
        vs = client.vector_stores.retrieve(vector_store.id)
        if vs.status == 'completed':
            print(f"✅ Vector store ready!")
            break
        elif vs.status == 'failed':
            print(f"❌ Vector store failed: {vs.last_error}")
            break
        else:
            print(f"  Status: {vs.status} - {vs.file_counts}")
            time.sleep(10)
    
    # Final status
    print(f"\n{'='*60}")
    print(f"VECTOR STORE CREATED SUCCESSFULLY!")
    print(f"Vector Store ID: {vector_store.id}")
    print(f"Status: {vs.status}")
    print(f"File counts: {vs.file_counts}")
    print(f"\n📝 Add this to your .env file:")
    print(f"OPENAI_VECTOR_STORE_ID={vector_store.id}")
    
except Exception as e:
    print(f"❌ Error creating vector store: {e}")