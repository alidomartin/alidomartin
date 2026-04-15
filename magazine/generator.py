"""
Weekly Social Magazine Generator
=================================
Fetches posts from X, Instagram, LinkedIn, WordPress, and Substack
for the past N days (default: 7) and renders a magazine-style HTML file.

Usage:
    python -m magazine.generator
    python -m magazine.generator --lookback-days 14 --output-dir /tmp/magazine

Environment variables:
    See magazine/config.py and .env.example for full list.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from .config import Config
from .fetchers import (
    InstagramFetcher,
    LinkedInFetcher,
    SubstackFetcher,
    WordPressFetcher,
    XFetcher,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@dataclass
class Section:
    platform: str
    label: str
    color: str
    icon: str
    posts: list[Any] = field(default_factory=list)


def build_sections(cfg: Config, since: datetime) -> list[Section]:
    """Run all fetchers and return a list of populated Section objects."""

    sections: list[Section] = []

    # ── X (Twitter) ──────────────────────────────────────────────
    if cfg.x_bearer_token:
        logger.info("Fetching X posts…")
        try:
            posts = XFetcher(cfg.x_bearer_token, cfg.x_username or "").fetch(since)
            logger.info("  → %d X posts", len(posts))
        except Exception as exc:
            logger.warning("X fetch failed: %s", exc)
            posts = []
        sections.append(
            Section("x", "X (Twitter)", "#000000", "𝕏", posts)
        )

    # ── Instagram ─────────────────────────────────────────────────
    if cfg.instagram_access_token and cfg.instagram_user_id:
        logger.info("Fetching Instagram posts…")
        try:
            posts = InstagramFetcher(
                cfg.instagram_access_token, cfg.instagram_user_id
            ).fetch(since)
            logger.info("  → %d Instagram posts", len(posts))
        except Exception as exc:
            logger.warning("Instagram fetch failed: %s", exc)
            posts = []
        sections.append(
            Section("instagram", "Instagram", "#E1306C", "📸", posts)
        )

    # ── LinkedIn ──────────────────────────────────────────────────
    if cfg.linkedin_access_token and cfg.linkedin_person_id:
        logger.info("Fetching LinkedIn posts…")
        try:
            posts = LinkedInFetcher(
                cfg.linkedin_access_token, cfg.linkedin_person_id
            ).fetch(since)
            logger.info("  → %d LinkedIn posts", len(posts))
        except Exception as exc:
            logger.warning("LinkedIn fetch failed: %s", exc)
            posts = []
        sections.append(
            Section("linkedin", "LinkedIn", "#0A66C2", "💼", posts)
        )

    # ── WordPress ─────────────────────────────────────────────────
    if cfg.wordpress_site_url:
        logger.info("Fetching WordPress posts…")
        try:
            posts = WordPressFetcher(
                cfg.wordpress_site_url,
                cfg.wordpress_username,
                cfg.wordpress_app_password,
            ).fetch(since)
            logger.info("  → %d WordPress posts", len(posts))
        except Exception as exc:
            logger.warning("WordPress fetch failed: %s", exc)
            posts = []
        sections.append(
            Section("wordpress", "WordPress", "#21759B", "📝", posts)
        )

    # ── Substack ──────────────────────────────────────────────────
    if cfg.substack_publication_url:
        logger.info("Fetching Substack posts…")
        try:
            posts = SubstackFetcher(cfg.substack_publication_url).fetch(since)
            logger.info("  → %d Substack posts", len(posts))
        except Exception as exc:
            logger.warning("Substack fetch failed: %s", exc)
            posts = []
        sections.append(
            Section("substack", "Substack", "#FF6719", "📧", posts)
        )

    return sections


def render_magazine(cfg: Config, sections: list[Section]) -> str:
    """Render the HTML magazine using the Jinja2 template."""
    templates_dir = Path(__file__).parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html"]),
    )

    template = env.get_template("magazine.html")

    today = datetime.now(tz=timezone.utc)
    total_posts = sum(len(s.posts) for s in sections)
    active_platforms = [s for s in sections if s.posts]

    return template.render(
        title=cfg.magazine_title,
        edition_date=today.strftime("%B %-d, %Y"),
        post_count=total_posts,
        platform_count=len(active_platforms),
        sections=sections,
        generated_at=today.isoformat(),
    )


def save_magazine(html: str, output_dir: str) -> Path:
    """Write the magazine HTML to disk and return the output path."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    today = datetime.now(tz=timezone.utc)
    filename = f"magazine_{today.strftime('%Y-%m-%d')}.html"
    out_path = out / filename

    out_path.write_text(html, encoding="utf-8")

    # Also write a stable "latest" symlink / copy
    latest_path = out / "latest.html"
    latest_path.write_text(html, encoding="utf-8")

    return out_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate the weekly social media magazine."
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=None,
        help="Number of days to look back (overrides LOOKBACK_DAYS env var)",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Output directory (overrides MAGAZINE_OUTPUT_DIR env var)",
    )
    args = parser.parse_args(argv)

    cfg = Config()
    if args.lookback_days is not None:
        cfg.lookback_days = args.lookback_days
    if args.output_dir is not None:
        cfg.output_dir = args.output_dir

    since = datetime.now(tz=timezone.utc) - timedelta(days=cfg.lookback_days)
    logger.info(
        "Generating magazine for posts since %s (%d-day window)…",
        since.strftime("%Y-%m-%d"),
        cfg.lookback_days,
    )

    sections = build_sections(cfg, since)
    total = sum(len(s.posts) for s in sections)

    if total == 0:
        logger.warning("No posts found across any platform. Magazine will show empty state.")

    html = render_magazine(cfg, sections)
    out_path = save_magazine(html, cfg.output_dir)

    logger.info("Magazine written to %s", out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
