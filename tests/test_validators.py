import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.validators import validate_article_template, count_sources


def make_valid_article() -> str:
    frontmatter = """---
title: Valid Article
date: 2025-01-01
word_count: 1800
reading_time: 7 minutes
---
"""
    body_words = " ".join(["word" for _ in range(1750)])
    sections = (
        "\n## Key Insights at a Glance\n- insight\n"
        "\n## Key Takeaways\n- takeaway\n"
        "\n## Conclusion\nClosing.\n"
    )
    citations = "\n".join(
        [f"[Source{i}](https://example.com/{i})" for i in range(10)]
    )
    return frontmatter + body_words + sections + citations


def test_validate_article_template_success():
    text = make_valid_article()
    result = validate_article_template(text)
    assert result["ok"], result["issues"]
    assert result["citation_count"] >= 10
    assert result["word_count"] >= 1750


def test_validate_article_template_failure():
    text = "# Introduction\nThis is short.\n\n[OnlyOne](https://example.com)\n"
    result = validate_article_template(text)
    assert not result["ok"]
    assert any("Missing YAML frontmatter" in i for i in result["issues"])
    assert any("Missing required section: Key Insights at a Glance" in i for i in result["issues"])
    assert any("Contains disallowed section: Introduction" in i for i in result["issues"])
    assert any("Insufficient citations" in i for i in result["issues"])


def test_count_sources():
    text = (
        "Refer to [One](https://a.com) and [Two](https://b.org). "
        "Visit https://c.net for more."
    )
    stats = count_sources(text)
    assert stats["total_urls"] == 3
    assert stats["inline_citations"] == 2
    assert stats["unique_urls"] == 3
