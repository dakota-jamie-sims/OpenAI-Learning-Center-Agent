import os
import sys

import pytest

sys.path.insert(0, os.path.abspath("src"))

from validators import validate_article_template, count_sources


def _make_valid_article():
    front = "---\n" \
            "title: Test\n" \
            "date: 2024-01-01\n" \
            "word_count: 1800\n" \
            "reading_time: 8\n" \
            "---\n\n"
    sections = (
        "# Key Insights at a Glance\ntext\n\n"
        "# Key Takeaways\ntext\n\n"
        "# Conclusion\ntext\n\n"
    )
    citations = ' '.join([f"[c{i}](http://example.com/{i})" for i in range(10)])
    filler = ' '.join(['word'] * 1800)
    return front + sections + citations + ' ' + filler


def test_validate_article_template_valid():
    article = _make_valid_article()
    res = validate_article_template(article)
    assert res['ok'] is True
    assert res['issues'] == []
    assert res['word_count'] >= 1750
    assert res['citation_count'] >= 10


def test_validate_article_template_invalid():
    article = "No frontmatter\n# Missing sections"
    res = validate_article_template(article)
    assert res['ok'] is False
    assert any('Missing YAML frontmatter' in issue for issue in res['issues'])
    assert any('Missing required section' in issue for issue in res['issues'])


def test_count_sources():
    text = (
        "Check [A](http://a.com) and [B](http://b.com) plus https://c.com"
    )
    res = count_sources(text)
    assert res['total_urls'] == 3
    assert res['unique_urls'] == 3
    assert res['inline_citations'] == 2
    assert 'http://a.com' in res['urls']
