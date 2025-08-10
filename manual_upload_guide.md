# Manual Vector Store Upload Guide

## Option 1: Using OpenAI Platform (Web Interface)

1. Go to https://platform.openai.com/storage
2. Click on "Vector stores" in the left sidebar
3. Find your vector store (vs_6897c5e4fd0081919ec60a0ca81e3236)
4. Click "Add files"
5. Select and upload your files directly

## Option 2: Upload Individual Files via Script

```python
#!/usr/bin/env python3
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI()

# Your vector store ID
vector_store_id = "vs_6897c5e4fd0081919ec60a0ca81e3236"

# Upload a single file
def upload_file(file_path):
    try:
        # Upload file
        with open(file_path, 'rb') as f:
            file_obj = client.files.create(
                file=f,
                purpose='assistants'
            )
        
        # Add to vector store
        client.vector_stores.files.create(
            vector_store_id=vector_store_id,
            file_id=file_obj.id
        )
        
        print(f"✓ Uploaded: {file_path}")
        return True
    except Exception as e:
        print(f"✗ Failed: {file_path} - {e}")
        return False

# Example: Upload specific files
files_to_upload = [
    "knowledge_base/learning_center/article_001.json",
    "knowledge_base/learning_center/article_002.json",
    # Add more files as needed
]

for file_path in files_to_upload:
    upload_file(file_path)
```

## Option 3: Find and Upload Missing Files

```python
#!/usr/bin/env python3
# List files NOT in vector store
import os
from pathlib import Path

# Get all KB files
kb_files = set()
for f in Path("knowledge_base").rglob("*.json"):
    kb_files.add(f.stem)  # Just the filename without extension

print(f"Total KB files: {len(kb_files)}")

# You can then compare with what's already uploaded
# and manually upload any missing ones
```

## To check what's already in your vector store:

```python
# List first 100 files in vector store
response = client.vector_stores.files.list(
    vector_store_id=vector_store_id,
    limit=100
)

uploaded_files = set()
for file in response.data:
    file_details = client.files.retrieve(file.id)
    uploaded_files.add(file_details.filename)

print(f"Files in vector store: {len(uploaded_files)}")
```

Would you like me to create a simple script to help you identify which specific files are missing?