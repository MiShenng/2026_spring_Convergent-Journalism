"""Configuration for the overseas-platform scraper.

Secrets are read from environment variables (see .env.example); they are never
hard-coded here. Search/limit knobs have sensible defaults you can override.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# Default search terms. Keep these aligned with the domestic keywords so the
# overseas sample is comparable. Edit to taste before running.
DEFAULT_KEYWORDS: tuple[str, ...] = (
    "Dunhuang",
    "flying apsara",
    "feitian",
    "Dunhuang mural",
    "Mogao caves",
)


@dataclass(frozen=True)
class ScraperConfig:
    """Immutable run configuration."""

    keywords: tuple[str, ...] = DEFAULT_KEYWORDS
    max_videos_per_keyword: int = 50      # YouTube videos fetched per keyword
    max_comments_per_item: int = 100      # comments pulled per video/post
    max_posts_per_keyword: int = 50       # Reddit posts fetched per keyword
    # secrets (filled from env in load_config)
    youtube_api_key: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "dunhuang-overseas-research"
    output_path: Path = field(
        default_factory=lambda: Path(__file__).parent / "output" / "overseas_data.json"
    )


def load_config() -> ScraperConfig:
    """Build a ScraperConfig, pulling secrets from environment variables."""
    return ScraperConfig(
        youtube_api_key=os.environ.get("YOUTUBE_API_KEY", "").strip(),
        reddit_client_id=os.environ.get("REDDIT_CLIENT_ID", "").strip(),
        reddit_client_secret=os.environ.get("REDDIT_CLIENT_SECRET", "").strip(),
        reddit_user_agent=os.environ.get(
            "REDDIT_USER_AGENT", "dunhuang-overseas-research"
        ).strip(),
    )
