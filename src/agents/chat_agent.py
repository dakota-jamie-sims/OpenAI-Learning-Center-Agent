"""
Chat Completions API Agent Implementation
Uses OpenAI's Chat Completions (responses) API instead of Assistants
"""
from openai import OpenAI, AsyncOpenAI
from typing import Optional, List, Dict, Any, Callable
import json
import asyncio
from pathlib import Path
import tiktoken
from tenacity import retry, stop_after_attempt, wait_exponential


class ChatAgent:
    """Base agent using Chat Completions API with function calling"""
    
    def __init__(
        self,
        name: str,
        instructions: str,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_handlers: Optional[Dict[str, Callable]] = None
    ):
        self.name = name
        self.instructions = instructions
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.tools = tools or []
        self.tool_handlers = tool_handlers or {}
        self.conversation_history = []
        
        # Token counting
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def run_async(self, client: AsyncOpenAI, user_prompt: str) -> Dict[str, Any]:
        """Run the agent asynchronously with the Chat Completions API"""
        # Build messages
        messages = [
            {"role": "system", "content": self.instructions},
            {"role": "user", "content": user_prompt}
        ]
        
        # Add conversation history if any
        messages.extend(self.conversation_history)
        
        # Prepare API call parameters
        params = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature
        }
        
        if self.max_tokens:
            params["max_tokens"] = self.max_tokens
            
        if self.tools:
            params["tools"] = self.tools
            params["tool_choice"] = "auto"
        
        try:
            # Make API call
            response = await client.chat.completions.create(**params)
            
            # Handle the response
            message = response.choices[0].message
            
            # Handle function calls if any
            if message.tool_calls:
                tool_results = await self._handle_tool_calls(message.tool_calls)
                
                # Add function results to messages
                messages.append(message)
                messages.append({
                    "role": "tool",
                    "content": json.dumps(tool_results),
                    "tool_call_id": message.tool_calls[0].id
                })
                
                # Get final response after tool execution
                final_response = await client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature
                )
                
                final_message = final_response.choices[0].message
                
                return {
                    "content": final_message.content,
                    "tool_calls": tool_results,
                    "usage": {
                        "prompt_tokens": response.usage.prompt_tokens + final_response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens + final_response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens + final_response.usage.total_tokens
                    }
                }
            
            # Return regular response
            return {
                "content": message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "content": None
            }
    
    async def _handle_tool_calls(self, tool_calls) -> List[Dict[str, Any]]:
        """Handle tool/function calls"""
        results = []
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            if function_name in self.tool_handlers:
                # Execute the tool handler
                result = await self.tool_handlers[function_name](**function_args)
                results.append({
                    "tool_call_id": tool_call.id,
                    "function_name": function_name,
                    "result": result
                })
            else:
                results.append({
                    "tool_call_id": tool_call.id,
                    "function_name": function_name,
                    "error": f"No handler for function: {function_name}"
                })
        
        return results
    
    def add_to_history(self, role: str, content: str):
        """Add a message to conversation history"""
        self.conversation_history.append({"role": role, "content": content})
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []


class ChatAgentManager:
    """Manages multiple chat agents"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = AsyncOpenAI(api_key=api_key)
        self.agents: Dict[str, ChatAgent] = {}
        
    def create_agent_from_prompt(
        self,
        name: str,
        prompt_file: str,
        model: str = "gpt-4-turbo-preview",
        temperature: float = 0.7,
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_handlers: Optional[Dict[str, Callable]] = None
    ) -> ChatAgent:
        """Create an agent from a markdown prompt file"""
        # Load prompt
        prompts_dir = Path(__file__).parent.parent / "prompts"
        prompt_path = prompts_dir / prompt_file
        
        with open(prompt_path, 'r') as f:
            instructions = f.read()
        
        # Create agent
        agent = ChatAgent(
            name=name,
            instructions=instructions,
            model=model,
            temperature=temperature,
            tools=tools,
            tool_handlers=tool_handlers
        )
        
        self.agents[name] = agent
        return agent
    
    async def run_agent(self, agent_name: str, prompt: str) -> Dict[str, Any]:
        """Run an agent by name"""
        if agent_name not in self.agents:
            raise ValueError(f"Agent {agent_name} not found")
        
        agent = self.agents[agent_name]
        return await agent.run_async(self.client, prompt)
    
    async def run_agents_parallel(self, agent_prompts: List[tuple[str, str]]) -> List[Dict[str, Any]]:
        """Run multiple agents in parallel"""
        tasks = []
        for agent_name, prompt in agent_prompts:
            if agent_name in self.agents:
                tasks.append(self.run_agent(agent_name, prompt))
            else:
                tasks.append(asyncio.create_task(self._error_result(f"Agent {agent_name} not found")))
        
        return await asyncio.gather(*tasks)
    
    async def _error_result(self, error: str) -> Dict[str, Any]:
        """Return an error result"""
        return {"error": error, "content": None}


# Tool definitions for function calling
TOOL_DEFINITIONS = {
    "web_search": {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        }
    },
    "write_file": {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write content to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path"
                    },
                    "content": {
                        "type": "string",
                        "description": "The content to write"
                    }
                },
                "required": ["path", "content"]
            }
        }
    },
    "read_file": {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read content from a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path"
                    }
                },
                "required": ["path"]
            }
        }
    },
    "verify_urls": {
        "type": "function",
        "function": {
            "name": "verify_urls",
            "description": "Verify if URLs are accessible",
            "parameters": {
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of URLs to verify"
                    }
                },
                "required": ["urls"]
            }
        }
    },
    "validate_article": {
        "type": "function",
        "function": {
            "name": "validate_article",
            "description": "Validate article structure and requirements",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The article text to validate"
                    }
                },
                "required": ["text"]
            }
        }
    }
}