#!/usr/bin/env python3
"""
Update Knowledge Base Script
Add new files to the existing vector store
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import argparse

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from openai import OpenAI
from src.tools.vector_store_handler import VectorStoreHandler


def add_files_to_vector_store(file_paths: list, vector_store_id: str):
    """Add new files to existing vector store"""
    load_dotenv()
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in environment")
        return
    
    # Initialize client
    client = OpenAI(api_key=api_key)
    
    print(f"📦 Adding files to vector store: {vector_store_id}")
    print("=" * 50)
    
    # Upload and add files
    uploaded_file_ids = []
    for file_path in file_paths:
        path = Path(file_path)
        if not path.exists():
            print(f"❌ File not found: {file_path}")
            continue
            
        try:
            # Upload file
            with open(path, 'rb') as f:
                file_obj = client.files.create(
                    file=f,
                    purpose='assistants'
                )
            uploaded_file_ids.append(file_obj.id)
            print(f"✅ Uploaded: {path.name} ({file_obj.id})")
            
        except Exception as e:
            print(f"❌ Failed to upload {path.name}: {e}")
    
    if uploaded_file_ids:
        # Add files to vector store
        try:
            client.vector_stores.file_batches.create(
                vector_store_id=vector_store_id,
                file_ids=uploaded_file_ids
            )
            print(f"\n✅ Successfully added {len(uploaded_file_ids)} files to vector store")
        except Exception as e:
            print(f"❌ Failed to add files to vector store: {e}")
    else:
        print("❌ No files were uploaded")


def add_directory_to_vector_store(directory_path: str, vector_store_id: str, extensions: list = None):
    """Add all files from a directory to vector store"""
    if extensions is None:
        extensions = ['.md', '.txt']
    
    dir_path = Path(directory_path)
    if not dir_path.exists():
        print(f"❌ Directory not found: {directory_path}")
        return
    
    # Find all files with specified extensions
    files = []
    for ext in extensions:
        files.extend(dir_path.rglob(f"*{ext}"))
    
    if not files:
        print(f"❌ No files with extensions {extensions} found in {directory_path}")
        return
    
    print(f"📚 Found {len(files)} files to add")
    file_paths = [str(f) for f in files]
    add_files_to_vector_store(file_paths, vector_store_id)


def list_vector_store_contents(vector_store_id: str):
    """List all files currently in the vector store"""
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found")
        return
    
    client = OpenAI(api_key=api_key)
    
    try:
        # Get vector store details
        store = client.vector_stores.retrieve(vector_store_id)
        print(f"\n📦 Vector Store: {store.name}")
        print(f"ID: {store.id}")
        print(f"File Count: {store.file_counts.total}")
        print(f"Status: {store.status}")
        print("=" * 50)
        
        # List files
        files = client.vector_stores.files.list(
            vector_store_id=vector_store_id,
            limit=100
        )
        
        print("\n📄 Files in Vector Store:")
        for i, file in enumerate(files.data, 1):
            print(f"{i:3}. {file.id} - Status: {file.status}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Update Dakota Knowledge Base Vector Store")
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Add files command
    add_parser = subparsers.add_parser('add', help='Add files to vector store')
    add_parser.add_argument('files', nargs='+', help='File paths to add')
    add_parser.add_argument('--store-id', help='Vector store ID (defaults to .env value)')
    
    # Add directory command
    dir_parser = subparsers.add_parser('add-dir', help='Add directory to vector store')
    dir_parser.add_argument('directory', help='Directory path to add')
    dir_parser.add_argument('--extensions', nargs='+', default=['.md', '.txt'],
                          help='File extensions to include (default: .md .txt)')
    dir_parser.add_argument('--store-id', help='Vector store ID (defaults to .env value)')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List vector store contents')
    list_parser.add_argument('--store-id', help='Vector store ID (defaults to .env value)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Load environment
    load_dotenv()
    
    # Get vector store ID
    vector_store_id = args.store_id if hasattr(args, 'store_id') and args.store_id else os.getenv("VECTOR_STORE_ID")
    if not vector_store_id:
        print("❌ Error: No vector store ID found")
        print("Run 'python setup_vector_store.py' first or provide --store-id")
        return
    
    # Execute command
    if args.command == 'add':
        add_files_to_vector_store(args.files, vector_store_id)
    elif args.command == 'add-dir':
        add_directory_to_vector_store(args.directory, vector_store_id, args.extensions)
    elif args.command == 'list':
        list_vector_store_contents(vector_store_id)


if __name__ == "__main__":
    main()