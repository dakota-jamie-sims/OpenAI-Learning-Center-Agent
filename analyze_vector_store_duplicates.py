#!/usr/bin/env python3
"""
Analyze and remove duplicate files from vector store
"""
import os
from dotenv import load_dotenv
from openai import OpenAI
from collections import defaultdict
from datetime import datetime

load_dotenv()

def analyze_vector_store():
    """Analyze vector store for duplicates"""
    client = OpenAI()
    vector_store_id = os.getenv("VECTOR_STORE_ID")
    
    print(f"Analyzing vector store: {vector_store_id}")
    
    # Get all files from vector store
    all_files = []
    has_more = True
    after = None
    
    while has_more:
        if after:
            response = client.vector_stores.files.list(
                vector_store_id=vector_store_id,
                limit=100,
                after=after
            )
        else:
            response = client.vector_stores.files.list(
                vector_store_id=vector_store_id,
                limit=100
            )
        
        all_files.extend(response.data)
        has_more = response.has_more
        if response.data:
            after = response.data[-1].id
    
    print(f"Total files in vector store: {len(all_files)}")
    
    # Group files by name to find duplicates
    files_by_name = defaultdict(list)
    files_by_base_name = defaultdict(list)  # Group by base name without extension
    
    for file in all_files:
        try:
            # Get file details
            file_details = client.files.retrieve(file.id)
            filename = file_details.filename
            created_at = datetime.fromtimestamp(file_details.created_at)
            
            # Extract base name without extension
            base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
            
            file_info = {
                'id': file.id,
                'vs_file_id': file.id,
                'filename': filename,
                'base_name': base_name,
                'created_at': created_at,
                'status': file.status,
                'bytes': file_details.bytes if hasattr(file_details, 'bytes') else 0
            }
            
            files_by_name[filename].append(file_info)
            files_by_base_name[base_name].append(file_info)
            
        except Exception as e:
            print(f"Error retrieving file {file.id}: {e}")
    
    # Find duplicates
    duplicates = {name: files for name, files in files_by_name.items() if len(files) > 1}
    
    print(f"\nFound {len(duplicates)} duplicate filenames")
    
    # Find potential content duplicates (same base name, different extension)
    content_duplicates = {name: files for name, files in files_by_base_name.items() 
                         if len(files) > 1 and any(f['filename'].endswith('.json') for f in files)}
    
    print(f"Found {len(content_duplicates)} potential content duplicates (JSON/TXT pairs)")
    
    # Analyze duplicates
    files_to_remove = []
    
    for filename, file_list in duplicates.items():
        # Sort by created_at (newest first)
        file_list.sort(key=lambda x: x['created_at'], reverse=True)
        
        print(f"\nDuplicate: {filename}")
        for i, f in enumerate(file_list):
            status_emoji = "✅" if f['status'] == 'completed' else "⏳"
            keep = i == 0  # Keep the newest one
            print(f"  {'KEEP' if keep else 'REMOVE'} {status_emoji} {f['id']} - Created: {f['created_at']} - {f['bytes']} bytes")
            
            if not keep:
                files_to_remove.append(f['vs_file_id'])
    
    # Check content duplicates
    if content_duplicates:
        print(f"\n{'='*60}")
        print("Potential content duplicates (JSON converted to TXT):")
        for base_name, file_list in list(content_duplicates.items())[:10]:  # Show first 10
            print(f"\n{base_name}:")
            # Sort by created_at
            file_list.sort(key=lambda x: x['created_at'])
            
            # Generally keep TXT over JSON for better searchability
            has_txt = any(f['filename'].endswith('.txt') for f in file_list)
            has_json = any(f['filename'].endswith('.json') for f in file_list)
            
            for f in file_list:
                is_json = f['filename'].endswith('.json')
                should_remove = is_json and has_txt  # Remove JSON if we have TXT
                
                status_emoji = "✅" if f['status'] == 'completed' else "⏳"
                action = 'REMOVE' if should_remove else 'KEEP'
                print(f"  {action} {status_emoji} {f['filename']} - {f['created_at']} - {f['bytes']} bytes")
                
                if should_remove and f['status'] == 'completed':
                    files_to_remove.append(f['vs_file_id'])
    
    # Also check for truly duplicate content (files that were uploaded multiple times)
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"- Total files: {len(all_files)}")
    print(f"- Unique filenames: {len(files_by_name)}")
    print(f"- Duplicate filenames: {len(duplicates)}")
    print(f"- Files to remove: {len(files_to_remove)}")
    
    return files_to_remove, vector_store_id

def remove_duplicates(files_to_remove, vector_store_id):
    """Remove duplicate files from vector store"""
    if not files_to_remove:
        print("\nNo duplicates to remove!")
        return
    
    client = OpenAI()
    
    confirm = input(f"\nRemove {len(files_to_remove)} duplicate files? (y/N): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return
    
    print(f"\nRemoving {len(files_to_remove)} duplicate files...")
    
    removed_count = 0
    failed_count = 0
    
    # Remove in batches
    batch_size = 10
    for i in range(0, len(files_to_remove), batch_size):
        batch = files_to_remove[i:i+batch_size]
        
        for file_id in batch:
            try:
                client.vector_stores.files.delete(
                    vector_store_id=vector_store_id,
                    file_id=file_id
                )
                removed_count += 1
                print(f"  ✓ Removed {file_id}")
            except Exception as e:
                failed_count += 1
                print(f"  ✗ Failed to remove {file_id}: {e}")
    
    print(f"\n{'='*60}")
    print(f"Cleanup complete:")
    print(f"- Successfully removed: {removed_count}")
    print(f"- Failed to remove: {failed_count}")
    
    # Check final state
    try:
        store = client.vector_stores.retrieve(vector_store_id)
        print(f"\nVector store status:")
        print(f"- Total files now: {store.file_counts.total}")
        print(f"- Completed: {store.file_counts.completed}")
    except Exception as e:
        print(f"Error checking final state: {e}")

if __name__ == "__main__":
    files_to_remove, vector_store_id = analyze_vector_store()
    if files_to_remove:
        remove_duplicates(files_to_remove, vector_store_id)