"""
Configuration for the Weekly Social Magazine generator.
All credentials are loaded from environment variables.
"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    # X (Twitter) API v2
    x_bearer_token: Optional[str] = field(
        default_factory=lambda: os.getenv("X_BEARER_TOKEN")
    )
    x_username: Optional[str] = field(
        default_factory=lambda: os.getenv("X_USERNAME", "alidomartin")
    )

    # Instagram Graph API
    instagram_access_token: Optional[str] = field(
        default_factory=lambda: os.getenv("INSTAGRAM_ACCESS_TOKEN")
    )
    instagram_user_id: Optional[str] = field(
        default_factory=lambda: os.getenv("INSTAGRAM_USER_ID")
    )

    # LinkedIn
    linkedin_access_token: Optional[str] = field(
        default_factory=lambda: os.getenv("LINKEDIN_ACCESS_TOKEN")
    )
    linkedin_person_id: Optional[str] = field(
        default_factory=lambda: os.getenv("LINKEDIN_PERSON_ID")
    )

    # WordPress REST API
    wordpress_site_url: Optional[str] = field(
        default_factory=lambda: os.getenv("WORDPRESS_SITE_URL")
    )
    wordpress_username: Optional[str] = field(
        default_factory=lambda: os.getenv("WORDPRESS_USERNAME")
    )
    wordpress_app_password: Optional[str] = field(
        default_factory=lambda: os.getenv("WORDPRESS_APP_PASSWORD")
    )

    # Substack (RSS-based, no API key needed)
    substack_publication_url: Optional[str] = field(
        default_factory=lambda: os.getenv("SUBSTACK_PUBLICATION_URL")
    )

    # Magazine settings
    magazine_title: str = field(
        default_factory=lambda: os.getenv("MAGAZINE_TITLE", "Alido Martin — Weekly Digest")
    )
    magazine_author: str = field(
        default_factory=lambda: os.getenv("MAGAZINE_AUTHOR", "Alido Martin")
    )
    output_dir: str = field(
        default_factory=lambda: os.getenv("MAGAZINE_OUTPUT_DIR", "magazine/output")
    )

    # How many days back to look for posts (default: 7 days)
    lookback_days: int = field(
        default_factory=lambda: int(os.getenv("LOOKBACK_DAYS", "7"))
    )
