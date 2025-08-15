from .base_agent import make_agent
from ..config import settings

def create(model: str | None = None):
    return make_agent(
        name="dakota-seo-specialist",
        prompt_filename="dakota-seo-specialist.md",
        model=model or settings.DEFAULT_MODELS["seo"],
    )
