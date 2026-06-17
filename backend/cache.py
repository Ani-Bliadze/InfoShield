"""JSON-file + in-memory caching. No database.

- `cache.json` holds per-post classification + analysis so the demo is instant
  and works fully offline after one build.
- `activation.json` holds the landing-page-selected target URL and on/off state.
- An in-memory dict caches ad-hoc /classify and /analyze results by content hash.
"""
from __future__ import annotations

import hashlib
import json
import logging
import threading
from datetime import datetime, timezone
from typing import Optional

from config import ACTIVATION_FILE, CACHE_FILE, CACHE_VERSION, DATA_DIR, POSTS_FILE

log = logging.getLogger("infoshield.cache")
_lock = threading.Lock()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def text_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:16]


# --- posts ----------------------------------------------------------------
def load_posts() -> list[dict]:
    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


# --- post cache -----------------------------------------------------------
class PostCache:
    def __init__(self) -> None:
        self.meta: dict = {}
        self.posts: dict[str, dict] = {}
        self.adhoc: dict[str, dict] = {}  # content-hash -> {classification, analysis}

    def load(self) -> bool:
        if not CACHE_FILE.exists():
            log.warning("Cache file %s not found -- starting empty.", CACHE_FILE)
            return False
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.meta = data.get("meta", {})
            self.posts = data.get("posts", {})
            if self.meta.get("version") != CACHE_VERSION:
                log.info("Cache version mismatch (have %s, want %s) -- discarding stale cache.",
                         self.meta.get("version"), CACHE_VERSION)
                self.posts = {}
                self.meta = {}
                return False
            log.info("Loaded cache: %d posts (built_at=%s).",
                     len(self.posts), self.meta.get("built_at"))
            return True
        except Exception as exc:  # noqa: BLE001
            log.error("Failed to load cache: %s", exc)
            return False

    def save(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.meta["version"] = CACHE_VERSION
        with _lock:
            payload = {"meta": self.meta, "posts": self.posts}
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        log.info("Cache saved (%d posts).", len(self.posts))

    def get(self, post_id: str) -> Optional[dict]:
        return self.posts.get(post_id)

    def set(self, post_id: str, classification: dict, analysis: Optional[dict]) -> None:
        self.posts[post_id] = {"classification": classification, "analysis": analysis}

    def set_meta(self, **kw) -> None:
        self.meta.update(kw)
        self.meta["built_at"] = _now()
        self.meta["version"] = CACHE_VERSION

    @property
    def mode(self) -> str:
        return "cache-first" if self.posts else "empty"


_cache: Optional[PostCache] = None


def get_cache() -> PostCache:
    global _cache
    if _cache is None:
        _cache = PostCache()
        _cache.load()
    return _cache


# --- activation config ----------------------------------------------------
DEFAULT_ACTIVATION = {
    "target_url": "",
    "enabled": False,
    "updated_at": None,
}


def load_activation() -> dict:
    if not ACTIVATION_FILE.exists():
        return dict(DEFAULT_ACTIVATION)
    try:
        with open(ACTIVATION_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {**DEFAULT_ACTIVATION, **data}
    except Exception:  # noqa: BLE001
        return dict(DEFAULT_ACTIVATION)


def save_activation(target_url: str, enabled: bool = True) -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cfg = {
        "target_url": target_url,
        "enabled": enabled,
        "updated_at": _now(),
    }
    with _lock:
        with open(ACTIVATION_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    log.info("Activation target saved: %s (enabled=%s)", target_url, enabled)
    return cfg


def reset_activation() -> dict:
    """Reset activation to default (disabled) so each fresh run starts at the
    landing page's ACTIVATE button."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with _lock:
        with open(ACTIVATION_FILE, "w", encoding="utf-8") as f:
            json.dump(dict(DEFAULT_ACTIVATION), f, ensure_ascii=False, indent=2)
    log.info("Activation reset to default (fresh demo).")
    return dict(DEFAULT_ACTIVATION)
