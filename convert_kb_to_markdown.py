#!/usr/bin/env python3
"""
Convert knowledge base JSON files to Markdown format
"""
import json
from pathlib import Path
import re

def clean_html(text):
    """Remove HTML tags and clean up text"""
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Convert HTML entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&#39;', "'")
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n', '\n\n', text)
    return text.strip()

def json_to_markdown(json_path):
    """Convert a JSON article to well-formatted Markdown"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract metadata from meta section if it exists
    meta = data.get('meta', {})
    title = meta.get('title') or data.get('title', 'Untitled')
    url = meta.get('url') or data.get('url', '')
    date = meta.get('date') or data.get('date', '')
    author = meta.get('author') or data.get('author', '')
    topics = data.get('topics', [])
    
    # Extract content - handle both string and object formats
    content_data = data.get('content', {})
    if isinstance(content_data, str):
        content = clean_html(content_data)
    elif isinstance(content_data, dict):
        # Handle structured content
        parts = []
        if 'title' in content_data:
            # Title is already extracted
            pass
        if 'introduction' in content_data:
            parts.append(content_data['introduction'])
        if 'sections' in content_data:
            for section in content_data['sections']:
                if isinstance(section, dict):
                    if 'heading' in section:
                        parts.append(f"\n## {section['heading']}\n")
                    if 'content' in section:
                        parts.append(section['content'])
                    if 'text' in section:
                        parts.append(section['text'])
        if 'body' in content_data:
            parts.append(content_data['body'])
        if 'conclusion' in content_data:
            parts.append(content_data['conclusion'])
        
        content = clean_html('\n\n'.join(str(p) for p in parts if p))
    else:
        content = str(content)
    
    # Build markdown with proper formatting
    md_lines = []
    
    # Title
    md_lines.append(f"# {title}")
    md_lines.append("")
    
    # Metadata section
    if date or author or url:
        md_lines.append("## Article Information")
        if date:
            md_lines.append(f"- **Published:** {date}")
        if author and author != "Unknown":
            md_lines.append(f"- **Author:** {author}")
        if url:
            md_lines.append(f"- **Original URL:** {url}")
        if topics:
            md_lines.append(f"- **Topics:** {', '.join(topics)}")
        md_lines.append("")
    
    # Main content
    md_lines.append("## Content")
    md_lines.append("")
    
    # Format content with proper paragraphs
    paragraphs = content.split('\n\n')
    for para in paragraphs:
        if para.strip():
            md_lines.append(para.strip())
            md_lines.append("")
    
    # Add footer
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("*This article is part of the Dakota Learning Center knowledge base.*")
    
    return '\n'.join(md_lines)

def convert_all_files():
    """Convert all JSON files to Markdown"""
    kb_path = Path("knowledge_base")
    output_path = Path("knowledge_base_markdown")
    
    # Create output directories
    output_path.mkdir(exist_ok=True)
    (output_path / "learning_center").mkdir(exist_ok=True)
    (output_path / "dakota_way").mkdir(exist_ok=True)
    
    # Get all JSON files
    json_files = list(kb_path.rglob("*.json"))
    print(f"Found {len(json_files)} JSON files to convert")
    
    converted = 0
    failed = []
    
    for json_path in json_files:
        try:
            # Convert to markdown
            markdown_content = json_to_markdown(json_path)
            
            # Determine output path
            relative_path = json_path.relative_to(kb_path)
            md_path = output_path / relative_path.with_suffix('.md')
            
            # Ensure parent directory exists
            md_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write markdown file
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            converted += 1
            if converted % 50 == 0:
                print(f"  Converted {converted}/{len(json_files)} files...")
                
        except Exception as e:
            failed.append((str(json_path), str(e)))
    
    print(f"\n{'='*60}")
    print(f"Conversion Complete!")
    print(f"- Total files: {len(json_files)}")
    print(f"- Successfully converted: {converted}")
    print(f"- Failed: {len(failed)}")
    print(f"- Output directory: {output_path}")
    
    if failed:
        print(f"\nFailed conversions:")
        for path, error in failed[:5]:
            print(f"  - {path}: {error}")
        if len(failed) > 5:
            print(f"  ... and {len(failed) - 5} more")
    
    # Show sample
    print(f"\n{'='*60}")
    print("Sample converted file:")
    sample_file = list(output_path.glob("learning_center/*.md"))[0]
    with open(sample_file, 'r') as f:
        content = f.read()
        print(content[:500] + "..." if len(content) > 500 else content)

if __name__ == "__main__":
    convert_all_files()