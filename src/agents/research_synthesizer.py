from .base_agent import make_agent
from ..config import settings

def create(model: str | None = None):
    return make_agent(
        name="dakota-research-synthesizer",
        prompt_filename="dakota-research-synthesizer.md",
        model=model or settings.DEFAULT_MODELS["synthesizer"],
    )
