"""Theme keyword buckets and a small English stopword list.

The theme grouping is an *editor-defined heuristic*: each comment word is bucketed
by whether it matches one of these keyword lists. This is approximate and should be
documented as such on the page (it is not a trained classifier).
"""
from __future__ import annotations

import re

# Page bucket key -> (Chinese label, English label, keyword list).
# Multi-word keywords (e.g. "silk road") are matched as substrings.
THEME_KEYWORDS: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "praise": ("赞叹", "Praise", (
        "beautiful", "stunning", "gorgeous", "amazing", "wow", "masterpiece",
        "elegant", "breathtaking", "lovely", "incredible",
    )),
    "culture": ("文化认知", "Culture", (
        "chinese culture", "culture", "buddhist", "buddhism", "heritage",
        "history", "ancient", "religion", "spiritual", "tradition",
    )),
    "crossref": ("跨文化坐标", "Cross-ref", (
        "silk road", "india", "gandhara", "greek", "persian", "central asia",
        "japan", "korea", "hellenistic",
    )),
    "intent": ("行动", "Intent", (
        "want to visit", "visit", "travel", "where is this", "where can i",
        "bucket list", "go there", "see it",
    )),
    "remix": ("二创", "Remix", (
        "ai", "midjourney", "stable diffusion", "cosplay", "makeup", "remake",
        "fan art", "edit", "filter",
    )),
}

# Minimal English stopword set (avoids an NLTK dependency).
STOPWORDS: frozenset[str] = frozenset("""
a an the and or but if then than so of to in on at by for with about as is are was
were be been being this that these those it its it's i you he she they we me my your
his her their our us them not no yes do does did done have has had can could would
should will just like really very too also more most some any all what which who whom
how when where why from into out up down over under again here there one two get got
""".split())

_WORD_RE = re.compile(r"[a-z][a-z']+")


def tokenize(text: str) -> list[str]:
    """Lowercase, keep alphabetic words >=3 chars, drop stopwords."""
    return [
        w for w in _WORD_RE.findall(text.lower())
        if len(w) >= 3 and w not in STOPWORDS
    ]


def count_keyword(text_lower: str, keyword: str) -> int:
    """Count non-overlapping occurrences of a keyword/phrase in lowercased text."""
    if " " in keyword:
        return text_lower.count(keyword)
    # whole-word match for single tokens
    return len(re.findall(rf"\b{re.escape(keyword)}\b", text_lower))
