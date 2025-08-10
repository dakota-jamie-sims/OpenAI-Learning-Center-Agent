#!/usr/bin/env python3
"""
Check for potential upload issues with knowledge base files
"""
import os
from pathlib import Path
import re

def check_files():
    """Check files for potential upload issues"""
    kb_dir = Path("knowledge_base_markdown")
    
    issues = {
        'special_chars': [],
        'large_files': [],
        'empty_files': [],
        'long_names': [],
        'encoding_issues': []
    }
    
    all_files = list(kb_dir.rglob("*.md"))
    print(f"Checking {len(all_files)} files for potential issues...\n")
    
    for file_path in all_files:
        filename = file_path.name
        
        # Check for special characters that might cause issues
        if re.search(r'[^a-zA-Z0-9_\-.]', filename):
            issues['special_chars'].append(filename)
        
        # Check file size (OpenAI limit is 512MB but large files might timeout)
        size = file_path.stat().st_size
        if size > 1024 * 1024:  # Files over 1MB
            issues['large_files'].append((filename, f"{size/1024/1024:.1f}MB"))
        
        # Check for empty files
        if size == 0:
            issues['empty_files'].append(filename)
        
        # Check filename length (even after renaming)
        if len(filename) > 50:
            issues['long_names'].append((filename, len(filename)))
        
        # Check encoding
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                f.read()
        except UnicodeDecodeError:
            issues['encoding_issues'].append(filename)
    
    # Report findings
    print("POTENTIAL ISSUES FOUND:")
    print("="*60)
    
    if issues['special_chars']:
        print(f"\n❌ Files with special characters ({len(issues['special_chars'])}):")
        for f in issues['special_chars'][:5]:
            print(f"  - {f}")
        if len(issues['special_chars']) > 5:
            print(f"  ... and {len(issues['special_chars'])-5} more")
    
    if issues['large_files']:
        print(f"\n⚠️  Large files ({len(issues['large_files'])}):")
        for f, size in issues['large_files'][:5]:
            print(f"  - {f} ({size})")
    
    if issues['empty_files']:
        print(f"\n❌ Empty files ({len(issues['empty_files'])}):")
        for f in issues['empty_files']:
            print(f"  - {f}")
    
    if issues['long_names']:
        print(f"\n⚠️  Files with names still over 50 chars ({len(issues['long_names'])}):")
        for f, length in issues['long_names']:
            print(f"  - {f} ({length} chars)")
    
    if issues['encoding_issues']:
        print(f"\n❌ Files with encoding issues ({len(issues['encoding_issues'])}):")
        for f in issues['encoding_issues']:
            print(f"  - {f}")
    
    # Check for patterns in filenames
    print(f"\n\nFILE PATTERNS:")
    print("="*60)
    
    # Group by prefix
    prefixes = {}
    for file_path in all_files:
        prefix = file_path.name.split('_')[0]
        prefixes[prefix] = prefixes.get(prefix, 0) + 1
    
    for prefix, count in sorted(prefixes.items()):
        print(f"{prefix}: {count} files")
    
    # List all unique special characters found
    all_chars = set()
    for file_path in all_files:
        for char in file_path.name:
            if not char.isalnum() and char not in '_-.':
                all_chars.add(char)
    
    if all_chars:
        print(f"\nUnique special characters found: {sorted(all_chars)}")
    
    return issues

if __name__ == "__main__":
    issues = check_files()
    
    # Check what's currently in OpenAI
    print(f"\n\nCHECKING OPENAI FILES:")
    print("="*60)
    
    try:
        from openai import OpenAI
        from dotenv import load_dotenv
        load_dotenv()
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        files = list(client.files.list())
        
        print(f"Files currently in OpenAI: {len(files)}")
        
        if files:
            # Check which files made it
            uploaded_names = [f.filename for f in files]
            kb_files = list(Path("knowledge_base_markdown").rglob("*.md"))
            kb_names = [f.name for f in kb_files]
            
            # Find which didn't upload
            not_uploaded = [name for name in kb_names if name not in uploaded_names]
            print(f"Files that failed to upload: {len(not_uploaded)}")
            
            if not_uploaded:
                print("\nFirst 10 files that didn't upload:")
                for name in not_uploaded[:10]:
                    print(f"  - {name}")
                    
                # Look for patterns in failures
                print("\nAnalyzing failed uploads...")
                failed_prefixes = {}
                for name in not_uploaded:
                    prefix = name.split('_')[0]
                    failed_prefixes[prefix] = failed_prefixes.get(prefix, 0) + 1
                
                print("Failed uploads by prefix:")
                for prefix, count in sorted(failed_prefixes.items()):
                    print(f"  {prefix}: {count} files")
                    
    except Exception as e:
        print(f"Error checking OpenAI files: {e}")