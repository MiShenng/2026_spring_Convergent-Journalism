"""Collect Wikipedia pageview counts for Dunhuang-related articles.

Uses the free Wikimedia REST API (no key, no auth). Measures how often people
actively *search out* Dunhuang on Wikipedia, across language editions — an
independent "demand" signal next to the platform "supply"/reaction data.

API: https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/...
A descriptive User-Agent is required by Wikimedia policy.
"""
from __future__ import annotations

import json
import logging
import urllib.request
from datetime import date, timedelta
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

_API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
_UA = "dunhuang-overseas-research/1.0 (educational; contact via github)"

# (project, article title) pairs. Titles must match the article URL exactly.
_ARTICLES: Tuple[Tuple[str, str, str], ...] = (
    ("en.wikipedia", "Dunhuang", "English · Dunhuang"),
    ("en.wikipedia", "Mogao_Caves", "English · Mogao Caves"),
    ("en.wikipedia", "Apsara", "English · Apsara"),
    ("ja.wikipedia", "敦煌市", "Japanese · 敦煌"),
    ("fr.wikipedia", "Dunhuang", "French · Dunhuang"),
    ("es.wikipedia", "Dunhuang", "Spanish · Dunhuang"),
)


def _fetch_article(project: str, article: str, start: str, end: str) -> int:
    url = (
        f"{_API}/{project}/all-access/user/"
        f"{urllib.parse.quote(article, safe='')}/monthly/{start}/{end}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return sum(item.get("views", 0) for item in data.get("items", []))


def collect_wikipedia(months: int = 12) -> Dict:
    """Return a dict with per-article pageview totals over the trailing months."""
    today = date.today().replace(day=1)
    start_d = today - timedelta(days=months * 31)
    start = start_d.strftime("%Y%m01")
    end = today.strftime("%Y%m01")

    rows: List[dict] = []
    for project, article, label in _ARTICLES:
        try:
            views = _fetch_article(project, article, start, end)
            rows.append({"project": project, "article": article,
                         "label": label, "views": views})
            logger.info("Wikipedia %s: %d views (%s–%s)", label, views, start, end)
        except Exception as e:  # noqa: BLE001 - network / 404 on missing article
            logger.warning("Wikipedia fetch failed for %s/%s: %s", project, article, e)

    rows.sort(key=lambda r: r["views"], reverse=True)
    return {
        "window": {"start": start, "end": end, "months": months,
                   "granularity": "monthly", "access": "all-access", "agent": "user"},
        "articles": rows,
        "total_views": sum(r["views"] for r in rows),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s",
                        datefmt="%H:%M:%S")
    result = collect_wikipedia()
    out = Path = __import__("pathlib").Path(__file__).parent / "output" / "wikipedia_data.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out} — total {result['total_views']:,} views across "
          f"{len(result['articles'])} articles.")
