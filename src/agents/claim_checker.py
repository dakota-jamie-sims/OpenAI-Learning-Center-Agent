from agents import WebSearchTool, FileSearchTool
from .base_agent import make_agent
from ..config import DEFAULT_MODELS, VECTOR_STORE_ID

def create(model: str | None = None):
    tools = [WebSearchTool()]
    if VECTOR_STORE_ID:
        tools.append(FileSearchTool(max_num_results=6, vector_store_ids=[VECTOR_STORE_ID]))
    return make_agent(
        name="dakota-claim-checker",
        prompt_filename="dakota-claim-checker.md",
        model=model or DEFAULT_MODELS["claim_checker"],
        tools=tools,
    )
