"""
Tool definitions and handlers for OpenAI Assistants
"""
import json
import requests
from typing import Dict, Any, List
import re
from pathlib import Path


class AssistantTools:
    """Handles tool execution for OpenAI Assistants"""
    
    @staticmethod
    def web_search(query: str, max_results: int = 10) -> Dict[str, Any]:
        """Simulate web search functionality"""
        # In production, integrate with a real search API
        return {
            "query": query,
            "results": [
                {
                    "title": f"Result for {query}",
                    "url": "https://example.com",
                    "snippet": "This would contain actual search results"
                }
            ]
        }
    
    @staticmethod
    def verify_url(url: str) -> Dict[str, Any]:
        """Verify if a URL is accessible"""
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            return {
                "url": url,
                "status_code": response.status_code,
                "accessible": 200 <= response.status_code < 400
            }
        except Exception as e:
            return {
                "url": url,
                "status_code": 0,
                "accessible": False,
                "error": str(e)
            }
    
    @staticmethod
    def verify_urls(urls: List[str]) -> List[Dict[str, Any]]:
        """Verify multiple URLs"""
        return [AssistantTools.verify_url(url) for url in urls]
    
    @staticmethod
    def validate_article(text: str, min_words: int = 2000, min_sources: int = 12) -> Dict[str, Any]:
        """Validate article structure and requirements"""
        issues = []
        
        # Check word count
        word_count = len(text.split())
        if word_count < min_words:
            issues.append(f"Word count ({word_count}) below minimum ({min_words})")
        
        # Check for required sections
        required_sections = [
            "Key Insights at a Glance",
            "Key Takeaways",
            "Conclusion"
        ]
        
        for section in required_sections:
            if section not in text:
                issues.append(f"Missing required section: {section}")
        
        # Check for forbidden sections
        forbidden_sections = [
            "Introduction",
            "Executive Summary",
            "About Dakota",
            "Disclaimer"
        ]
        
        for section in forbidden_sections:
            if section in text:
                issues.append(f"Contains forbidden section: {section}")
        
        # Check YAML frontmatter
        if not text.strip().startswith("---"):
            issues.append("Missing YAML frontmatter")
        
        # Count sources (look for markdown links)
        sources = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', text)
        if len(sources) < min_sources:
            issues.append(f"Insufficient sources ({len(sources)}) - minimum {min_sources} required")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "word_count": word_count,
            "source_count": len(sources)
        }
    
    @staticmethod
    def write_file(path: str, content: str) -> Dict[str, Any]:
        """Write content to a file"""
        try:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, 'w') as f:
                f.write(content)
            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def read_file(path: str) -> Dict[str, Any]:
        """Read content from a file"""
        try:
            with open(path, 'r') as f:
                content = f.read()
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def list_directory(path: str) -> Dict[str, Any]:
        """List contents of a directory"""
        try:
            p = Path(path)
            if not p.exists():
                return {"success": False, "error": "Path does not exist"}
            
            if p.is_file():
                return {"success": True, "type": "file", "name": p.name}
            
            contents = []
            for item in p.iterdir():
                contents.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            
            return {"success": True, "type": "directory", "contents": contents}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Tool schemas for OpenAI Assistants
TOOL_SCHEMAS = [
    {
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
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
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
    {
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
    },
    {
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
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read content from a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path to read"
                    }
                },
                "required": ["path"]
            }
        }
    }
]


def execute_tool_call(tool_call) -> Dict[str, Any]:
    """Execute a tool call and return results"""
    tool_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    
    tool_map = {
        "web_search": AssistantTools.web_search,
        "verify_urls": AssistantTools.verify_urls,
        "validate_article": AssistantTools.validate_article,
        "write_file": AssistantTools.write_file,
        "read_file": AssistantTools.read_file,
        "list_directory": AssistantTools.list_directory
    }
    
    if tool_name in tool_map:
        return tool_map[tool_name](**arguments)
    else:
        return {"error": f"Unknown tool: {tool_name}"}