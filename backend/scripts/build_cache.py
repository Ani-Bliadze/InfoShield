"""Build the demo cache with the REAL pipeline: local classifier + Gemini.

For every seed post: classify locally (content-only, author-agnostic), and if
flagged, generate an educational analysis via Gemini (text only). Persists to
data/cache.json. Same routine the backend exposes at POST /rebuild-cache.

Requires torch + transformers installed; Gemini is optional (falls back to a
local heuristic analysis if GEMINI_API_KEY is unset).

Run:  python backend/scripts/build_cache.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from analyzer import available as gemini_available  # noqa: E402
from cache import get_cache, load_posts  # noqa: E402
from rebuild import rebuild_cache  # noqa: E402


def main() -> None:
    posts = load_posts()
    cache = get_cache()
    print(f"Gemini available: {gemini_available()}")
    print(f"Building cache for {len(posts)} posts ...\n")

    def progress(pid: str, classification: dict) -> None:
        tag = "FLAG" if classification["flagged"] else "ok  "
        print(f"  [{tag}] {pid:>3}  conf={classification['confidence']:.2f}")

    summary = rebuild_cache(cache, posts, on_post=progress)
    print(f"\nDone. {summary['flagged']} flagged / {summary['posts']} posts "
          f"on {summary['device']}. Cache written.")


if __name__ == "__main__":
    main()
