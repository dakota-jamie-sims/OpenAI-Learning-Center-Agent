from .base_agent import make_agent
from ..config import DEFAULT_MODELS

def create(model: str | None = None):
    return make_agent(
        name="dakota-social-promoter",
        prompt_filename="dakota-social-promoter.md",
        model=model or DEFAULT_MODELS["social"],
    )
