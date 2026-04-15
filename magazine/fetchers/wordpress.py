"""
WordPress fetcher using the WordPress REST API.
Works with self-hosted WordPress and WordPress.com sites.
Falls back to RSS feed parsing if no credentials are provided.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urljoin

import feedparser
import requests

logger = logging.getLogger(__name__)


@dataclass
class Post:
    id: str
    text: str
    created_at: datetime
    url: str
    title: str = ""
    excerpt: str = ""
    media_url: Optional[str] = None
    platform: str = "wordpress"
    platform_label: str = "WordPress"
    platform_color: str = "#21759B"
    platform_icon: str = "📝"


class WordPressFetcher:
    """Fetches posts from WordPress via REST API or RSS fallback."""

    def __init__(
        self,
        site_url: str,
        username: Optional[str] = None,
        app_password: Optional[str] = None,
    ):
        self.site_url = site_url.rstrip("/")
        self.username = username
        self.app_password = app_password

    def fetch(self, since: datetime) -> list[Post]:
        try:
            return self._fetch_via_api(since)
        except Exception as e:
            logger.warning("WordPress REST API failed (%s), falling back to RSS", e)
            return self._fetch_via_rss(since)

    def _fetch_via_api(self, since: datetime) -> list[Post]:
        api_url = urljoin(self.site_url + "/", "wp-json/wp/v2/posts")
        since_iso = since.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

        params = {
            "after": since_iso,
            "per_page": 20,
            "status": "publish",
            "_fields": "id,title,excerpt,content,link,date,featured_media,jetpack_featured_media_url",
        }

        auth = None
        if self.username and self.app_password:
            auth = (self.username, self.app_password)

        resp = requests.get(api_url, params=params, auth=auth, timeout=15)
        resp.raise_for_status()

        posts = []
        for item in resp.json():
            raw_title = item.get("title", {}).get("rendered", "")
            raw_excerpt = item.get("excerpt", {}).get("rendered", "")
            raw_content = item.get("content", {}).get("rendered", "")

            # Strip basic HTML tags for plain text
            import re
            clean = re.compile(r"<[^>]+>")
            title = clean.sub("", raw_title).strip()
            excerpt = clean.sub("", raw_excerpt).strip()[:300]
            text = excerpt or clean.sub("", raw_content).strip()[:300]

            created_at = datetime.fromisoformat(item["date"] + "+00:00")

            posts.append(
                Post(
                    id=str(item["id"]),
                    text=text,
                    created_at=created_at,
                    url=item.get("link", ""),
                    title=title,
                    excerpt=excerpt,
                    media_url=item.get("jetpack_featured_media_url"),
                )
            )

        return sorted(posts, key=lambda p: p.created_at, reverse=True)

    def _fetch_via_rss(self, since: datetime) -> list[Post]:
        rss_url = urljoin(self.site_url + "/", "feed/")
        feed = feedparser.parse(rss_url)

        posts = []
        import re
        clean = re.compile(r"<[^>]+>")

        for entry in feed.entries:
            import time as time_mod
            created_at = datetime.fromtimestamp(
                time_mod.mktime(entry.published_parsed), tz=timezone.utc
            )
            if created_at < since.astimezone(timezone.utc):
                continue

            summary = clean.sub("", entry.get("summary", "")).strip()[:300]
            posts.append(
                Post(
                    id=entry.get("id", entry.link),
                    text=summary,
                    created_at=created_at,
                    url=entry.link,
                    title=entry.get("title", ""),
                    excerpt=summary,
                )
            )

        return sorted(posts, key=lambda p: p.created_at, reverse=True)
