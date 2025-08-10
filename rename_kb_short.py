#!/usr/bin/env python3
"""
Rename KB files to ensure they're under 50 characters
"""
import os
import shutil
from pathlib import Path

def rename_all_files():
    """Rename files to ensure they're under 50 chars"""
    # Backup first
    backup_dir = Path("knowledge_base_markdown_backup")
    if not backup_dir.exists():
        print("Creating backup...")
        shutil.copytree("knowledge_base_markdown", backup_dir)
        print(f"Backup created at: {backup_dir}")
    
    kb_dir = Path("knowledge_base_markdown")
    renamed = 0
    
    # Create mapping file
    mapping = ["# File Rename Mapping\n\n"]
    
    for md_file in kb_dir.rglob("*.md"):
        old_name = md_file.name
        
        # Skip if already short enough
        if len(old_name) <= 50:
            continue
            
        # For articles, keep number and shorten title
        if old_name.startswith('article_'):
            parts = old_name.split('_', 2)
            if len(parts) >= 3:
                num = parts[1]
                # Take first few words of title
                title_parts = parts[2].replace('.md', '').split('-')[:4]
                new_name = f"article_{num}_{'_'.join(title_parts)}.md"
                
                # Ensure it's under 50 chars
                if len(new_name) > 50:
                    new_name = f"article_{num}_{title_parts[0]}.md"
                
                # Rename
                new_path = md_file.parent / new_name
                if not new_path.exists():
                    md_file.rename(new_path)
                    renamed += 1
                    mapping.append(f"- `{old_name}` → `{new_name}`\n")
                    print(f"Renamed: {old_name[:40]}... → {new_name}")
    
    # Save mapping
    with open("rename_mapping.md", 'w') as f:
        f.writelines(mapping)
    
    print(f"\nRenamed {renamed} files")
    print(f"Mapping saved to: rename_mapping.md")

if __name__ == "__main__":
    rename_all_files()