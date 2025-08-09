from .base_agent import make_agent
from ..config import DEFAULT_MODELS

def create(model: str | None = None):
    return make_agent(
        name="dakota-fact-checker",
        prompt_filename="dakota-fact-checker.md",
        model=model or DEFAULT_MODELS["fact_checker"],
    )
