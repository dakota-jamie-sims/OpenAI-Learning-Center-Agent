#!/usr/bin/env python3
"""
Analyze specific files that failed to upload
"""
from pathlib import Path
import os

failed_files = [
    "article_167_5_benefits_to_video.md",
    "article_286_financial_advisor_and_ria.md",
    "article_140_top-10-family-offices-in-italy.md",
    "article_137_top-10-family-offices-in-norway.md",
    "article_195_5_key_features_to.md",
    "article_072_consultant_led_private_equity.md",
    "article_019_what_happened_in_the.md",
    "article_042_how_to_create_a.md",
    "article_245_the_top_15_largest.md",
    "article_205_the-top-10-rias-in-seattle.md"
]

def analyze_failed_files():
    """Analyze why specific files failed"""
    kb_dir = Path("knowledge_base_markdown/learning_center")
    
    print("ANALYZING FAILED FILES:")
    print("="*60)
    
    for filename in failed_files:
        file_path = kb_dir / filename
        
        if not file_path.exists():
            print(f"\n❌ {filename}")
            print("   File does not exist!")
            continue
            
        print(f"\n📄 {filename}")
        
        # File size
        size = file_path.stat().st_size
        print(f"   Size: {size:,} bytes ({size/1024:.1f} KB)")
        
        # Check filename characteristics
        print(f"   Length: {len(filename)} chars")
        print(f"   Has hyphens: {'-' in filename}")
        print(f"   Has underscores: {'_' in filename}")
        
        # Check first few lines of content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()[:5]
                print("   First line:", lines[0].strip() if lines else "EMPTY")
                
                # Check for any unusual characters
                content = f.read()
                unusual_chars = set()
                for char in content:
                    if ord(char) > 127 or (ord(char) < 32 and char not in '\n\r\t'):
                        unusual_chars.add(char)
                
                if unusual_chars:
                    print(f"   Unusual characters found: {unusual_chars}")
                    
        except Exception as e:
            print(f"   Error reading file: {e}")
    
    # Look for patterns
    print(f"\n\nPATTERNS IN FAILED FILES:")
    print("="*60)
    
    # Check if these are duplicates
    print("\nChecking for potential duplicates...")
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    uploaded_files = list(client.files.list())
    uploaded_names = [f.filename for f in uploaded_files]
    
    for failed in failed_files:
        # Check if a similar file was uploaded
        article_num = failed.split('_')[1]
        similar = [u for u in uploaded_names if f"article_{article_num}_" in u]
        if similar:
            print(f"\n{failed}")
            print(f"  Similar file uploaded: {similar[0]}")

if __name__ == "__main__":
    analyze_failed_files()
    
    # Also check all files for mixed naming
    print(f"\n\nCHECKING ALL FILES FOR MIXED NAMING:")
    print("="*60)
    
    kb_dir = Path("knowledge_base_markdown/learning_center")
    mixed_naming = []
    
    for file_path in kb_dir.glob("*.md"):
        filename = file_path.name
        if '-' in filename and '_' in filename:
            # Skip the article number part
            parts = filename.split('_', 2)
            if len(parts) >= 3 and '-' in parts[2]:
                mixed_naming.append(filename)
    
    print(f"Files with mixed hyphens and underscores: {len(mixed_naming)}")
    if mixed_naming:
        print("Examples:")
        for f in mixed_naming[:10]:
            print(f"  - {f}")