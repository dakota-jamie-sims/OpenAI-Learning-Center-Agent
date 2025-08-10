#!/usr/bin/env python3
"""
Delete all files from OpenAI storage
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
        
        if not file_list:
            print("No files found to delete.")
            return
        
        print(f"Found {len(file_list)} files to delete.")
        
        # Confirm before deletion
        response = input(f"Are you sure you want to delete all {len(file_list)} files? (yes/no): ")
        if response.lower() != 'yes':
            print("Deletion cancelled.")
            return
        
        # Delete each file
        deleted_count = 0
        failed_count = 0
        
        for file in file_list:
            try:
                client.files.delete(file.id)
                deleted_count += 1
                print(f"Deleted: {file.filename} ({file.id})")
                
                # Rate limiting - OpenAI allows 500 requests per minute
                if deleted_count % 50 == 0:
                    print(f"Deleted {deleted_count} files so far...")
                    time.sleep(1)  # Brief pause every 50 files
                    
            except Exception as e:
                failed_count += 1
                print(f"Failed to delete {file.filename}: {e}")
        
        print(f"\n{'='*60}")
        print(f"Deletion complete!")
        print(f"- Successfully deleted: {deleted_count} files")
        print(f"- Failed: {failed_count} files")
        
    except Exception as e:
        print(f"Error: {e}")

def list_files_summary():
    """List a summary of current files"""
    try:
        files = client.files.list()
        file_list = list(files)
        
        if not file_list:
            print("No files found.")
            return
        
        print(f"Total files: {len(file_list)}")
        print("\nFirst 10 files:")
        for i, file in enumerate(file_list[:10]):
            print(f"- {file.filename} (created: {file.created_at})")
        
        if len(file_list) > 10:
            print(f"... and {len(file_list) - 10} more files")
            
    except Exception as e:
        print(f"Error listing files: {e}")

if __name__ == "__main__":
    print("OpenAI File Manager")
    print("="*60)
    
    # First show summary
    list_files_summary()
    
    print("\n" + "="*60)
    print("\nOptions:")
    print("1. Delete all files")
    print("2. Exit")
    
    choice = input("\nEnter your choice (1 or 2): ")
    
    if choice == "1":
        delete_all_files()
    else:
        print("Exiting without changes.")