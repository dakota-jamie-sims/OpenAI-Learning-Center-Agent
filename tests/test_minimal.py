#!/usr/bin/env python3
"""Minimal test to check if file writing works."""

import os

# Test basic file writing
test_content = """---
title: Test Article
date: 2025-08-09
word_count: 100
reading_time: 1 minute
---

# Test Article

This is a test article to check if file writing works properly.

## Key Insights at a Glance
- Test insight 1
- Test insight 2

## Main Content
Some content here.

## Key Takeaways
- Test takeaway

## Conclusion
Test conclusion.
"""

try:
    # Test 1: Write to current directory
    with open("test_write.md", "w") as f:
        f.write(test_content)
    print("✓ Successfully wrote test_write.md")
    
    # Test 2: Check if file exists
    if os.path.exists("test_write.md"):
        print("✓ File exists")
        with open("test_write.md", "r") as f:
            content = f.read()
        print(f"✓ File contains {len(content)} characters")
        os.remove("test_write.md")
        print("✓ File removed")
    
    # Test 3: Test write function from utils
    from src.utils.files import write_text
    write_text("test_utils.md", test_content)
    print("✓ Utils write_text works")
    
    if os.path.exists("test_utils.md"):
        print("✓ Utils file created")
        os.remove("test_utils.md")
        
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print(f"\nCurrent directory: {os.getcwd()}")
print(f"Directory writable: {os.access('.', os.W_OK)}")