from .base_agent import make_agent
from ..config import settings

def create(model: str | None = None):
    return make_agent(
        name="dakota-metrics-analyzer",
        prompt_filename="dakota-metrics-analyzer.md",
        model=model or settings.DEFAULT_MODELS["metrics"],
    )
