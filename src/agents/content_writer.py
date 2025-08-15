from .base_agent import make_agent
from ..config import settings

def create(model: str | None = None):
    return make_agent(
        name="dakota-content-writer",
        prompt_filename="dakota-content-writer.md",
        model=model or settings.DEFAULT_MODELS["writer"],
    )
