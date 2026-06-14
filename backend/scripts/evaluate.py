"""Quick sanity evaluation of the local classifier.

Runs a small labeled probe set and prints per-example results plus accuracy and
the resolved device/label map. This is a smoke test, not a benchmark.

Run:  python backend/scripts/evaluate.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from classifier import get_classifier  # noqa: E402

# (text, expected_flagged). NOTE: this is a HATE-SPEECH classifier. It flags
# group-directed hostility, NOT generic manipulation/urgency/insults -- those are
# correctly left to Gemini's broader manipulation analysis. The probes reflect
# that division of labour.
PROBES = [
    # Benign -> not flagged
    ("Have a lovely weekend, everyone!", False),
    ("The library extended its opening hours this month.", False),
    ("Thanks for the thoughtful feedback on my draft.", False),
    # Manipulative but NOT hate speech -> a hate model should NOT flag these
    ("Act now before midnight or you will lose everything forever!", False),
    ("Anyone who disagrees is a brainless fool.", False),
    # Genuine hate speech (synthetic, unnamed groups) -> flagged
    ("Those people are vermin and should be removed.", True),
    ("They are subhuman filth and don't belong here.", True),
    ("People like that are animals who should be driven out of our town.", True),
]


def main() -> None:
    clf = get_classifier()
    clf.load()
    print(f"\nDevice: {clf.device} | Model: {clf.model_name} | warmup ~{clf.warmup_ms} ms")
    print("(Hate-speech model: flags group hostility; manipulation is handled by Gemini analysis.)\n")

    correct = 0
    for text, expected in PROBES:
        res = clf.classify(text)
        ok = res["flagged"] == expected
        correct += ok
        mark = "PASS" if ok else "FAIL"
        print(f"  [{mark}] flagged={res['flagged']!s:<5} conf={res['confidence']:.2f}  {text[:54]}")
    print(f"\nAccuracy on probes: {correct}/{len(PROBES)} = {correct / len(PROBES):.0%}")


if __name__ == "__main__":
    main()
