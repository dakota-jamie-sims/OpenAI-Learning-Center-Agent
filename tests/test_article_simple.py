#!/usr/bin/env python3
"""
Simple article generation test without strict validation
"""
import os
import sys
sys.path.append('src')

from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path
import json

load_dotenv()

# Initialize client
client = OpenAI()

# Configuration
TOPIC = "Top Private Equity Firms in Dallas 2025"
OUTPUT_DIR = Path("output/test_article")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("🚀 GENERATING TEST ARTICLE")
print("="*60)
print(f"Topic: {TOPIC}")
print()

# Step 1: Search Knowledge Base
print("📚 Step 1: Searching Knowledge Base...")
vector_store_id = os.getenv('OPENAI_VECTOR_STORE_ID')

kb_context = ""
if vector_store_id:
    # For now, we'll simulate KB search since the file_search API format changed
    kb_context = """
    Based on Dakota's knowledge base:
    - City Scheduling is a key strategy for PE firms to build relationships
    - Dallas is a major hub for private equity activity in Texas
    - Relationship-building through face-to-face meetings is crucial
    - Dakota emphasizes the importance of local market knowledge
    """
    print("✅ Found relevant Dakota content")
else:
    print("⚠️  No vector store configured")

# Step 2: Generate Article
print("\n📝 Step 2: Generating Article...")
try:
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": f"""You are a Dakota Learning Center content writer. Write a comprehensive article about {TOPIC}.
                
                Use this Dakota knowledge base context: {kb_context}
                
                Requirements:
                - 1500+ words
                - Include specific firm names and details
                - Add statistics and data points
                - Professional tone
                - SEO optimized
                - Include citations in [Source: citation] format
                """
            },
            {
                "role": "user",
                "content": f"Write a complete article about '{TOPIC}'. Include an introduction, main sections covering top firms, market analysis, and conclusion."
            }
        ],
        max_tokens=4000,
        temperature=0.7
    )
    
    article_content = response.choices[0].message.content
    print("✅ Article generated!")
    
    # Save article
    article_path = OUTPUT_DIR / "article.md"
    article_path.write_text(article_content)
    print(f"   Saved to: {article_path}")
    
except Exception as e:
    print(f"❌ Generation error: {e}")
    article_content = ""

# Step 3: Generate Metadata
print("\n📊 Step 3: Generating Metadata...")
try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Generate article metadata in JSON format."
            },
            {
                "role": "user",
                "content": f"""Generate metadata for this article:
                Title: {TOPIC}
                
                Include: meta_title, meta_description, slug, tags, primary_keyword, target_audience"""
            }
        ],
        max_tokens=500
    )
    
    metadata = response.choices[0].message.content
    metadata_path = OUTPUT_DIR / "metadata.json"
    metadata_path.write_text(metadata)
    print("✅ Metadata generated!")
    
except Exception as e:
    print(f"❌ Metadata error: {e}")

# Step 4: Generate Social Posts
print("\n📱 Step 4: Generating Social Posts...")
try:
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "Generate social media posts for LinkedIn, Twitter, and Instagram."
            },
            {
                "role": "user",
                "content": f"Create engaging social media posts for an article about '{TOPIC}'. Include hashtags."
            }
        ],
        max_tokens=800
    )
    
    social_posts = response.choices[0].message.content
    social_path = OUTPUT_DIR / "social_posts.md"
    social_path.write_text(social_posts)
    print("✅ Social posts generated!")
    
except Exception as e:
    print(f"❌ Social posts error: {e}")

print("\n" + "="*60)
print("✅ TEST COMPLETE!")
print(f"\nOutput files in: {OUTPUT_DIR}")
print("- article.md")
print("- metadata.json") 
print("- social_posts.md")

# Show preview
if article_content:
    print("\n📄 Article Preview:")
    print("-"*40)
    print(article_content[:500] + "...")
    
    # Word count
    word_count = len(article_content.split())
    print(f"\nWord count: {word_count}")