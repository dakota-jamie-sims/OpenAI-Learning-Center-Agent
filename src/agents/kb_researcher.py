from agents import FileSearchTool
from .base_agent import make_agent
from ..config import settings

def create(model: str | None = None):
    tools = []
    if settings.VECTOR_STORE_ID:
        tools = [FileSearchTool(max_num_results=6, vector_store_ids=[settings.VECTOR_STORE_ID])]
    return make_agent(
        name="dakota-kb-researcher",
        prompt_filename="dakota-kb-researcher.md",
        model=model or settings.DEFAULT_MODELS["kb_researcher"],
        tools=tools,
    )
