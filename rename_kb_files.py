#!/usr/bin/env python3
"""
Rename knowledge base files to shorter names for vector store upload
"""
import os
import shutil
from pathlib import Path

def shorten_filename(filename, max_length=50):
    """Shorten filename while preserving key information"""
    # Remove the extension
    name = filename.replace('.md', '')
    
    # Extract article number
    if name.startswith('article_'):
        parts = name.split('_', 2)
        if len(parts) >= 3:
            article_num = parts[1]
            title = parts[2]
            
            # Shorten title but keep key words
            title_parts = title.split('-')
            
            # Keep first few meaningful words
            short_title = []
            current_length = len(f"article_{article_num}_")
            
            for part in title_parts:
                if current_length + len(part) + 1 <= max_length - 3:  # -3 for .md
                    short_title.append(part)
                    current_length += len(part) + 1
                else:
                    break
            
            if short_title:
                return f"article_{article_num}_{'_'.join(short_title)}.md"
            else:
                return f"article_{article_num}.md"
    
    # For dakota way files, keep them as is (they're already short)
    if 'dakota_way' in name:
        return filename
    
    # For other files, truncate at max_length
    if len(name) > max_length - 3:
        return name[:max_length-3] + '.md'
    
    return filename

def rename_files():
    """Rename all KB files to shorter names"""
    # Create a backup directory
    backup_dir = Path("knowledge_base_markdown_backup")
    if not backup_dir.exists():
        print("Creating backup of original files...")
        shutil.copytree("knowledge_base_markdown", backup_dir)
        print(f"Backup created at: {backup_dir}")
    
    # Process files
    kb_dir = Path("knowledge_base_markdown")
    renamed_count = 0
    failed = []
    
    # Create mapping file to track renames
    mapping_lines = ["# File Rename Mapping\n\n"]
    
    for md_file in kb_dir.rglob("*.md"):
        try:
            old_name = md_file.name
            new_name = shorten_filename(old_name)
            
            if old_name != new_name:
                old_path = md_file
                new_path = md_file.parent / new_name
                
                # Check if new path already exists
                if new_path.exists():
                    # Add number suffix
                    base = new_name.replace('.md', '')
                    counter = 1
                    while new_path.exists():
                        new_name = f"{base}_{counter}.md"
                        new_path = md_file.parent / new_name
                        counter += 1
                
                # Rename the file
                old_path.rename(new_path)
                renamed_count += 1
                
                # Add to mapping
                mapping_lines.append(f"- `{old_name}` → `{new_name}`\n")
                
                if renamed_count % 50 == 0:
                    print(f"Renamed {renamed_count} files...")
                    
        except Exception as e:
            failed.append((str(md_file), str(e)))
    
    # Write mapping file
    with open("kb_rename_mapping.md", 'w') as f:
        f.writelines(mapping_lines)
    
    print(f"\n{'='*60}")
    print(f"Rename Complete!")
    print(f"- Total files renamed: {renamed_count}")
    print(f"- Failed: {len(failed)}")
    print(f"- Mapping saved to: kb_rename_mapping.md")
    print(f"- Backup saved to: {backup_dir}")
    
    if failed:
        print(f"\nFailed renames:")
        for path, error in failed[:5]:
            print(f"  - {path}: {error}")

def check_current_lengths():
    """Check current filename lengths"""
    kb_dir = Path("knowledge_base_markdown")
    
    lengths = []
    for md_file in kb_dir.rglob("*.md"):
        lengths.append((len(md_file.name), md_file.name))
    
    lengths.sort(reverse=True)
    
    print("Current filename lengths:")
    print(f"Longest: {lengths[0][0]} chars - {lengths[0][1][:50]}...")
    print(f"Average: {sum(l[0] for l in lengths) / len(lengths):.1f} chars")
    print(f"\nFiles over 50 chars: {sum(1 for l in lengths if l[0] > 50)}")
    print(f"Files over 80 chars: {sum(1 for l in lengths if l[0] > 80)}")
    print(f"Files over 100 chars: {sum(1 for l in lengths if l[0] > 100)}")

if __name__ == "__main__":
    print("Checking current filename lengths...\n")
    check_current_lengths()
    
    print(f"\n{'='*60}\n")
    
    response = input("Do you want to rename files to shorter names? (y/n): ")
    if response.lower() == 'y':
        rename_files()
    else:
        print("Rename cancelled.")