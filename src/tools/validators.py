import re
from typing import Dict

import yaml
from markdown_it import MarkdownIt

def validate_article_template(text: str) -> Dict[str, any]:
    """Validate article follows Dakota's required template structure."""
    issues = []
    warnings = []
    
    # Check YAML frontmatter
    frontmatter_data = {}
    body = text
    stripped = text.lstrip()
    if not stripped.startswith("---"):
        issues.append("Missing YAML frontmatter '---' at top.")
    else:
        try:
            _, fm, body = stripped.split('---', 2)
            body = body.lstrip("\n")
            try:
                frontmatter_data = yaml.safe_load(fm) or {}
            except yaml.YAMLError:
                issues.append("Malformed YAML frontmatter")
            required_fields = ["title", "date", "word_count", "reading_time"]
            for field in required_fields:
                if field not in frontmatter_data:
                    issues.append(f"Missing required frontmatter field: {field}")
        except ValueError:
            issues.append("Missing closing '---' for YAML frontmatter")
    
    # Check required sections
    required_sections = [
        "Key Insights at a Glance",
        "Key Takeaways",
        "Conclusion",
    ]
    md = MarkdownIt()
    tokens = md.parse(body)
    headings = []
    for i, token in enumerate(tokens):
        if token.type == 'heading_open' and i + 1 < len(tokens):
            inline = tokens[i + 1]
            if inline.type == 'inline':
                headings.append(inline.content.strip().lower())

    for sec in required_sections:
        if sec.lower() not in headings:
            issues.append(f"Missing required section: {sec}")
    
    # Check forbidden sections
    disallowed = ["Introduction", "Executive Summary", "About Dakota", "Disclaimer"]
    for sec in disallowed:
        if sec.lower() in headings:
            issues.append(f"Contains disallowed section: {sec}")
    
    # Check word count
    word_count = len(text.split())
    if word_count < 1750:
        issues.append(f"Article too short: {word_count} words (minimum 1,750 required)")
    
    # Check for inline citations
    citation_pattern = r'\[([^\]]+)\]\(https?://[^\)]+\)'
    citations = re.findall(citation_pattern, text)
    if len(citations) < 10:
        issues.append(f"Insufficient citations: {len(citations)} found (minimum 10 required)")
    
    # Check for vague references
    vague_patterns = [
        r'\bstudies show\b',
        r'\bexperts say\b',
        r'\bresearch suggests\b',
        r'\bsome believe\b',
        r'\bmany think\b'
    ]
    for pattern in vague_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            warnings.append(f"Contains vague reference: '{pattern.strip('\\\\b')}'")
    
    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "word_count": word_count,
        "citation_count": len(citations)
    }

def count_sources(text: str) -> Dict[str, any]:
    """Count and extract all sources from the article."""
    # Extract all URLs
    url_pattern = r'https?://[^\s\)\]\>]+'
    urls = re.findall(url_pattern, text)
    
    # Extract inline citations
    citation_pattern = r'\[([^\]]+)\]\((https?://[^\)]+)\)'
    citations = re.findall(citation_pattern, text)
    
    # Unique sources
    unique_urls = list(set(urls))
    
    return {
        "total_urls": len(urls),
        "unique_urls": len(unique_urls),
        "inline_citations": len(citations),
        "urls": unique_urls
    }
