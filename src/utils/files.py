import os, re, unicodedata, datetime

def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[-\s]+", "-", value)

def run_dir_for_topic(base_dir: str, topic: str) -> tuple[str, str]:
    slug = slugify(topic)
    # Shorten slug to max 50 chars
    if len(slug) > 50:
        slug = slug[:50].rstrip('-')
    date = datetime.date.today().isoformat()
    # Create path: output/Learning Center Articles/YYYY-MM-DD-slug/
    learning_center_dir = os.path.join(base_dir, "Learning Center Articles")
    path = os.path.join(learning_center_dir, f"{date}-{slug}")
    os.makedirs(path, exist_ok=True)
    return path, slug

def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_text(path: str, content: str) -> None:
    # Only create directories if path contains directory components
    dir_path = os.path.dirname(path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def list_dir(path: str) -> list[str]:
    if not os.path.isdir(path):
        return []
    return sorted(os.listdir(path))
