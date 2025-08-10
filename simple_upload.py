#!/usr/bin/env python3
"""
Simple file upload to OpenAI
"""
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Get all files
kb_dir = Path("knowledge_base_markdown")
files = list(kb_dir.rglob("*.md"))
print(f"Uploading {len(files)} files...")

success = 0
for i, file_path in enumerate(files):
    try:
        with open(file_path, 'rb') as f:
            response = client.files.create(file=f, purpose='assistants')
        success += 1
        if (i + 1) % 50 == 0:
            print(f"Progress: {i + 1}/{len(files)} ({success} successful)")
    except Exception as e:
        print(f"Failed: {file_path.name} - {e}")

print(f"\nComplete! Uploaded {success}/{len(files)} files")

# Check total
total = len(list(client.files.list()))
print(f"Total files in OpenAI: {total}")