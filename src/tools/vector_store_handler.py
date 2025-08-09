"""
Vector Store Handler for Knowledge Base
Integrates OpenAI's Vector Store with Chat Completions API
"""
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
from openai import OpenAI
import json


class VectorStoreHandler:
    """Handles vector store operations for knowledge base search"""
    
    def __init__(self, client: OpenAI):
        self.client = client
        self.vector_store_id = None
        self.file_ids = []
        
    def create_or_get_vector_store(self, name: str = "Dakota Knowledge Base") -> str:
        """Create or retrieve existing vector store"""
        # Check if we already have a vector store ID in env
        existing_id = os.getenv("VECTOR_STORE_ID")
        if existing_id:
            try:
                # Verify it still exists
                store = self.client.beta.vector_stores.retrieve(existing_id)
                self.vector_store_id = existing_id
                print(f"✅ Using existing vector store: {existing_id}")
                return existing_id
            except:
                print(f"⚠️ Existing vector store {existing_id} not found, creating new one")
        
        # Create new vector store
        vector_store = self.client.beta.vector_stores.create(name=name)
        self.vector_store_id = vector_store.id
        
        # Save to .env for future use
        self._save_vector_store_id(vector_store.id)
        
        print(f"✅ Created new vector store: {vector_store.id}")
        return vector_store.id
    
    def upload_knowledge_base(self, kb_directory: str, max_files: int = 100) -> List[str]:
        """Upload knowledge base files to vector store"""
        kb_path = Path(kb_directory)
        if not kb_path.exists():
            raise ValueError(f"Knowledge base directory not found: {kb_directory}")
        
        # Get all markdown files
        files = list(kb_path.rglob("*.md")) + list(kb_path.rglob("*.txt"))
        files = files[:max_files]  # Limit number of files
        
        print(f"📚 Uploading {len(files)} knowledge base files...")
        
        uploaded_files = []
        for file_path in files:
            try:
                # Upload file
                with open(file_path, 'rb') as f:
                    file_obj = self.client.files.create(
                        file=f,
                        purpose='assistants'
                    )
                self.file_ids.append(file_obj.id)
                uploaded_files.append(str(file_path))
                
            except Exception as e:
                print(f"❌ Failed to upload {file_path}: {e}")
        
        # Add files to vector store
        if self.file_ids and self.vector_store_id:
            self.client.beta.vector_stores.file_batches.create(
                vector_store_id=self.vector_store_id,
                file_ids=self.file_ids
            )
            print(f"✅ Added {len(self.file_ids)} files to vector store")
        
        return uploaded_files
    
    async def search_knowledge_base(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Search the vector store for relevant content"""
        if not self.vector_store_id:
            return {
                "error": "No vector store configured",
                "results": []
            }
        
        try:
            # Create a temporary assistant for search
            assistant = self.client.beta.assistants.create(
                name="KB Search Assistant",
                instructions="You are a search assistant. Return relevant content from the knowledge base.",
                model="gpt-4.1",
                tools=[{
                    "type": "file_search",
                    "file_search": {
                        "max_num_results": max_results,
                        "vector_store_ids": [self.vector_store_id]
                    }
                }]
            )
            
            # Create thread and search
            thread = self.client.beta.threads.create()
            
            message = self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=f"Search for: {query}"
            )
            
            run = self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=assistant.id
            )
            
            # Wait for completion
            import time
            while run.status in ['queued', 'in_progress']:
                time.sleep(1)
                run = self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
            
            # Get results
            if run.status == 'completed':
                messages = self.client.beta.threads.messages.list(
                    thread_id=thread.id,
                    order="desc",
                    limit=1
                )
                
                # Clean up
                self.client.beta.assistants.delete(assistant.id)
                
                if messages.data:
                    content = messages.data[0].content[0].text.value
                    return {
                        "query": query,
                        "results": content,
                        "source": "vector_store"
                    }
            
            # Clean up on failure
            self.client.beta.assistants.delete(assistant.id)
            
            return {
                "error": f"Search failed with status: {run.status}",
                "results": []
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "results": []
            }
    
    def _save_vector_store_id(self, store_id: str):
        """Save vector store ID to .env file"""
        env_path = Path(".env")
        
        # Read existing .env
        lines = []
        if env_path.exists():
            with open(env_path, 'r') as f:
                lines = f.readlines()
        
        # Update or add VECTOR_STORE_ID
        found = False
        for i, line in enumerate(lines):
            if line.startswith("VECTOR_STORE_ID="):
                lines[i] = f"VECTOR_STORE_ID={store_id}\n"
                found = True
                break
        
        if not found:
            lines.append(f"VECTOR_STORE_ID={store_id}\n")
        
        # Write back
        with open(env_path, 'w') as f:
            f.writelines(lines)


class KnowledgeBaseSearchTool:
    """Tool for searching knowledge base in Chat Completions API"""
    
    def __init__(self, vector_handler: VectorStoreHandler):
        self.vector_handler = vector_handler
        
    async def search(self, query: str, max_results: int = 6) -> str:
        """Search knowledge base and return formatted results"""
        results = await self.vector_handler.search_knowledge_base(query, max_results)
        
        if results.get("error"):
            return f"Knowledge base search failed: {results['error']}"
        
        return f"""Knowledge Base Search Results for: "{query}"

{results.get('results', 'No relevant content found')}

Source: Dakota Knowledge Base (Vector Store)"""
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Get tool definition for function calling"""
        return {
            "type": "function",
            "function": {
                "name": "search_knowledge_base",
                "description": "Search Dakota's knowledge base for relevant information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results",
                            "default": 6
                        }
                    },
                    "required": ["query"]
                }
            }
        }