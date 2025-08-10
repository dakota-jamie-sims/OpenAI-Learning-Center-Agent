#!/usr/bin/env python3
"""
Upload only remaining files
"""
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Get uploaded files
uploaded = set(f.filename for f in client.files.list())
print(f"Files already uploaded: {len(uploaded)}")

# Get local files
kb_dir = Path("knowledge_base_markdown")
local_files = list(kb_dir.rglob("*.md"))
print(f"Total local files: {len(local_files)}")

# Find remaining
remaining = [f for f in local_files if f.name not in uploaded]
print(f"Files to upload: {len(remaining)}")

if remaining:
    print("\nUploading remaining files:")
    for f in remaining:
        print(f"  - {f.name}")
    
    print("\nStarting upload...")
    for file_path in remaining:
        try:
            with open(file_path, 'rb') as f:
                response = client.files.create(file=f, purpose='assistants')
            print(f"✅ {file_path.name}")
        except Exception as e:
            print(f"❌ {file_path.name}: {e}")
else:
    print("All files are uploaded!")

# Final check
final = len(list(client.files.list()))
print(f"\nFinal count: {final}/{len(local_files)}")