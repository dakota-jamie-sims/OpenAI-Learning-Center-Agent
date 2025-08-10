#!/usr/bin/env python3
"""
Simple script to rename files with hyphens to use underscores
"""
from pathlib import Path

kb_dir = Path("knowledge_base_markdown")
files_with_hyphens = list(kb_dir.rglob("*-*.md"))

print(f"Found {len(files_with_hyphens)} files with hyphens")

renamed = 0
for file_path in files_with_hyphens:
    old_name = file_path.name
    new_name = old_name.replace('-', '_')
    new_path = file_path.parent / new_name
    
    if not new_path.exists():
        file_path.rename(new_path)
        renamed += 1
        print(f"Renamed: {old_name} → {new_name}")
    else:
        print(f"Skipped (exists): {new_name}")

print(f"\nRenamed {renamed} files")

# Verify
remaining = list(Path("knowledge_base_markdown").rglob("*-*.md"))
print(f"Files still with hyphens: {len(remaining)}")