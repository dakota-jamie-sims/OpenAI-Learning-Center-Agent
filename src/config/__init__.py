from dotenv import load_dotenv
from .models import Settings

load_dotenv()
settings = Settings()

__all__ = ["settings", "Settings"]
