#!/usr/bin/env python3
"""
Clean up OpenAI files and fix naming conventions
"""
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import shutil

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def cleanup_openai_files():
    """Delete all files from OpenAI"""
    print("Cleaning up OpenAI files...")
    files = list(client.files.list())
    print(f"Found {len(files)} files to delete")
    
    for i, file in enumerate(files):
        try:
            client.files.delete(file.id)
            if (i + 1) % 50 == 0:
                print(f"Deleted {i + 1}/{len(files)} files...")
        except Exception as e:
            print(f"Error deleting {file.filename}: {e}")
    
    print("Cleanup complete!")
    return len(files)

def fix_filenames():
    """Fix all filenames to use consistent naming (underscores only)"""
    kb_dir = Path("knowledge_base_markdown")
    
    # Create a backup first
    backup_dir = Path("knowledge_base_markdown_backup2")
    if not backup_dir.exists():
        print("Creating backup...")
        shutil.copytree(kb_dir, backup_dir)
    
    renamed_count = 0
    all_files = list(kb_dir.rglob("*.md"))
    
    print(f"\nFixing filenames for {len(all_files)} files...")
    
    for file_path in all_files:
        old_name = file_path.name
        
        # Replace all hyphens with underscores in the filename
        new_name = old_name.replace('-', '_')
        
        if old_name != new_name:
            new_path = file_path.parent / new_name
            
            # Check if target exists
            if new_path.exists():
                print(f"Warning: {new_name} already exists, skipping")
                continue
                
            file_path.rename(new_path)
            renamed_count += 1
            
            if renamed_count % 10 == 0:
                print(f"Renamed {renamed_count} files...")
    
    print(f"\nRenamed {renamed_count} files to use consistent naming")
    
    # Verify no mixed naming remains
    mixed = 0
    for file_path in kb_dir.rglob("*.md"):
        if '-' in file_path.name:
            mixed += 1
            print(f"Still has hyphen: {file_path.name}")
    
    if mixed == 0:
        print("✅ All files now use consistent underscore naming!")
    else:
        print(f"⚠️  {mixed} files still have hyphens")

def check_final_state():
    """Check the final state of files"""
    kb_dir = Path("knowledge_base_markdown")
    all_files = list(kb_dir.rglob("*.md"))
    
    print(f"\nFINAL STATE:")
    print(f"Total files: {len(all_files)}")
    
    # Check max length
    max_len = max(len(f.name) for f in all_files)
    longest = [f for f in all_files if len(f.name) == max_len][0]
    print(f"Longest filename: {longest.name} ({max_len} chars)")
    
    # Check for any remaining issues
    issues = []
    for f in all_files:
        if '-' in f.name:
            issues.append(f"Has hyphen: {f.name}")
        if len(f.name) > 100:
            issues.append(f"Too long: {f.name}")
    
    if issues:
        print("\nRemaining issues:")
        for issue in issues[:10]:
            print(f"  - {issue}")
    else:
        print("✅ No issues found!")

if __name__ == "__main__":
    print("FILE UPLOAD FIX PROCESS")
    print("="*60)
    
    # Step 1: Clean up OpenAI
    deleted = cleanup_openai_files()
    
    # Step 2: Fix filenames
    print("\n" + "="*60)
    fix_filenames()
    
    # Step 3: Check final state
    print("\n" + "="*60)
    check_final_state()
    
    print("\n✅ Ready for re-upload!")