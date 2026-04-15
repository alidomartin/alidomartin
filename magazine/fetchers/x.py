"""
X (Twitter) fetcher using the Twitter API v2.
Fetches tweets from the authenticated user's timeline for the past week.
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
    retweets: int = 0
    replies: int = 0
    platform: str = "x"
    platform_label: str = "X (Twitter)"
    platform_color: str = "#000000"
    platform_icon: str = "𝕏"


class XFetcher:
    """Fetches posts from X (Twitter) using API v2."""

    BASE_URL = "https://api.twitter.com/2"

    def __init__(self, bearer_token: str, username: str):
        self.bearer_token = bearer_token
        self.username = username.lstrip("@")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {bearer_token}"})

    def _get_user_id(self) -> Optional[str]:
        resp = self.session.get(f"{self.BASE_URL}/users/by/username/{self.username}")
        if resp.status_code != 200:
            logger.error("Failed to fetch X user ID: %s", resp.text)
            return None
        return resp.json()["data"]["id"]

    def fetch(self, since: datetime) -> list[Post]:
        user_id = self._get_user_id()
        if not user_id:
            return []

        since_iso = since.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        params = {
            "start_time": since_iso,
            "max_results": 100,
            "tweet.fields": "created_at,public_metrics,attachments",
            "expansions": "attachments.media_keys",
            "media.fields": "url,preview_image_url",
            "exclude": "retweets,replies",
        }

        resp = self.session.get(
            f"{self.BASE_URL}/users/{user_id}/tweets", params=params
        )

        if resp.status_code != 200:
            logger.error("Failed to fetch X tweets: %s", resp.text)
            return []

        data = resp.json()
        tweets = data.get("data", [])
        media_map = {
            m["media_key"]: m
            for m in data.get("includes", {}).get("media", [])
        }

        posts = []
        for tweet in tweets:
            metrics = tweet.get("public_metrics", {})
            media_url = None
            for mk in tweet.get("attachments", {}).get("media_keys", []):
                m = media_map.get(mk, {})
                media_url = m.get("url") or m.get("preview_image_url")
                if media_url:
                    break

            posts.append(
                Post(
                    id=tweet["id"],
                    text=tweet["text"],
                    created_at=datetime.fromisoformat(
                        tweet["created_at"].replace("Z", "+00:00")
                    ),
                    url=f"https://x.com/{self.username}/status/{tweet['id']}",
                    media_url=media_url,
                    likes=metrics.get("like_count", 0),
                    retweets=metrics.get("retweet_count", 0),
                    replies=metrics.get("reply_count", 0),
                )
            )

        return sorted(posts, key=lambda p: p.created_at, reverse=True)
