"""
Substack fetcher via RSS feed.
No API key required — Substack exposes a public RSS feed at
<publication>.substack.com/feed
"""
import logging
import re
import time as time_mod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import feedparser

logger = logging.getLogger(__name__)

_TAG_CLEAN = re.compile(r"<[^>]+>")


@dataclass
class Post:
    id: str
    text: str
    created_at: datetime
    url: str
    title: str = ""
    excerpt: str = ""
    media_url: Optional[str] = None
    platform: str = "substack"
    platform_label: str = "Substack"
    platform_color: str = "#FF6719"
    platform_icon: str = "📧"


class SubstackFetcher:
    """Fetches newsletter posts from Substack via RSS."""

    def __init__(self, publication_url: str):
        # Accept either the base URL or the full RSS URL
        if not publication_url.endswith("/feed"):
            publication_url = publication_url.rstrip("/") + "/feed"
        self.rss_url = publication_url

    def fetch(self, since: datetime) -> list[Post]:
        feed = feedparser.parse(self.rss_url)

        if feed.bozo and not feed.entries:
            logger.error(
                "Failed to parse Substack RSS feed from %s: %s",
                self.rss_url,
                feed.bozo_exception,
            )
            return []

        posts = []
        for entry in feed.entries:
            try:
                created_at = datetime.fromtimestamp(
                    time_mod.mktime(entry.published_parsed), tz=timezone.utc
                )
            except (AttributeError, TypeError):
                continue

            if created_at < since.astimezone(timezone.utc):
                continue

            # Grab the first image from the content if available
            media_url = None
            content_html = ""
            if entry.get("content"):
                content_html = entry.content[0].value
                img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content_html)
                if img_match:
                    media_url = img_match.group(1)

            summary = _TAG_CLEAN.sub("", entry.get("summary", content_html)).strip()[:350]

            posts.append(
                Post(
                    id=entry.get("id", entry.link),
                    text=summary,
                    created_at=created_at,
                    url=entry.link,
                    title=entry.get("title", ""),
                    excerpt=summary,
                    media_url=media_url,
                )
            )

        return sorted(posts, key=lambda p: p.created_at, reverse=True)
