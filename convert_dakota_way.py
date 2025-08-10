#!/usr/bin/env python3
"""
Convert Dakota Way files to proper Markdown format
"""
import json
from pathlib import Path
import re

def clean_text(text):
    """Clean up text formatting"""
    if not text:
        return ""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    return text.strip()

def convert_dakota_way_complete():
    """Convert the complete Dakota Way book to markdown"""
    with open('knowledge_base/dakota_way/dakota_way_complete.json', 'r') as f:
        data = json.load(f)
    
    md_lines = []
    
    # Title and metadata
    md_lines.append("# The Dakota Way")
    md_lines.append("")
    md_lines.append("*The complete guide to Dakota's relationship-focused approach to investment sales*")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    
    # Table of contents
    if 'table_of_contents' in data:
        md_lines.append("## Table of Contents")
        md_lines.append("")
        for item in data['table_of_contents']:
            chapter_num = item.get('chapter_number', '')
            # Don't include the faulty title from the JSON
            md_lines.append(f"- Chapter {chapter_num}")
        md_lines.append("")
    
    # Process chapters
    if 'chapters' in data:
        for chapter in data['chapters']:
            chapter_num = chapter.get('chapter_number', '')
            title = chapter.get('title', '').strip()
            
            # Chapter heading
            if title:
                md_lines.append(f"## Chapter {chapter_num}: {title}")
            else:
                md_lines.append(f"## Chapter {chapter_num}")
            md_lines.append("")
            
            # Chapter content
            content = chapter.get('content', [])
            if isinstance(content, list):
                for section in content:
                    if isinstance(section, dict):
                        if 'heading' in section:
                            md_lines.append(f"### {section['heading']}")
                            md_lines.append("")
                        if 'text' in section:
                            md_lines.append(clean_text(section['text']))
                            md_lines.append("")
                        if 'content' in section:
                            md_lines.append(clean_text(section['content']))
                            md_lines.append("")
                    elif isinstance(section, str):
                        md_lines.append(clean_text(section))
                        md_lines.append("")
            elif isinstance(content, str):
                md_lines.append(clean_text(content))
                md_lines.append("")
            
            # Add chapter separator
            md_lines.append("---")
            md_lines.append("")
    
    # Footer
    md_lines.append("*The Dakota Way - Building lasting relationships in investment sales*")
    
    return '\n'.join(md_lines)

def convert_dakota_way_quick_reference():
    """Convert the quick reference guide to markdown"""
    with open('knowledge_base/dakota_way/dakota_way_quick_reference.json', 'r') as f:
        data = json.load(f)
    
    md_lines = []
    
    # Title
    md_lines.append("# Dakota Way Quick Reference")
    md_lines.append("")
    md_lines.append("*Key principles and strategies from The Dakota Way*")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    
    # Process the content based on structure
    if 'quick_reference' in data:
        ref_data = data['quick_reference']
        
        # Key principles
        if 'key_principles' in ref_data:
            md_lines.append("## Key Principles")
            md_lines.append("")
            for principle in ref_data['key_principles']:
                if isinstance(principle, dict):
                    name = principle.get('name', '')
                    description = principle.get('description', '')
                    md_lines.append(f"### {name}")
                    md_lines.append(f"{description}")
                    md_lines.append("")
                else:
                    md_lines.append(f"- {principle}")
                    md_lines.append("")
        
        # Best practices
        if 'best_practices' in ref_data:
            md_lines.append("## Best Practices")
            md_lines.append("")
            for practice in ref_data['best_practices']:
                if isinstance(practice, dict):
                    title = practice.get('title', '')
                    content = practice.get('content', '')
                    md_lines.append(f"### {title}")
                    md_lines.append(f"{content}")
                    md_lines.append("")
                else:
                    md_lines.append(f"- {practice}")
                    md_lines.append("")
    
    # If structure is different, just process all content
    else:
        for key, value in data.items():
            if isinstance(value, dict) or isinstance(value, list):
                md_lines.append(f"## {key.replace('_', ' ').title()}")
                md_lines.append("")
                md_lines.append(json.dumps(value, indent=2))
                md_lines.append("")
    
    # Footer
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("*Dakota Way Quick Reference Guide*")
    
    return '\n'.join(md_lines)

def main():
    """Convert and clean up Dakota Way files"""
    output_dir = Path("knowledge_base_markdown/dakota_way")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Converting Dakota Way files...")
    
    # Convert complete book
    try:
        complete_content = convert_dakota_way_complete()
        with open(output_dir / "dakota_way_complete.md", 'w', encoding='utf-8') as f:
            f.write(complete_content)
        print("✓ Converted dakota_way_complete.md")
    except Exception as e:
        print(f"✗ Failed to convert complete book: {e}")
    
    # Convert quick reference
    try:
        quick_ref_content = convert_dakota_way_quick_reference()
        with open(output_dir / "dakota_way_quick_reference.md", 'w', encoding='utf-8') as f:
            f.write(quick_ref_content)
        print("✓ Converted dakota_way_quick_reference.md")
    except Exception as e:
        print(f"✗ Failed to convert quick reference: {e}")
    
    # Remove redundant files
    print("\nRemoving redundant files...")
    redundant_files = [
        "dakota_way_chapter_001_.md",
        "dakota_way_chapter_002_chapter-1.md",
        "dakota_way_chapter_003_chapter-2.md",
        "dakota_way_chapter_004_chapter-3.md",
        "dakota_way_chapter_005_chapter-4.md",
        "dakota_way_chapter_006_chapter-5.md",
        "integration_config.md"
    ]
    
    for filename in redundant_files:
        filepath = output_dir / filename
        if filepath.exists():
            filepath.unlink()
            print(f"✓ Removed {filename}")
    
    print("\nDakota Way conversion complete!")
    print(f"Output directory: {output_dir}")
    
    # Show file sizes
    print("\nFinal files:")
    for md_file in output_dir.glob("*.md"):
        size = md_file.stat().st_size
        print(f"- {md_file.name}: {size:,} bytes")

if __name__ == "__main__":
    main()