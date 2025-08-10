#!/usr/bin/env python3
"""
Reformat and re-upload knowledge base files for optimal vector store performance
"""
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

def convert_json_to_markdown(json_path):
    """Convert JSON article to markdown format"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract fields
    title = data.get('title', 'Untitled')
    content = data.get('content', '')
    url = data.get('url', '')
    date = data.get('date', '')
    author = data.get('author', '')
    topics = data.get('topics', [])
    
    # Create markdown
    markdown = f"# {title}\n\n"
    
    if date:
        markdown += f"**Date:** {date}\n"
    if author:
        markdown += f"**Author:** {author}\n"
    if url:
        markdown += f"**URL:** {url}\n"
    if topics:
        markdown += f"**Topics:** {', '.join(topics)}\n"
    
    markdown += "\n---\n\n"
    markdown += content
    
    return markdown, title

def create_optimized_vector_store():
    """Create a new optimized vector store with properly formatted files"""
    client = OpenAI()
    
    print("Creating new optimized vector store...")
    vector_store = client.vector_stores.create(
        name="Dakota Knowledge Base - Optimized for Responses API"
    )
    vector_store_id = vector_store.id
    print(f"Created vector store: {vector_store_id}")
    
    # Process knowledge base files
    kb_path = Path("knowledge_base")
    all_files = []
    
    # Collect all files
    json_files = list(kb_path.rglob("*.json"))
    txt_files = list(kb_path.rglob("*.txt"))
    md_files = list(kb_path.rglob("*.md"))
    
    print(f"\nFound:")
    print(f"- {len(json_files)} JSON files")
    print(f"- {len(txt_files)} TXT files") 
    print(f"- {len(md_files)} MD files")
    
    # Convert and upload files
    uploaded_count = 0
    batch_size = 20
    file_batch = []
    
    print("\nConverting JSON to Markdown and uploading...")
    
    # Process JSON files first (convert to markdown)
    for json_path in json_files:
        try:
            markdown_content, title = convert_json_to_markdown(json_path)
            
            # Upload as markdown
            file_obj = client.files.create(
                file=(f"{json_path.stem}.md", markdown_content.encode('utf-8')),
                purpose='assistants'  # Still need to use assistants for vector stores
            )
            
            file_batch.append(file_obj.id)
            uploaded_count += 1
            
            if len(file_batch) >= batch_size:
                # Add batch to vector store
                client.vector_stores.file_batches.create(
                    vector_store_id=vector_store_id,
                    file_ids=file_batch
                )
                print(f"  ✓ Uploaded batch of {len(file_batch)} files ({uploaded_count} total)")
                file_batch = []
                
        except Exception as e:
            print(f"  ✗ Error processing {json_path}: {e}")
    
    # Upload remaining TXT and MD files
    print("\nUploading text and markdown files...")
    
    for file_path in txt_files + md_files:
        try:
            with open(file_path, 'rb') as f:
                file_obj = client.files.create(
                    file=f,
                    purpose='assistants'
                )
            
            file_batch.append(file_obj.id)
            uploaded_count += 1
            
            if len(file_batch) >= batch_size:
                client.vector_stores.file_batches.create(
                    vector_store_id=vector_store_id,
                    file_ids=file_batch
                )
                print(f"  ✓ Uploaded batch of {len(file_batch)} files ({uploaded_count} total)")
                file_batch = []
                
        except Exception as e:
            print(f"  ✗ Error uploading {file_path}: {e}")
    
    # Upload final batch
    if file_batch:
        client.vector_stores.file_batches.create(
            vector_store_id=vector_store_id,
            file_ids=file_batch
        )
        print(f"  ✓ Uploaded final batch of {len(file_batch)} files")
    
    print(f"\n{'='*60}")
    print(f"Optimization complete!")
    print(f"- Total files uploaded: {uploaded_count}")
    print(f"- New vector store ID: {vector_store_id}")
    print(f"\nUpdate your .env file with:")
    print(f"VECTOR_STORE_ID={vector_store_id}")
    
    return vector_store_id

def check_file_purposes():
    """Check the purpose of files in current vector store"""
    client = OpenAI()
    
    # Get a sample of files
    response = client.vector_stores.files.list(
        vector_store_id=os.getenv("VECTOR_STORE_ID"),
        limit=10
    )
    
    print("Sample of current files:")
    for file in response.data:
        try:
            file_details = client.files.retrieve(file.id)
            print(f"- {file_details.filename}: purpose={file_details.purpose}")
        except:
            pass

if __name__ == "__main__":
    print("Current vector store analysis:")
    print("="*60)
    check_file_purposes()
    
    print("\n" + "="*60)
    response = input("\nThe files are uploaded with purpose='assistants' which is correct for vector stores.\nHowever, we can optimize by converting JSON to Markdown.\nCreate optimized vector store? (y/N): ")
    
    if response.lower() == 'y':
        new_id = create_optimized_vector_store()
    else:
        print("Keeping current vector store.")