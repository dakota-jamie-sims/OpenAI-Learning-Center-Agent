#!/usr/bin/env python3
"""
Batch delete all OpenAI files
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def delete_all_files():
    """Delete all files from OpenAI storage"""
    try:
        # List all files
        print("Fetching list of files...")
        files = client.files.list()
        file_list = list(files)
        
        print(f"Found {len(file_list)} files to delete.")
        print("Starting batch deletion...")
        
        # Delete each file
        deleted_count = 0
        failed_count = 0
        failed_files = []
        
        for i, file in enumerate(file_list):
            try:
                client.files.delete(file.id)
                deleted_count += 1
                
                # Show progress every 10 files
                if (i + 1) % 10 == 0:
                    print(f"Progress: {i + 1}/{len(file_list)} files processed ({deleted_count} deleted, {failed_count} failed)")
                
                # Rate limiting - pause briefly every 50 files
                if (i + 1) % 50 == 0:
                    time.sleep(1)
                    
            except Exception as e:
                failed_count += 1
                failed_files.append((file.filename, str(e)))
        
        print(f"\n{'='*60}")
        print(f"Deletion complete!")
        print(f"- Total files: {len(file_list)}")
        print(f"- Successfully deleted: {deleted_count}")
        print(f"- Failed: {failed_count}")
        
        if failed_files:
            print(f"\nFirst 10 failed deletions:")
            for filename, error in failed_files[:10]:
                print(f"  - {filename}: {error}")
        
        # Verify remaining files
        print("\nVerifying remaining files...")
        remaining_files = list(client.files.list())
        print(f"Files remaining: {len(remaining_files)}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("OpenAI Batch File Deletion")
    print("="*60)
    print("WARNING: This will delete ALL files from your OpenAI storage!")
    print("Starting in 5 seconds... (Ctrl+C to cancel)")
    
    try:
        for i in range(5, 0, -1):
            print(f"{i}...")
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nCancelled!")
        exit(0)
    
    delete_all_files()