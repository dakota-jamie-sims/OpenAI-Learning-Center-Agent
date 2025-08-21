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

from src.utils.logging import get_logger


logger = get_logger(__name__)


class VectorStoreHandler:
    """Handles vector store operations for knowledge base search"""

    def __init__(self, client: OpenAI):
        self.client = client
        self.vector_store_id = None
        self.file_ids = []
        
    def create_or_get_vector_store(self, name: str = "Dakota Knowledge Base") -> str:
        """Create or retrieve existing vector store"""
        # Check if we already have a vector store ID in env
        existing_id = os.getenv("OPENAI_VECTOR_STORE_ID") or os.getenv("VECTOR_STORE_ID")
        if existing_id:
            try:
                # Verify it still exists
                store = self.client.vector_stores.retrieve(existing_id)
                self.vector_store_id = existing_id
                logger.info("✅ Using existing vector store: %s", existing_id)
                return existing_id
            except:
                logger.warning("⚠️ Existing vector store %s not found, creating new one", existing_id)
        
        # Create new vector store
        vector_store = self.client.vector_stores.create(name=name)
        self.vector_store_id = vector_store.id
        
        # Save to .env for future use
        self._save_vector_store_id(vector_store.id)
        
        logger.info("✅ Created new vector store: %s", vector_store.id)
        return vector_store.id
    
    def upload_knowledge_base(self, kb_directory: str, max_files: int = 100) -> List[str]:
        """Upload knowledge base files to vector store"""
        kb_path = Path(kb_directory)
        if not kb_path.exists():
            raise ValueError(f"Knowledge base directory not found: {kb_directory}")
        
        # Get all markdown files
        files = list(kb_path.rglob("*.md")) + list(kb_path.rglob("*.txt"))
        files = files[:max_files]  # Limit number of files
        
        logger.info("📚 Uploading %d knowledge base files...", len(files))
        
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
                logger.error("❌ Failed to upload %s: %s", file_path, e)
        
        # Add files to vector store
        if self.file_ids and self.vector_store_id:
            self.client.vector_stores.file_batches.create(
                vector_store_id=self.vector_store_id,
                file_ids=self.file_ids
            )
            logger.info("✅ Added %d files to vector store", len(self.file_ids))
        
        return uploaded_files
    
    async def search_knowledge_base(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """Search the vector store for relevant content using Responses API"""
        if not self.vector_store_id:
            return {
                "error": "No vector store configured",
                "results": []
            }
        
        try:
            # Use the Responses API with file search tool
            response = self.client.responses.create(
                model="gpt-4.1",
                input=f"Search for information about: {query}",
                tools=[{
                    "type": "file_search",
                    "vector_store_ids": [self.vector_store_id],
                    "max_num_results": max_results
                }],
                include=["file_search_call.results"]
            )
            
            # Extract search results and file citations from response
            search_results = []
            file_citations = []
            response_text = ""
            
            # Process the output array
            if hasattr(response, 'output'):
                for output_item in response.output:
                    if output_item.type == "file_search_call":
                        # This contains the search metadata
                        if hasattr(output_item, 'search_results') and output_item.search_results:
                            for result in output_item.search_results:
                                search_results.append({
                                    "content": result.content if hasattr(result, 'content') else "",
                                    "file_id": result.file_id if hasattr(result, 'file_id') else "",
                                    "score": result.score if hasattr(result, 'score') else 0
                                })
                    elif output_item.type == "message":
                        # Extract the actual response text and citations
                        if hasattr(output_item, 'content'):
                            for content_item in output_item.content:
                                if content_item.type == "output_text":
                                    response_text = content_item.text
                                    # Extract file citations from annotations
                                    if hasattr(content_item, 'annotations'):
                                        for annotation in content_item.annotations:
                                            if annotation.type == "file_citation":
                                                file_citations.append({
                                                    "file_id": annotation.file_id,
                                                    "filename": annotation.filename if hasattr(annotation, 'filename') else "unknown"
                                                })
            
            # Format results
            if response_text:
                # Add search results info if available
                result_info = ""
                if search_results:
                    result_info = f"\n\n**Found {len(search_results)} relevant documents**"
                
                return {
                    "query": query,
                    "results": f"{response_text}{result_info}",
                    "source": "dakota_knowledge_base",
                    "citations": file_citations,
                    "search_results": search_results
                }
            else:
                # Fallback to hardcoded Dakota articles if no results
                return self._get_fallback_results(query, max_results)
                
        except Exception as e:
            logger.error("Error searching knowledge base: %s", e)
            # Fallback to hardcoded results on error
            return self._get_fallback_results(query, max_results)
    
    def _get_fallback_results(self, query: str, max_results: int) -> Dict[str, Any]:
        """Fallback to hardcoded Dakota articles"""
        dakota_articles = {
            "family offices": [
                {
                    "title": "Top 10 Family Offices in Texas",
                    "url": "https://dakota.com/learning-center/top-10-family-offices-in-texas",
                    "relevance": "Direct match for Texas family offices"
                },
                {
                    "title": "Top 10 Family Offices in California", 
                    "url": "https://dakota.com/learning-center/top-10-family-offices-in-california",
                    "relevance": "California family office landscape"
                },
                {
                    "title": "The Growth of Family Offices",
                    "url": "https://dakota.com/learning-center/the-growth-of-family-offices",
                    "relevance": "Family office trends and insights"
                }
            ],
            "private equity": [
                {
                    "title": "Top Private Equity Fund Databases for 2025",
                    "url": "https://dakota.com/learning-center/top-private-equity-fund-databases-for-2025",
                    "relevance": "PE fund research resources"
                },
                {
                    "title": "Top Private Equity Firms in Dallas | 2025 Rankings",
                    "url": "https://dakota.com/learning-center/top-private-equity-firms-in-dallas-2025-rankings",
                    "relevance": "Regional PE firm analysis"
                }
            ],
            "ria": [
                {
                    "title": "Top 10 RIA Firms in Dallas Metro Area",
                    "url": "https://dakota.com/learning-center/top-10-ria-firms-in-the-dallas-metro-area",
                    "relevance": "Dallas RIA landscape"
                },
                {
                    "title": "How to Leverage RIAs with Dakota Marketplace",
                    "url": "https://dakota.com/learning-center/how-to-leverage-rias-with-dakota-marketplace",
                    "relevance": "RIA engagement strategies"
                }
            ]
        }
        
        # Find relevant articles based on query
        query_lower = query.lower()
        results = []
        
        for category, articles in dakota_articles.items():
            if category in query_lower or any(keyword in query_lower for keyword in category.split()):
                results.extend(articles[:max_results])
        
        # Format results as KB search output
        if results:
            formatted_results = "\n\n".join([
                f"### {r['title']}\n- URL: {r['url']}\n- Relevance: {r['relevance']}"
                for r in results[:max_results]
            ])
            
            return {
                "query": query,
                "results": f"Found {len(results)} relevant Dakota Learning Center articles:\n\n{formatted_results}",
                "source": "dakota_knowledge_base_fallback"
            }
        
        return {
            "query": query,
            "results": "No specific articles found for this query in the knowledge base.",
            "source": "dakota_knowledge_base_fallback"
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