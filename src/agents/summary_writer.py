from .base_agent import make_agent
from ..config import settings

def create(model: str | None = None):
    return make_agent(
        name="dakota-summary-writer",
        prompt_filename="dakota-summary-writer.md",
        model=model or settings.DEFAULT_MODELS["summary"],
    )
