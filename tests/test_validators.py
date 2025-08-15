import pytest

from src.tools.validators import validate_article_template

VALID_FRONTMATTER = """---
title: Test
date: 2024-01-01
word_count: 2000
reading_time: 8
---
"""

def build_article(body: str) -> str:
    return VALID_FRONTMATTER + body


def test_nested_headings_and_forbidden_section():
    body = (
        "# Start\n"
        "## Overview\n"
        "### Key Insights at a Glance\n"
        "Text\n"
        "#### Key Takeaways\n"
        "More text\n"
        "### Conclusion\n"
        "### Introduction\n"
    )
    text = build_article(body)
    result = validate_article_template(text)
    assert "Contains disallowed section: Introduction" in result["issues"]
    for sec in ["Key Insights at a Glance", "Key Takeaways", "Conclusion"]:
        assert f"Missing required section: {sec}" not in result["issues"]


def test_malformed_yaml():
    text = (
        "---\n"
        "title: Test\n"
        "date: 2024-01-01\n"
        "word_count: 2000\n"
        "reading_time: 8\n"
        "bad: [oops\n"  # malformed YAML
        "---\n"
        "# Key Insights at a Glance\n"
        "## Key Takeaways\n"
        "## Conclusion\n"
    )
    result = validate_article_template(text)
    assert "Malformed YAML frontmatter" in result["issues"]
