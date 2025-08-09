from agents import Agent
from typing import Optional
from .. import config
import os
from pathlib import Path

def make_agent(
    name: str,
    prompt_filename: str,
    model: str,
    tools: Optional[list] = None,
) -> Agent:
    # Load the prompt
    prompts_dir = Path(__file__).parent.parent / "prompts"
    prompt_path = prompts_dir / prompt_filename
    
    with open(prompt_path, 'r') as f:
        prompt_content = f.read()
    
    # Create agent with specified model
    return Agent(
        name=name,
        instructions=prompt_content,
        model=model,
        tools=tools or []
    )
