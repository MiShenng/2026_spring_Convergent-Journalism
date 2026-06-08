"""Shared immutable data models for the overseas-platform collectors."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MediaItem:
    """A single piece of content (video / post) about Dunhuang on a platform."""

    platform: str
    item_id: str
    title: str
    url: str
    views: int = 0
    comment_count: int = 0


@dataclass(frozen=True)
class Comment:
    """A single public comment under a MediaItem."""

    platform: str
    comment_id: str
    text: str
    likes: int = 0
    url: str = ""
    lang: str = ""
