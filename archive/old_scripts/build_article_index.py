#!/usr/bin/env python3
"""
Build an index of all Learning Center articles with their URLs
This allows the KB researcher to find real URLs for related articles
"""

import os
import json
import re
from typing import Dict, List, Tuple
from pathlib import Path


def extract_article_info(file_path: str) -> Tuple[str, str, str]:
    """Extract title and URL from an article file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract title
    title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    title = title_match.group(1) if title_match else Path(file_path).stem
    
    # Extract URL - look for different patterns
    url = ""
    
    # Pattern 1: "- **Original URL:** https://..."
    url_match = re.search(r'-\s*\*\*Original URL:\*\*\s*(https?://[^\s\n]+)', content)
    if url_match:
        url = url_match.group(1).strip()
    else:
        # Pattern 2: "Original URL: https://..."
        url_match = re.search(r'Original URL:\s*(https?://[^\s\n]+)', content)
        if url_match:
            url = url_match.group(1).strip()
    
    # Extract description (first paragraph after title)
    desc_match = re.search(r'^#.*?\n\n(.+?)(?:\n\n|\n##)', content, re.MULTILINE | re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else ""
    if len(description) > 200:
        description = description[:197] + "..."
    
    return title, url, description


def build_index(kb_directory: str) -> Dict[str, Dict[str, str]]:
    """Build index of all articles"""
    index = {}
    
    # Walk through all markdown files
    for root, dirs, files in os.walk(kb_directory):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                try:
                    title, url, description = extract_article_info(file_path)
                    if url:  # Only include articles with URLs
                        index[title] = {
                            "url": url,
                            "description": description,
                            "file_path": file_path.replace(kb_directory, "").lstrip("/")
                        }
                        print(f"✓ Indexed: {title}")
                    else:
                        print(f"✗ No URL found in: {file}")
                except Exception as e:
                    print(f"✗ Error processing {file}: {e}")
    
    return index


def main():
    """Build and save the article index"""
    # Get the KB directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    kb_dir = project_root / "data" / "knowledge_base" / "learning_center"
    
    if not kb_dir.exists():
        print(f"Error: KB directory not found at {kb_dir}")
        return
    
    print(f"Building index from: {kb_dir}")
    print("-" * 50)
    
    # Build the index
    index = build_index(str(kb_dir))
    
    # Save the index
    output_path = project_root / "data" / "knowledge_base" / "article_index.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
    
    print("-" * 50)
    print(f"✅ Index built successfully!")
    print(f"Total articles indexed: {len(index)}")
    print(f"Index saved to: {output_path}")
    
    # Show sample entries
    print("\nSample entries:")
    for i, (title, info) in enumerate(list(index.items())[:3]):
        print(f"\n{i+1}. {title}")
        print(f"   URL: {info['url']}")
        print(f"   Description: {info['description'][:100]}...")


if __name__ == "__main__":
    main()