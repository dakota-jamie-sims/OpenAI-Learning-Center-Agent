from .base_agent import make_agent
from ..config import settings

def create(model: str | None = None):
    return make_agent(
        name="dakota-iteration-manager",
        prompt_filename="dakota-iteration-manager.md",
        model=model or settings.DEFAULT_MODELS["iteration"],
    )
