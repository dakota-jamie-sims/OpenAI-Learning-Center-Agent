"""
OpenAI Assistant API Base Class
Provides proper assistant creation and management
"""
from openai import OpenAI
from typing import Optional, List, Dict, Any
import os
from pathlib import Path
import json
import time

class BaseAssistant:
    """Base class for OpenAI Assistants with proper API usage"""
    
    def __init__(self, client: OpenAI):
        self.client = client
        self.assistant = None
        self.thread = None
        
    def create_assistant(
        self,
        name: str,
        instructions: str,
        model: str = "gpt-4-turbo-preview",
        tools: Optional[List[Dict[str, Any]]] = None,
        file_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, str]] = None
    ):
        """Create an OpenAI Assistant"""
        self.assistant = self.client.beta.assistants.create(
            name=name,
            instructions=instructions,
            model=model,
            tools=tools or [],
            file_ids=file_ids or [],
            metadata=metadata or {}
        )
        return self.assistant
    
    def create_thread(self, messages: Optional[List[Dict[str, str]]] = None):
        """Create a new thread for conversation"""
        if messages:
            self.thread = self.client.beta.threads.create(messages=messages)
        else:
            self.thread = self.client.beta.threads.create()
        return self.thread
    
    def add_message(self, content: str, role: str = "user", file_ids: Optional[List[str]] = None):
        """Add a message to the thread"""
        if not self.thread:
            raise ValueError("No thread created. Call create_thread() first.")
        
        message = self.client.beta.threads.messages.create(
            thread_id=self.thread.id,
            role=role,
            content=content,
            file_ids=file_ids or []
        )
        return message
    
    def run(self, additional_instructions: Optional[str] = None) -> Any:
        """Run the assistant on the current thread"""
        if not self.assistant or not self.thread:
            raise ValueError("Assistant and thread must be created first.")
        
        # Create a run
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread.id,
            assistant_id=self.assistant.id,
            instructions=additional_instructions
        )
        
        # Poll for completion
        while run.status in ['queued', 'in_progress', 'cancelling']:
            time.sleep(1)
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread.id,
                run_id=run.id
            )
            
            # Handle any required actions
            if run.status == 'requires_action':
                # Handle tool calls if needed
                self._handle_required_action(run)
        
        if run.status == 'completed':
            # Get the messages
            messages = self.client.beta.threads.messages.list(
                thread_id=self.thread.id,
                order="desc",
                limit=1
            )
            return messages.data[0] if messages.data else None
        else:
            raise Exception(f"Run failed with status: {run.status}")
    
    def _handle_required_action(self, run):
        """Handle tool calls during run"""
        if run.required_action.type == 'submit_tool_outputs':
            tool_outputs = []
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                # Execute the actual tool
                output = self._execute_tool(tool_call)
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": json.dumps(output)
                })
            
            # Submit tool outputs
            self.client.beta.threads.runs.submit_tool_outputs(
                thread_id=self.thread.id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
    
    def _execute_tool(self, tool_call):
        """Execute a tool call - override in subclasses"""
        return {"status": "success", "result": "Tool executed"}
    
    def cleanup(self):
        """Clean up resources"""
        if self.assistant:
            try:
                self.client.beta.assistants.delete(self.assistant.id)
            except:
                pass


class AssistantManager:
    """Manages multiple assistants and their lifecycle"""
    
    def __init__(self, client: OpenAI):
        self.client = client
        self.assistants = {}
        self.vector_store_id = None
        
    def create_vector_store(self, name: str, file_paths: List[str]) -> str:
        """Create a vector store for file search"""
        # Upload files
        file_ids = []
        for path in file_paths:
            with open(path, 'rb') as f:
                file = self.client.files.create(file=f, purpose='assistants')
                file_ids.append(file.id)
        
        # Create vector store
        vector_store = self.client.beta.vector_stores.create(
            name=name,
            file_ids=file_ids
        )
        self.vector_store_id = vector_store.id
        return vector_store.id
    
    def create_assistant_from_prompt(
        self,
        name: str,
        prompt_file: str,
        model: str = "gpt-4-turbo-preview",
        tools: Optional[List[Dict[str, Any]]] = None,
        use_vector_store: bool = False
    ) -> BaseAssistant:
        """Create an assistant from a markdown prompt file"""
        # Load prompt
        prompts_dir = Path(__file__).parent.parent / "prompts"
        prompt_path = prompts_dir / prompt_file
        
        with open(prompt_path, 'r') as f:
            instructions = f.read()
        
        # Create assistant
        assistant = BaseAssistant(self.client)
        
        # Add vector store to tools if requested
        if use_vector_store and self.vector_store_id:
            if not tools:
                tools = []
            tools.append({
                "type": "file_search",
                "file_search": {
                    "vector_store_ids": [self.vector_store_id]
                }
            })
        
        assistant.create_assistant(
            name=name,
            instructions=instructions,
            model=model,
            tools=tools
        )
        
        self.assistants[name] = assistant
        return assistant
    
    def get_assistant(self, name: str) -> Optional[BaseAssistant]:
        """Get an assistant by name"""
        return self.assistants.get(name)
    
    def cleanup_all(self):
        """Clean up all assistants"""
        for assistant in self.assistants.values():
            assistant.cleanup()