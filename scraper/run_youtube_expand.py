"""Expanded YouTube-only re-collection -> output/overseas_data.json.

Reddit credentials are dead (401), and the page will drop the Reddit/TikTok/IG/X
rows, so this runner skips Reddit entirely and just deepens the YouTube sample:
more keywords, more videos per keyword. Quota stays well under the 10k/day budget.

Loads .env manually (tolerating stray spaces), then reuses the existing
collect_youtube + analyze pipeline so the JSON shape stays identical.
"""
from __future__ import annotations

import dataclasses
import json
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("run_youtube_expand")


def _load_env() -> None:
    path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main() -> None:
    _load_env()
    from analyze import build_dataset
    from collect_youtube import collect_youtube
    from config import load_config

    base = load_config()
    # Deepen the sample: broader keywords + more videos per keyword.
    cfg = dataclasses.replace(
        base,
        keywords=(
            "Dunhuang",
            "flying apsara",
            "feitian",
            "Dunhuang mural",
            "Mogao caves",
            "Dunhuang dance",
            "敦煌飞天",
            "apsara dance",
            "Dunhuang Buddhist art",
            "Silk Road Dunhuang",
        ),
        max_videos_per_keyword=120,
        max_comments_per_item=100,
    )
    logger.info("Keywords (%d): %s", len(cfg.keywords), ", ".join(cfg.keywords))

    if not cfg.youtube_api_key:
        logger.error("YOUTUBE_API_KEY missing; aborting.")
        return

    items, comments = collect_youtube(cfg)
    if not items:
        logger.error("No videos collected (quota or key issue?); leaving existing JSON untouched.")
        return

    dataset = build_dataset(items, comments, cfg)
    out = cfg.output_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8")

    kpi = dataset["kpi"]
    eng = dataset.get("engagement", {})
    logger.info(
        "DONE. videos=%d comments=%d languages=%d total_views=%s median_views=%s -> %s",
        kpi["items"], kpi["comments"], kpi["languages"],
        eng.get("total_views"), eng.get("median_views"), out,
    )


if __name__ == "__main__":
    main()
