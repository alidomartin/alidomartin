"""
LinkedIn fetcher using the LinkedIn Marketing API.
Uses a member access token to fetch the user's recent posts/shares.
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
    likes: int = 0
    comments: int = 0
    platform: str = "linkedin"
    platform_label: str = "LinkedIn"
    platform_color: str = "#0A66C2"
    platform_icon: str = "💼"


class LinkedInFetcher:
    """Fetches posts from LinkedIn using the v2 API."""

    BASE_URL = "https://api.linkedin.com/v2"

    def __init__(self, access_token: str, person_id: str):
        self.access_token = access_token
        self.person_id = person_id
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "X-Restli-Protocol-Version": "2.0.0",
                "LinkedIn-Version": "202401",
            }
        )

    def fetch(self, since: datetime) -> list[Post]:
        since_ms = int(since.astimezone(timezone.utc).timestamp() * 1000)

        params = {
            "author": f"urn:li:person:{self.person_id}",
            "q": "author",
            "count": 50,
            "sortBy": "LAST_MODIFIED",
        }

        resp = self.session.get(f"{self.BASE_URL}/ugcPosts", params=params)

        if resp.status_code != 200:
            logger.error("Failed to fetch LinkedIn posts: %s", resp.text)
            return []

        posts = []
        for item in resp.json().get("elements", []):
            created_ms = item.get("created", {}).get("time", 0)
            if created_ms < since_ms:
                continue

            created_at = datetime.fromtimestamp(
                created_ms / 1000, tz=timezone.utc
            )

            text = (
                item.get("specificContent", {})
                .get("com.linkedin.ugc.ShareContent", {})
                .get("shareCommentary", {})
                .get("text", "")
            )

            post_id = item.get("id", "")
            url = f"https://www.linkedin.com/feed/update/{post_id}"

            # Extract media thumbnail if present
            media_url = None
            media_list = (
                item.get("specificContent", {})
                .get("com.linkedin.ugc.ShareContent", {})
                .get("media", [])
            )
            if media_list:
                media_url = (
                    media_list[0]
                    .get("thumbnails", [{}])[0]
                    .get("url")
                )

            posts.append(
                Post(
                    id=post_id,
                    text=text,
                    created_at=created_at,
                    url=url,
                    media_url=media_url,
                )
            )

        return sorted(posts, key=lambda p: p.created_at, reverse=True)
