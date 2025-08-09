from agents import function_tool
from typing import List
from ..utils.files import write_text, read_text, list_dir
from .validators import validate_article_template, count_sources
from .link_checker import check_urls, get_url_verification_summary

@function_tool
def write_file(path: str, content: str) -> str:
    """Write text content to a file path (overwrites if exists)."""
    write_text(path, content)
    return f"Wrote {len(content)} chars to {path}"

@function_tool
def read_file(path: str) -> str:
    """Read text content from a file path and return it."""
    return read_text(path)

@function_tool
def list_directory(path: str) -> str:
    """List a directory and return entries as a newline-separated string."""
    return "\n".join(list_dir(path))

@function_tool
def validate_article(text: str) -> str:
    """Validate article structure & frontmatter. Returns a JSON report."""
    import json
    report = validate_article_template(text)
    return json.dumps(report)

@function_tool
async def verify_urls(urls: List[str]) -> str:
    """Check a list of URLs; returns detailed verification results with status codes."""
    import json
    results = await check_urls(urls)
    summary = get_url_verification_summary(results)
    return json.dumps({
        "summary": summary,
        "details": results
    })

@function_tool
def analyze_sources(text: str) -> str:
    """Count and analyze all sources in the article."""
    import json
    analysis = count_sources(text)
    return json.dumps(analysis)
