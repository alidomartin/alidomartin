"""
Instagram fetcher using the Instagram Graph API.
Requires a long-lived access token and the user's Instagram Business/Creator account ID.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class Post:
    id: str
    text: str
    created_at: datetime
    url: str
    media_url: Optional[str] = None
    media_type: str = "IMAGE"
    likes: int = 0
    platform: str = "instagram"
    platform_label: str = "Instagram"
    platform_color: str = "#E1306C"
    platform_icon: str = "📸"


class InstagramFetcher:
    """Fetches media from Instagram via the Graph API."""

    BASE_URL = "https://graph.instagram.com/v19.0"

    def __init__(self, access_token: str, user_id: str):
        self.access_token = access_token
        self.user_id = user_id

    def fetch(self, since: datetime) -> list[Post]:
        params = {
            "fields": "id,caption,media_type,media_url,thumbnail_url,permalink,timestamp,like_count",
            "access_token": self.access_token,
            "limit": 50,
        }

        resp = requests.get(f"{self.BASE_URL}/{self.user_id}/media", params=params)

        if resp.status_code != 200:
            logger.error("Failed to fetch Instagram media: %s", resp.text)
            return []

        posts = []
        for item in resp.json().get("data", []):
            created_at = datetime.fromisoformat(
                item["timestamp"].replace("Z", "+00:00")
            )
            if created_at < since.astimezone(timezone.utc):
                continue

            media_url = item.get("media_url") or item.get("thumbnail_url")
            posts.append(
                Post(
                    id=item["id"],
                    text=item.get("caption", ""),
                    created_at=created_at,
                    url=item.get("permalink", ""),
                    media_url=media_url,
                    media_type=item.get("media_type", "IMAGE"),
                    likes=item.get("like_count", 0),
                )
            )

        return sorted(posts, key=lambda p: p.created_at, reverse=True)
