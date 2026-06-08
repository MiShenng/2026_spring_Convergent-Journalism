"""Collect Dunhuang-related posts and comments from Reddit (PRAW).

Needs a free Reddit "script" app: set REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET /
REDDIT_USER_AGENT in the env. Read-only; no Reddit account login required.
"""
from __future__ import annotations

import logging
from typing import List, Tuple

from config import ScraperConfig
from models import Comment, MediaItem

logger = logging.getLogger(__name__)

_PLATFORM = "Reddit"


def collect_reddit(cfg: ScraperConfig) -> Tuple[List[MediaItem], List[Comment]]:
    """Return (posts, comments). Empty if credentials or PRAW are missing."""
    if not (cfg.reddit_client_id and cfg.reddit_client_secret):
        logger.warning("Reddit credentials not set; skipping Reddit.")
        return [], []
    try:
        import praw
    except ImportError:
        logger.error("praw not installed; skipping Reddit.")
        return [], []

    reddit = praw.Reddit(
        client_id=cfg.reddit_client_id,
        client_secret=cfg.reddit_client_secret,
        user_agent=cfg.reddit_user_agent,
        check_for_async=False,
    )
    reddit.read_only = True

    items: dict[str, MediaItem] = {}
    comments: dict[str, Comment] = {}

    for kw in cfg.keywords:
        try:
            for sub in reddit.subreddit("all").search(
                kw, sort="relevance", limit=cfg.max_posts_per_keyword
            ):
                items[sub.id] = MediaItem(
                    platform=_PLATFORM,
                    item_id=sub.id,
                    title=sub.title or "",
                    url=f"https://www.reddit.com{sub.permalink}",
                    views=0,  # Reddit API does not expose view counts
                    comment_count=int(sub.num_comments or 0),
                )
                _collect_post_comments(sub, cfg.max_comments_per_item, comments)
        except Exception as e:  # noqa: BLE001 - keep going on a bad query/post
            logger.error("Reddit search failed for '%s': %s", kw, e)

    logger.info("Reddit: %d posts, %d comments collected.", len(items), len(comments))
    return list(items.values()), list(comments.values())


def _collect_post_comments(submission, limit: int, out: dict[str, Comment]) -> None:
    submission.comments.replace_more(limit=0)  # skip "load more" stubs
    for c in submission.comments.list()[:limit]:
        body = getattr(c, "body", "")
        if not body or body in ("[deleted]", "[removed]"):
            continue
        out[c.id] = Comment(
            platform=_PLATFORM,
            comment_id=c.id,
            text=body,
            likes=int(getattr(c, "score", 0) or 0),
            url=f"https://www.reddit.com{submission.permalink}",
        )
