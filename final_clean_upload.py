#!/usr/bin/env python3
"""
Final clean upload - delete all and upload fresh
"""
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import os
import time

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("FINAL CLEAN UPLOAD PROCESS")
print("="*60)

# Step 1: Delete ALL files
print("\nStep 1: Deleting all OpenAI files...")
files = list(client.files.list())
print(f"Found {len(files)} files to delete")

for i, f in enumerate(files):
    try:
        client.files.delete(f.id)
        if (i + 1) % 100 == 0:
            print(f"  Deleted {i + 1}...")
    except:
        pass

print("✅ All files deleted")

# Verify clean state
remaining = len(list(client.files.list()))
print(f"Verification: {remaining} files remaining")

if remaining > 0:
    print("⚠️  Some files couldn't be deleted. Exiting.")
    exit(1)

# Step 2: Upload all files
print("\nStep 2: Uploading knowledge base files...")
kb_dir = Path("knowledge_base_markdown")
local_files = list(kb_dir.rglob("*.md"))
print(f"Found {len(local_files)} files to upload")

success = 0
failed = []

for i, file_path in enumerate(local_files):
    try:
        with open(file_path, 'rb') as f:
            response = client.files.create(file=f, purpose='assistants')
        success += 1
        
        if (i + 1) % 50 == 0:
            print(f"  Progress: {i + 1}/{len(local_files)} uploaded")
            
    except Exception as e:
        failed.append((file_path.name, str(e)))

print(f"\n{'='*60}")
print(f"UPLOAD COMPLETE!")
print(f"- Total files: {len(local_files)}")
print(f"- Successfully uploaded: {success}")
print(f"- Failed: {len(failed)}")

if failed:
    print("\nFailed uploads:")
    for name, error in failed:
        print(f"  - {name}: {error}")

# Final verification
final = len(list(client.files.list()))
print(f"\nFinal verification: {final} files in OpenAI")

if final == len(local_files):
    print("✅ Perfect! All files uploaded successfully!")
else:
    print(f"⚠️  Mismatch: Expected {len(local_files)}, got {final}")