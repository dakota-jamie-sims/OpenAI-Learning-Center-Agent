# Utils module
import os
from pathlib import Path
from datetime import datetime
import re


def ensure_output_dir(base_dir: str = None) -> Path:
    """Ensure output directory exists and return Path object"""
    if base_dir is None:
        from learning_center_agent.config import OUTPUT_BASE_DIR
        base_dir = OUTPUT_BASE_DIR
    
    output_path = Path(base_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def format_article_filename(topic: str, max_length: int = 50) -> str:
    """Format topic into a safe filename"""
    # Remove special characters and replace spaces with underscores
    safe_name = re.sub(r'[^\w\s-]', '', topic.lower())
    safe_name = re.sub(r'[-\s]+', '_', safe_name)
    
    # Truncate to max length
    if len(safe_name) > max_length:
        safe_name = safe_name[:max_length].rstrip('_')
    
    return safe_name


def create_article_directory(topic: str, base_dir: str = None) -> Path:
    """Create a timestamped directory for article output"""
    output_base = ensure_output_dir(base_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_topic = format_article_filename(topic)
    
    article_dir = output_base / f"{timestamp}_{safe_topic}"
    article_dir.mkdir(parents=True, exist_ok=True)
    
    return article_dir