"""Shared cache-rebuild routine used by both build_cache.py and POST /rebuild-cache.

This is the ONLY place that incurs API cost: it classifies every post with the
local model and calls Gemini for analysis on flagged posts, then overwrites
cache.json. Normal startup never calls this -- the backend is cache-first.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Callable, Optional

log = logging.getLogger("infoshield.rebuild")


def rebuild_cache(cache, posts, on_post: Optional[Callable[[str, dict], None]] = None) -> dict:
    """Reclassify + re-analyze all posts into `cache` (in-memory + on disk).

    `on_post(post_id, classification)` is an optional progress callback.
    Returns a summary dict. The caller's in-memory cache is updated, so results
    are live immediately with no restart.
    """
    from analyzer import available as gemini_available, generate_analysis
    from classifier import get_classifier

    clf = get_classifier()
    clf.load()  # device select + warmup + label sanity check

    flagged = 0
    for post in posts:
        classification = clf.classify(post["text"])
        analysis = None
        if classification["flagged"]:
            flagged += 1
            analysis = generate_analysis(post["text"])
        cache.set(post["id"], classification, analysis)
        if on_post:
            on_post(post["id"], classification)

    cache.set_meta(
        model=clf.model_name,
        device=clf.device,
        warmup_ms=clf.warmup_ms,
        gemini=gemini_available(),
        built_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    cache.save()

    summary = {
        "posts": len(posts),
        "flagged": flagged,
        "model": clf.model_name,
        "device": clf.device,
        "gemini": gemini_available(),
    }
    log.info("Rebuild complete: %s", summary)
    return summary
