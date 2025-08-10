#!/usr/bin/env python3
"""
Clean OpenAI files and upload fresh
"""
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import os
import time

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def delete_all_files():
    """Delete all files from OpenAI"""
    print("STEP 1: Cleaning up OpenAI files...")
    print("="*60)
    
    files = list(client.files.list())
    total = len(files)
    print(f"Found {total} files to delete")
    
    if total == 0:
        print("No files to delete!")
        return
    
    deleted = 0
    for i, file in enumerate(files):
        try:
            client.files.delete(file.id)
            deleted += 1
            if (i + 1) % 50 == 0:
                print(f"Progress: {i + 1}/{total} deleted...")
        except Exception as e:
            print(f"Failed to delete {file.filename}: {e}")
    
    print(f"✅ Deleted {deleted} files")
    
    # Verify
    remaining = len(list(client.files.list()))
    print(f"Files remaining: {remaining}")
    
    return deleted

def upload_all_files():
    """Upload all knowledge base files"""
    print("\n\nSTEP 2: Uploading knowledge base files...")
    print("="*60)
    
    # Get all local files
    kb_dir = Path("knowledge_base_markdown")
    local_files = list(kb_dir.rglob("*.md"))
    total = len(local_files)
    print(f"Found {total} files to upload")
    
    success_count = 0
    failed_files = []
    
    print("\nStarting uploads...")
    for i, file_path in enumerate(local_files):
        try:
            with open(file_path, 'rb') as f:
                response = client.files.create(
                    file=f,
                    purpose='assistants'
                )
                success_count += 1
                
                # Show progress
                if (i + 1) % 10 == 0:
                    print(f"Progress: {i + 1}/{total} uploaded ({success_count} successful)")
                
                # Brief pause every 50 files
                if (i + 1) % 50 == 0:
                    time.sleep(1)
                    
        except Exception as e:
            failed_files.append((file_path.name, str(e)))
            print(f"❌ Failed: {file_path.name} - {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"UPLOAD COMPLETE!")
    print(f"- Total files: {total}")
    print(f"- Successfully uploaded: {success_count}")
    print(f"- Failed: {len(failed_files)}")
    
    if failed_files:
        print("\nFailed uploads:")
        for name, error in failed_files[:10]:
            print(f"  - {name}: {error}")
        if len(failed_files) > 10:
            print(f"  ... and {len(failed_files) - 10} more")
    
    # Final verification
    print("\nFinal verification...")
    final_count = len(list(client.files.list()))
    print(f"Total files in OpenAI: {final_count}")
    
    if final_count == total:
        print("✅ All files successfully uploaded!")
    else:
        print(f"⚠️  Missing {total - final_count} files")
    
    return success_count, failed_files

if __name__ == "__main__":
    print("CLEAN AND UPLOAD PROCESS")
    print("="*60)
    
    # Step 1: Clean
    delete_all_files()
    
    # Small pause
    print("\nWaiting 2 seconds before upload...")
    time.sleep(2)
    
    # Step 2: Upload
    upload_all_files()