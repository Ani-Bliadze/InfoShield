"""One-time, run-while-online model download.

Pulls the primary (and fallback) hate-speech checkpoints into the local
Hugging Face cache so the demo can later run with Wi-Fi off.

Run:  python backend/scripts/download_models.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config import FALLBACK_MODEL, PRIMARY_MODEL  # noqa: E402


def fetch(name: str) -> bool:
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    print(f"\n=== Downloading {name} ===")
    try:
        AutoTokenizer.from_pretrained(name)
        AutoModelForSequenceClassification.from_pretrained(name)
        print(f"  OK: {name} cached.")
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"  FAILED: {name} -> {exc}")
        return False


def main() -> None:
    ok_primary = fetch(PRIMARY_MODEL)
    ok_fallback = fetch(FALLBACK_MODEL)
    if not ok_primary and not ok_fallback:
        raise SystemExit("Could not download any classifier model. Check your connection.")
    print("\nDone. You can now build the cache (build_cache.py) and run offline.")


if __name__ == "__main__":
    main()
