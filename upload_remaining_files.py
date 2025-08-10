#!/usr/bin/env python3
"""
Upload all remaining files to OpenAI
"""
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import os
import time

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def upload_remaining_files():
    """Upload all files that aren't already uploaded"""
    
    # Get current uploaded files
    print("Fetching uploaded files...")
    uploaded_files = list(client.files.list())
    uploaded_names = set(f.filename for f in uploaded_files)
    print(f"Files already uploaded: {len(uploaded_names)}")
    
    # Get local files
    kb_dir = Path("knowledge_base_markdown")
    local_files = list(kb_dir.rglob("*.md"))
    print(f"Total local files: {len(local_files)}")
    
    # Find files to upload
    to_upload = [f for f in local_files if f.name not in uploaded_names]
    print(f"Files to upload: {len(to_upload)}")
    
    if not to_upload:
        print("All files are already uploaded!")
        return
    
    # Upload remaining files
    success_count = 0
    failed_files = []
    
    print("\nStarting uploads...")
    for i, file_path in enumerate(to_upload):
        print(f"\n[{i+1}/{len(to_upload)}] Uploading {file_path.name}...")
        
        try:
            with open(file_path, 'rb') as f:
                response = client.files.create(
                    file=f,
                    purpose='assistants'
                )
                print(f"  ✅ Success! ID: {response.id}")
                success_count += 1
                
                # Brief pause to avoid rate limits
                if (i + 1) % 10 == 0:
                    time.sleep(1)
                    
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            failed_files.append((file_path.name, str(e)))
    
    # Summary
    print(f"\n{'='*60}")
    print(f"UPLOAD COMPLETE!")
    print(f"- Successfully uploaded: {success_count}")
    print(f"- Failed: {len(failed_files)}")
    
    if failed_files:
        print("\nFailed uploads:")
        for name, error in failed_files:
            print(f"  - {name}: {error}")
    
    # Final check
    print("\nFinal verification...")
    final_count = len(list(client.files.list()))
    print(f"Total files in OpenAI: {final_count}")
    print(f"Expected: {len(local_files)}")
    
    if final_count == len(local_files):
        print("✅ All files successfully uploaded!")
    else:
        print(f"⚠️  Missing {len(local_files) - final_count} files")

if __name__ == "__main__":
    upload_remaining_files()