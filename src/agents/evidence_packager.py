from agents import WebSearchTool, FileSearchTool
from .base_agent import make_agent
from ..config import settings

def create(model: str | None = None):
    tools = [WebSearchTool()]
    if settings.VECTOR_STORE_ID:
        tools.append(FileSearchTool(max_num_results=6, vector_store_ids=[settings.VECTOR_STORE_ID]))
    return make_agent(
        name="dakota-evidence-packager",
        prompt_filename="dakota-evidence-packager.md",
        model=model or settings.DEFAULT_MODELS["evidence"],
        tools=tools,
    )
