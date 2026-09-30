"""Extract the article HTML from a rendered Wikidot page.

Verified against dnd2024.wikidot.com / dnd5e.wikidot.com:
- the article lives inside <div id="page-content">
- it is fully rendered server-side (no module-suppressed blobs)
- it ends before #action-area / .page-tags / #footer
- ads, nav and tooltips live outside that region
"""
from __future__ import annotations

import html
import re

START_MARKER = '<div id="page-content">'
END_MARKERS = (
    '<div id="action-area"',
    '<div class="page-tags"',
    '<div class="page-info-break"',
    '<div id="page-options-bottom-tips"',
    '<div id="footer"',
)

# Constructs that are navigation/chrome, not rules content.
JUNK_PATTERNS = [
    r'<div[^>]*id="toc"[^>]*>.*?</div>\s*</div>\s*</div>',  # table of contents
    r'<div[^>]*id="toc-action-bar".*?</div>',
    r'<div[^>]*class="content-separator"[^>]*>\s*</div>',
    r'<div[^>]*id="page-info".*?</div>\s*</div>',
    r'<span[^>]*id="wiki-credit".*?</span>',
    r'<div[^>]*class="footnotes-footer".*?</div>',
    r'<div[^>]*class="_footnotes".*?</div>',
    r'<a[^>]*name="[^"]*"[^>]*>\s*</a>',
]


def extract_article(page_html: str) -> str:
    """Return the cleaned article HTML, or '' when the container is missing."""
    start = page_html.find(START_MARKER)
    if start == -1:
        return ""
    start += len(START_MARKER)

    end = len(page_html)
    for marker in END_MARKERS:
        found = page_html.find(marker, start)
        if found != -1:
            end = min(end, found)

    article = page_html[start:end]

    # The closing </div> of page-content belongs to the wrapper, not the article.
    tail = article.rfind("</div>")
    if tail != -1:
        article = article[:tail]

    for pattern in JUNK_PATTERNS:
        article = re.sub(pattern, "", article, flags=re.IGNORECASE | re.DOTALL)

    # Never let scripts, styles or event handlers reach the Markdown.
    article = re.sub(r"<script\b.*?</script>", "", article, flags=re.IGNORECASE | re.DOTALL)
    article = re.sub(r"<style\b.*?</style>", "", article, flags=re.IGNORECASE | re.DOTALL)
    article = re.sub(r"<noscript\b.*?</noscript>", "", article, flags=re.IGNORECASE | re.DOTALL)
    article = re.sub(r"\son\w+\s*=\s*\"[^\"]*\"", "", article, flags=re.IGNORECASE)

    return article.strip()


def extract_title(page_html: str) -> str:
    match = re.search(r"<title>(.*?)</title>", page_html, re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    title = html.unescape(re.sub(r"<[^>]+>", "", match.group(1)))
    # "Fireball - D&D 5e (2024)" -> "Fireball"
    title = re.split(r"\s+[-–]\s+", title)[0]
    return title.strip()


def extract_tags(page_html: str) -> list[str]:
    block = re.search(r'<div class="page-tags">(.*?)</div>', page_html, re.DOTALL)
    if not block:
        return []
    tags = re.findall(r"/system:page-tags/tag/([^#\"]+)", block.group(1))
    return [html.unescape(tag).strip() for tag in tags if tag.strip()]


def extract_parent_page(page_html: str) -> str:
    """Wikidot breadcrumbs expose the parent page path."""
    crumb = re.search(r'<div[^>]*id="page-path".*?</div>', page_html, re.DOTALL)
    if not crumb:
        return ""
    links = re.findall(r'href="[^"]*?/([a-z0-9\-]+:[a-z0-9\-_%]+)"', crumb.group(0))
    return links[-1] if links else ""