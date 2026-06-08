"""Collect Dunhuang-related videos and comments from YouTube (Data API v3).

Uses the official API, so it is rate-limited by your quota (default 10,000
units/day; each search.list costs 100 units). Set YOUTUBE_API_KEY in the env.
"""
from __future__ import annotations

import logging
import re
from typing import List, Tuple

from config import ScraperConfig
from models import Comment, MediaItem

logger = logging.getLogger(__name__)

_PLATFORM = "YouTube"

# Title/channel blocklist — filters K-pop content that shares keywords (e.g. Lay/EXO "飞天")
_BLOCKLIST_TERMS = {
    "lay zhang", "zhang yixing", "exo", "kpop", "k-pop",
    "bts", "blackpink", "idol", "mv", "music video",
    "xiao zhan", "wang yibo", "cdrama",
}

# Stage name "LAY" (EXO member Zhang Yixing). His song is literally titled
# "飞天 / Flying Apsaras", so word-boundary uppercase "LAY" catches those videos
# without hitting normal English words like "display" or "player".
_LAY_RE = re.compile(r"\bLAY\b")


def _is_relevant(title: str, channel: str) -> bool:
    if _LAY_RE.search(title) or _LAY_RE.search(channel):
        return False
    low = (title + " " + channel).lower()
    return not any(t in low for t in _BLOCKLIST_TERMS)


def collect_youtube(cfg: ScraperConfig) -> Tuple[List[MediaItem], List[Comment]]:
    """Return (videos, comments). Empty if no API key or the client is missing."""
    if not cfg.youtube_api_key:
        logger.warning("YOUTUBE_API_KEY not set; skipping YouTube.")
        return [], []
    try:
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
    except ImportError:
        logger.error("google-api-python-client not installed; skipping YouTube.")
        return [], []

    yt = build("youtube", "v3", developerKey=cfg.youtube_api_key, cache_discovery=False)
    video_ids: set[str] = set()

    for kw in cfg.keywords:
        try:
            video_ids |= _search_video_ids(yt, kw, cfg.max_videos_per_keyword)
        except HttpError as e:  # quota / transient API errors
            logger.error("YouTube search failed for '%s': %s", kw, e)

    logger.info("YouTube: %d unique videos found.", len(video_ids))
    items = _fetch_video_stats(yt, sorted(video_ids))

    comments: dict[str, Comment] = {}
    for item in items:
        try:
            for c in _fetch_comments(yt, item.item_id, cfg.max_comments_per_item):
                comments[c.comment_id] = c  # dedup by comment id
        except Exception as e:  # noqa: BLE001 - comments often disabled; keep going
            logger.warning("YouTube comments unavailable for %s: %s", item.item_id, e)

    logger.info("YouTube: %d videos, %d comments collected.", len(items), len(comments))
    return items, list(comments.values())


def _search_video_ids(yt, keyword: str, limit: int) -> set[str]:
    ids: set[str] = set()
    page_token = None
    while len(ids) < limit:
        resp = yt.search().list(
            part="id", q=keyword, type="video", maxResults=min(50, limit - len(ids)),
            relevanceLanguage="en", pageToken=page_token,
        ).execute()
        for it in resp.get("items", []):
            vid = it.get("id", {}).get("videoId")
            if vid:
                ids.add(vid)
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return ids


def _fetch_video_stats(yt, video_ids: List[str]) -> List[MediaItem]:
    items: List[MediaItem] = []
    for i in range(0, len(video_ids), 50):
        chunk = video_ids[i:i + 50]
        resp = yt.videos().list(part="snippet,statistics", id=",".join(chunk)).execute()
        for it in resp.get("items", []):
            stats = it.get("statistics", {})
            snip = it.get("snippet", {})
            title = snip.get("title", "")
            channel = snip.get("channelTitle", "")
            if not _is_relevant(title, channel):
                continue
            items.append(MediaItem(
                platform=_PLATFORM,
                item_id=it["id"],
                title=title,
                url=f"https://www.youtube.com/watch?v={it['id']}",
                views=int(stats.get("viewCount", 0) or 0),
                comment_count=int(stats.get("commentCount", 0) or 0),
            ))
    return items


def _fetch_comments(yt, video_id: str, limit: int) -> List[Comment]:
    out: List[Comment] = []
    page_token = None
    while len(out) < limit:
        resp = yt.commentThreads().list(
            part="snippet", videoId=video_id, maxResults=min(100, limit - len(out)),
            textFormat="plainText", order="relevance", pageToken=page_token,
        ).execute()
        for it in resp.get("items", []):
            top = it["snippet"]["topLevelComment"]
            snip = top["snippet"]
            out.append(Comment(
                platform=_PLATFORM,
                comment_id=top["id"],
                text=snip.get("textDisplay", ""),
                likes=int(snip.get("likeCount", 0) or 0),
                url=f"https://www.youtube.com/watch?v={video_id}",
            ))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return out
