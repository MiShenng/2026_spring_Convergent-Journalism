"""Orchestrator: collect overseas platform data, analyze, write JSON.

Usage (from this folder, with secrets exported or in a .env you've sourced):

    cd scraper
    python run.py

Output: output/overseas_data.json  — send this file back to fill the webpage.
"""
from __future__ import annotations

import json
import logging

from analyze import build_dataset
from collect_reddit import collect_reddit
from collect_youtube import collect_youtube
from config import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("run")


def main() -> None:
    cfg = load_config()
    logger.info("Keywords: %s", ", ".join(cfg.keywords))

    items, comments = [], []
    for collector in (collect_youtube, collect_reddit):
        c_items, c_comments = collector(cfg)
        items.extend(c_items)
        comments.extend(c_comments)

    if not items and not comments:
        logger.error(
            "Nothing collected. Set YOUTUBE_API_KEY and/or REDDIT_CLIENT_ID + "
            "REDDIT_CLIENT_SECRET (see .env.example) and install requirements."
        )
        return

    dataset = build_dataset(items, comments, cfg)
    cfg.output_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.output_path.write_text(
        json.dumps(dataset, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    kpi = dataset["kpi"]
    logger.info(
        "Done. items=%d comments=%d languages=%d -> %s",
        kpi["items"], kpi["comments"], kpi["languages"], cfg.output_path,
    )


if __name__ == "__main__":
    main()
