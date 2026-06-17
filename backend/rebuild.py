"""Shared cache-rebuild routine used by both build_cache.py and POST /rebuild-cache.

Serving is real-time now (pipeline.py), so this is only for building an offline
snapshot. It runs the same two-gate pipeline (local hate model + LLM manipulation
detector/explainer) over every post and writes data/cache.json.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable, Optional

import config

log = logging.getLogger("infoshield.rebuild")


def rebuild_cache(cache, posts, on_post: Optional[Callable[[str, dict], None]] = None) -> dict:
    """Reclassify + re-analyze all posts into `cache` (in-memory + on disk).

    `on_post(post_id, classification)` is an optional progress callback.
    """
    from classifier import get_classifier
    from llm import available as llm_available
    from pipeline import analyze_post

    clf = get_classifier()
    clf.load()  # device select + warmup + label sanity check

    flagged = 0
    for post in posts:
        classification, analysis = analyze_post(post["text"])
        if classification["flagged"]:
            flagged += 1
        cache.set(post["id"], classification, analysis)
        if on_post:
            on_post(post["id"], classification)

    cache.set_meta(
        model=clf.model_name,
        device=clf.device,
        warmup_ms=clf.warmup_ms,
        llm_provider=config.LLM_PROVIDER,
        llm=llm_available(),
        built_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    cache.save()

    summary = {
        "posts": len(posts),
        "flagged": flagged,
        "model": clf.model_name,
        "device": clf.device,
        "llm_provider": config.LLM_PROVIDER,
        "llm": llm_available(),
    }
    log.info("Rebuild complete: %s", summary)
    return summary
