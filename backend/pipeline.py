"""Per-post analysis pipeline -- the single source of truth for serving.

For each post text:
  1. HATE gate        -- local RoBERTa classifier  -> hate_confidence
  2. MANIPULATION gate -- local propaganda classifier -> manipulation_confidence
  3. If either fires -> LLM ANALYSIS (hate or manipulation prompt) explains WHY.
  4. VERIFIER (2nd LLM) judges the analysis; if it's not relevant/accurate the
     flag is overturned (treated as a false positive).

Both gates are local (fast, free), so the LLM only runs on flagged posts. Results
are cached by the caller (app.py) so the demo serves saved analysis instantly.
"""
from __future__ import annotations

import logging
import threading

from config import HIGH_CONFIDENCE

log = logging.getLogger("infoshield.pipeline")

_clf_lock = threading.Lock()  # serialize the (fast) local models across threads


def analyze_post(text: str) -> tuple[dict, dict | None]:
    """Return (classification, analysis-or-None) for one post text."""
    from analyzer import analyze, verify
    from classifier import get_classifier
    from manip_classifier import get_manip_classifier

    with _clf_lock:
        hate = get_classifier().classify(text)
        manip = get_manip_classifier().classify(text)

    hate_conf = float(hate.get("confidence", 0.0))
    manip_conf = float(manip.get("confidence", 0.0))
    hate_flag = bool(hate.get("flagged"))
    manip_flag = bool(manip.get("flagged"))
    flagged = hate_flag or manip_flag

    analysis = None
    verification = None
    kind = None
    if flagged:
        kind = "hate" if hate_flag else "manipulation"
        analysis = analyze(text, kind)
        verification = verify(text, analysis, kind)
        # Overturn (false positive) if EITHER the verifier judged the analysis
        # irrelevant, OR a manipulation flag produced no concrete technique/
        # highlight (deterministic precision guard; hate keeps its high-precision flag).
        empty = not analysis.get("techniques") and not analysis.get("highlights")
        if not verification.get("relevant", True) or (kind == "manipulation" and empty):
            flagged = False
            analysis = None
            kind = None

    trigger_conf = hate_conf if (kind == "hate") else manip_conf if (kind == "manipulation") else max(hate_conf, manip_conf)
    classification = {
        "label": "FLAGGED" if flagged else "CLEAR",
        "flagged": flagged,
        "kind": kind if flagged else None,
        "confidence": round(trigger_conf, 4),
        "hate_confidence": round(hate_conf, 4),
        "manipulation_confidence": round(manip_conf, 4),
        "high_confidence": flagged and trigger_conf >= HIGH_CONFIDENCE,
        "truncated": bool(hate.get("truncated")),
        "raw_scores": hate.get("raw_scores", {}),
        "model": hate.get("model"),
        "verification": verification,
    }
    return classification, analysis
