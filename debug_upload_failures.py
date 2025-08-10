#!/usr/bin/env python3
"""
Debug why files are failing to upload
"""
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_current_state():
    """Analyze what's uploaded vs what's local"""
    
    # Get uploaded files
    print("Checking OpenAI files...")
    uploaded_files = list(client.files.list())
    uploaded_names = set(f.filename for f in uploaded_files)
    print(f"Files in OpenAI: {len(uploaded_files)}")
    
    # Get local files
    kb_dir = Path("knowledge_base_markdown")
    local_files = list(kb_dir.rglob("*.md"))
    local_names = set(f.name for f in local_files)
    print(f"Local files: {len(local_files)}")
    
    # Find what didn't upload
    not_uploaded = local_names - uploaded_names
    print(f"Files that failed to upload: {len(not_uploaded)}")
    
    if not_uploaded:
        print("\nAnalyzing failed files...")
        
        # Group by characteristics
        failed_paths = [f for f in local_files if f.name in not_uploaded]
        
        # Check file sizes
        sizes = [(f.stat().st_size, f.name) for f in failed_paths]
        sizes.sort(reverse=True)
        
        print("\nLargest failed files:")
        for size, name in sizes[:5]:
            print(f"  {name}: {size:,} bytes ({size/1024:.1f} KB)")
        
        print("\nSmallest failed files:")
        for size, name in sizes[-5:]:
            print(f"  {name}: {size:,} bytes")
        
        # Check for patterns in names
        print("\nFailed file name patterns:")
        patterns = {}
        for name in not_uploaded:
            # Check various characteristics
            if len(name) > 60:
                patterns.setdefault('long_names', []).append(name)
            if name.count('_') > 5:
                patterns.setdefault('many_underscores', []).append(name)
            if any(ord(c) > 127 for c in name):
                patterns.setdefault('non_ascii', []).append(name)
            
            # Check article numbers
            if name.startswith('article_'):
                try:
                    num = int(name.split('_')[1])
                    if num < 100:
                        patterns.setdefault('low_numbers', []).append(name)
                    elif num > 300:
                        patterns.setdefault('high_numbers', []).append(name)
                except:
                    patterns.setdefault('bad_number', []).append(name)
        
        for pattern, files in patterns.items():
            if files:
                print(f"\n{pattern}: {len(files)} files")
                for f in files[:3]:
                    print(f"  - {f}")
        
        # Sample some failed files to check content
        print("\nChecking content of failed files...")
        for f in failed_paths[:3]:
            try:
                with open(f, 'rb') as file:
                    content = file.read()
                    # Check for BOM or other issues
                    if content.startswith(b'\xef\xbb\xbf'):
                        print(f"  {f.name}: Has UTF-8 BOM")
                    if b'\x00' in content:
                        print(f"  {f.name}: Contains null bytes")
                    if not content:
                        print(f"  {f.name}: Empty file")
            except Exception as e:
                print(f"  {f.name}: Error reading - {e}")
    
    # Check successful uploads
    if uploaded_files:
        print(f"\n\nSuccessfully uploaded {len(uploaded_files)} files")
        # Check patterns in successful uploads
        success_nums = []
        for name in uploaded_names:
            if name.startswith('article_'):
                try:
                    num = int(name.split('_')[1])
                    success_nums.append(num)
                except:
                    pass
        
        if success_nums:
            success_nums.sort()
            print(f"Article number range: {min(success_nums)} - {max(success_nums)}")
            
            # Find gaps
            all_nums = set(range(min(success_nums), max(success_nums) + 1))
            missing_nums = all_nums - set(success_nums)
            if missing_nums:
                print(f"Missing article numbers: {sorted(missing_nums)[:10]}...")

def test_individual_upload():
    """Try uploading a single failed file to see the error"""
    kb_dir = Path("knowledge_base_markdown")
    local_files = list(kb_dir.rglob("*.md"))
    
    # Get list of failed files
    uploaded_names = set(f.filename for f in client.files.list())
    failed_files = [f for f in local_files if f.name not in uploaded_names]
    
    if failed_files:
        test_file = failed_files[0]
        print(f"\n\nTesting individual upload of: {test_file.name}")
        print(f"File size: {test_file.stat().st_size} bytes")
        print(f"File path: {test_file}")
        
        try:
            with open(test_file, 'rb') as f:
                response = client.files.create(
                    file=f,
                    purpose='assistants'
                )
                print(f"✅ Upload successful! File ID: {response.id}")
        except Exception as e:
            print(f"❌ Upload failed with error: {type(e).__name__}: {e}")
            
            # Try with different purpose
            try:
                print("\nTrying with 'batch' purpose...")
                with open(test_file, 'rb') as f:
                    response = client.files.create(
                        file=f,
                        purpose='batch'
                    )
                    print(f"✅ Upload successful with 'batch' purpose!")
            except Exception as e2:
                print(f"❌ Also failed with 'batch': {e2}")

if __name__ == "__main__":
    analyze_current_state()
    test_individual_upload()