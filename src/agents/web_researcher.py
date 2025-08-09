from agents import WebSearchTool
from .base_agent import make_agent
from ..config import DEFAULT_MODELS

def create(model: str | None = None):
    return make_agent(
        name="dakota-web-researcher",
        prompt_filename="dakota-web-researcher.md",
        model=model or DEFAULT_MODELS["web_researcher"],
        tools=[WebSearchTool()],
    )
