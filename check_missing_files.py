#!/usr/bin/env python3
"""
Check the specific files that failed to upload
"""
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Get current uploaded files
uploaded = set(f.filename for f in client.files.list())

# Missing article numbers from the debug output
missing_nums = [41, 92, 121, 142, 143, 146, 153, 171, 187, 227, 236, 238, 271, 323]

print("CHECKING MISSING FILES:")
print("="*60)

kb_dir = Path("knowledge_base_markdown/learning_center")

for num in missing_nums:
    # Find file with this number
    pattern = f"article_{num:03d}_*.md"
    files = list(kb_dir.glob(pattern))
    
    if files:
        file_path = files[0]
        print(f"\n{file_path.name}")
        print(f"  Size: {file_path.stat().st_size:,} bytes")
        print(f"  Name length: {len(file_path.name)} chars")
        print(f"  Underscores: {file_path.name.count('_')}")
        
        # Check if already uploaded under different name
        if file_path.name in uploaded:
            print(f"  ✅ Already uploaded!")
        else:
            print(f"  ❌ Not uploaded")
            
            # Try to find similar names
            article_num = f"article_{num}"
            similar = [u for u in uploaded if article_num in u]
            if similar:
                print(f"  Similar file uploaded: {similar[0]}")
    else:
        print(f"\n❌ No file found for article {num}")

# Now let's try to upload the remaining files one by one
print("\n\nATTEMPTING INDIVIDUAL UPLOADS:")
print("="*60)

failed_files = []
for num in missing_nums[:5]:  # Try first 5
    pattern = f"article_{num:03d}_*.md"
    files = list(kb_dir.glob(pattern))
    
    if files and files[0].name not in uploaded:
        file_path = files[0]
        print(f"\nUploading {file_path.name}...")
        
        try:
            with open(file_path, 'rb') as f:
                response = client.files.create(
                    file=f,
                    purpose='assistants'
                )
                print(f"  ✅ Success! ID: {response.id}")
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            failed_files.append((file_path.name, str(e)))

if failed_files:
    print("\n\nFAILED UPLOADS:")
    for name, error in failed_files:
        print(f"  {name}: {error}")