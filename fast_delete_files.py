#!/usr/bin/env python3
"""
Fast batch delete OpenAI files with better progress tracking
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def delete_file(file_id, filename):
    """Delete a single file"""
    try:
        client.files.delete(file_id)
        return True, filename
    except Exception as e:
        return False, f"{filename}: {str(e)}"

def delete_files_parallel():
    """Delete files in parallel for faster processing"""
    try:
        # List all files
        print("Fetching list of files...")
        files = client.files.list()
        file_list = list(files)
        
        total_files = len(file_list)
        print(f"Found {total_files} files to delete.")
        
        if total_files == 0:
            print("No files to delete!")
            return
        
        print("Starting parallel deletion (10 threads)...")
        
        deleted_count = 0
        failed_count = 0
        
        # Use thread pool for parallel deletion
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit all deletion tasks
            future_to_file = {
                executor.submit(delete_file, file.id, file.filename): file 
                for file in file_list
            }
            
            # Process completed deletions
            for i, future in enumerate(as_completed(future_to_file)):
                success, result = future.result()
                
                if success:
                    deleted_count += 1
                else:
                    failed_count += 1
                    print(f"Failed: {result}")
                
                # Show progress
                if (i + 1) % 100 == 0 or (i + 1) == total_files:
                    print(f"Progress: {i + 1}/{total_files} ({deleted_count} deleted, {failed_count} failed)")
        
        print(f"\n{'='*60}")
        print(f"Deletion complete!")
        print(f"- Total files: {total_files}")
        print(f"- Successfully deleted: {deleted_count}")
        print(f"- Failed: {failed_count}")
        
        # Verify remaining files
        print("\nVerifying remaining files...")
        remaining_files = list(client.files.list())
        print(f"Files remaining: {len(remaining_files)}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("OpenAI Fast File Deletion")
    print("="*60)
    
    start_time = time.time()
    delete_files_parallel()
    
    elapsed_time = time.time() - start_time
    print(f"\nTotal time: {elapsed_time:.1f} seconds")