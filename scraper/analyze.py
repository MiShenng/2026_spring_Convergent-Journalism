"""Turn collected items/comments into the JSON the webpage needs.

Outputs platform distribution, KPI counts, themed word frequencies, language
distribution, optional sentiment, and a few top sample comments. Every number
here is derived from the collected sample only (documented in `meta.caveats`).
"""
from __future__ import annotations

import logging
from collections import Counter
from datetime import date
from typing import Dict, List, Optional

from config import ScraperConfig
from models import Comment, MediaItem
from themes import THEME_KEYWORDS, count_keyword

logger = logging.getLogger(__name__)


def detect_languages(comments: List[Comment]) -> List[Comment]:
    """Attach a best-effort language code to each comment (deterministic)."""
    try:
        from langdetect import DetectorFactory, detect
        DetectorFactory.seed = 0
    except ImportError:
        logger.warning("langdetect not installed; language left blank.")
        return comments
    out: List[Comment] = []
    for c in comments:
        lang = ""
        if len(c.text.strip()) >= 8:
            try:
                lang = detect(c.text)
            except Exception:  # noqa: BLE001 - langdetect raises on junk text
                lang = ""
        out.append(Comment(c.platform, c.comment_id, c.text, c.likes, c.url, lang))
    return out


def _platform_distribution(items: List[MediaItem], comments: List[Comment]) -> List[dict]:
    by_item = Counter(i.platform for i in items)
    by_comment = Counter(c.platform for c in comments)
    max_items = max(by_item.values(), default=1)
    rows = []
    for plat, n in by_item.most_common():
        rows.append({
            "platform": plat,
            "items": n,
            "comments": by_comment.get(plat, 0),
            "pct": round(n / max_items * 100),
        })
    return rows


def _engagement(items: List[MediaItem], top_n: int = 5) -> dict:
    """Aggregate view counts: total reach plus the most-watched videos."""
    total_views = sum(i.views for i in items)
    ranked = sorted(items, key=lambda i: i.views, reverse=True)
    top = [
        {"title": i.title, "views": i.views, "url": i.url, "platform": i.platform}
        for i in ranked[:top_n]
    ]
    return {
        "total_views": total_views,
        "median_views": _median([i.views for i in items]),
        "top_videos": top,
    }


def _median(values: List[int]) -> int:
    if not values:
        return 0
    s = sorted(values)
    mid = len(s) // 2
    return s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) // 2


def _word_frequency(comments: List[Comment]) -> Dict[str, dict]:
    texts = [c.text.lower() for c in comments]
    result: Dict[str, dict] = {}
    for key, (cn, en, keywords) in THEME_KEYWORDS.items():
        counts = [(kw, sum(count_keyword(t, kw) for t in texts)) for kw in keywords]
        counts = [w for w in counts if w[1] > 0]
        counts.sort(key=lambda x: x[1], reverse=True)
        result[key] = {
            "label_cn": cn,
            "label_en": en,
            "words": [{"word": w, "count": n} for w, n in counts],
        }
    return result


def _language_distribution(comments: List[Comment]) -> List[dict]:
    counts = Counter(c.lang for c in comments if c.lang)
    total = sum(counts.values()) or 1
    return [
        {"lang": lang, "count": n, "pct": round(n / total * 100)}
        for lang, n in counts.most_common(10)
    ]


def _sentiment(comments: List[Comment]) -> Optional[dict]:
    try:
        from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    except ImportError:
        logger.warning("vaderSentiment not installed; sentiment skipped.")
        return None
    analyzer = SentimentIntensityAnalyzer()
    pos = neg = neu = 0
    english = [c for c in comments if c.lang in ("en", "")]
    for c in english:
        score = analyzer.polarity_scores(c.text)["compound"]
        if score >= 0.05:
            pos += 1
        elif score <= -0.05:
            neg += 1
        else:
            neu += 1
    total = pos + neg + neu or 1
    return {
        "n": pos + neg + neu,
        "positive_pct": round(pos / total * 100, 1),
        "negative_pct": round(neg / total * 100, 1),
        "neutral_pct": round(neu / total * 100, 1),
    }


_COMMENT_BLOCKLIST = {
    "lay zhang", "zhang yixing", "exo", "kpop", "k-pop",
    "bts", "blackpink", "idol", "yixing", "xiao zhan", "wang yibo",
    "most talented artist", "raises the bar",  # K-pop fan phrases
}

_COMMENT_ALLOWLIST = {
    "dunhuang", "mural", "cave", "mogao", "apsara", "feitian",
    "silk road", "buddhist", "fresco", "ancient", "culture",
    "history", "heritage", "painting", "dance", "art", "india",
    "china", "civilization", "beautiful",
}


def _sample_comments(comments: List[Comment], n: int = 6) -> List[dict]:
    def _is_good(c: Comment) -> bool:
        low = c.text.lower()
        if any(b in low for b in _COMMENT_BLOCKLIST):
            return False
        return any(a in low for a in _COMMENT_ALLOWLIST)

    english = [
        c for c in comments
        if c.lang in ("en", "") and 20 <= len(c.text) <= 280 and _is_good(c)
    ]
    english.sort(key=lambda c: c.likes, reverse=True)
    return [
        {"text": c.text.strip(), "platform": c.platform, "url": c.url,
         "likes": c.likes, "lang": c.lang}
        for c in english[:n]
    ]


def build_dataset(items: List[MediaItem], comments: List[Comment],
                  cfg: ScraperConfig) -> dict:
    """Assemble the final dataset dict (ready to dump as JSON)."""
    comments = detect_languages(comments)
    platforms = sorted({i.platform for i in items})
    languages = _language_distribution(comments)
    return {
        "meta": {
            "collected_at": date.today().isoformat(),
            "keywords": list(cfg.keywords),
            "platforms_collected": platforms,
            "limits": {
                "max_videos_per_keyword": cfg.max_videos_per_keyword,
                "max_posts_per_keyword": cfg.max_posts_per_keyword,
                "max_comments_per_item": cfg.max_comments_per_item,
            },
            "dedup": "by platform item id and by comment id",
            "caveats": [
                "Sample only — not the whole platform; reflects API search ranking.",
                "Theme grouping is an editor-defined keyword heuristic, not a classifier.",
                "Sentiment is a VADER dictionary approximation over English comments.",
                "Commenter geolocation is NOT available from these APIs; we report "
                "comment LANGUAGE distribution instead of country.",
                "Reddit exposes no view counts; platform 'views' is 0 there.",
            ],
        },
        "kpi": {
            "items": len(items),
            "comments": len(comments),
            "languages": len(languages),
        },
        "engagement": _engagement(items),
        "platform_distribution": _platform_distribution(items, comments),
        "language_distribution": languages,
        "sentiment": _sentiment(comments),
        "word_frequency": _word_frequency(comments),
        "sample_comments": _sample_comments(comments),
    }
