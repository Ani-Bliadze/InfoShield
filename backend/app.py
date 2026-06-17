"""InfoShield Flask backend.

Cache-first by design: on startup it serves a pre-built JSON cache so the demo
is instant and works fully offline. Heavy ML / Gemini code is imported lazily,
so this process starts with only Flask installed when serving from cache.
"""
from __future__ import annotations

import logging
import threading
from collections import Counter
from urllib.parse import urlparse

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

import config
from cache import (
    get_cache,
    load_activation,
    load_posts,
    reset_activation,
    save_activation,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("infoshield.app")

app = Flask(__name__)
CORS(app)  # localhost demo: allow the Vite frontend and the extension to call us.

POSTS = load_posts()
POSTS_BY_ID = {p["id"]: p for p in POSTS}
CACHE = get_cache()


# --- helpers --------------------------------------------------------------
def _merged_post(post: dict) -> dict:
    """Serve cached classification + analysis; compute, store, and persist on a miss
    so activating the extension shows saved results instantly."""
    cached = CACHE.get(post["id"])
    if not cached or not cached.get("classification"):
        from pipeline import analyze_post

        classification, analysis = analyze_post(post["text"])
        CACHE.set(post["id"], classification, analysis)
        CACHE.save()
        cached = {"classification": classification, "analysis": analysis}
    cls = cached.get("classification") or {}
    return {
        **post,
        "classification": cls,
        "analysis": cached.get("analysis"),
        "flagged": bool(cls.get("flagged")),
    }


def _warm_cache() -> None:
    """Background pre-warm: compute analysis for any uncached posts so the demo is
    instant by the time the user activates the extension."""
    try:
        from classifier import get_classifier
        from manip_classifier import get_manip_classifier

        get_classifier().load()
        get_manip_classifier().load()
        missing = [p for p in POSTS if not (CACHE.get(p["id"]) or {}).get("classification")]
        if not missing:
            log.info("Cache already warm (%d posts).", len(POSTS))
            return
        log.info("Warming cache for %d post(s) in background ...", len(missing))
        for p in missing:
            _merged_post(p)
        log.info("Cache warm complete.")
    except Exception as exc:  # noqa: BLE001
        log.warning("Cache warm failed: %s", exc)


def _is_localhost(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:  # noqa: BLE001
        return False
    return host in ("localhost", "127.0.0.1", "0.0.0.0", "::1")


# --- routes ---------------------------------------------------------------
@app.get("/health")
def health():
    from classifier import get_classifier

    from llm import available as llm_available

    clf = get_classifier()
    cached = sum(1 for p in POSTS if (CACHE.get(p["id"]) or {}).get("classification"))
    return jsonify({
        "status": "ok",
        "service": "infoshield",
        "mode": "cached",
        "hate_model": config.PRIMARY_MODEL,
        "manipulation_model": config.MANIP_MODEL,
        "model_loaded": clf.loaded,
        "device": clf.device if clf.loaded else "unknown",
        "posts": len(POSTS),
        "cached_posts": cached,
        "llm_provider": config.LLM_PROVIDER,
        "verifier_model": config.VERIFIER_MODEL,
        "llm_configured": llm_available(),
    })


@app.get("/feed")
def feed():
    return jsonify({"posts": [_merged_post(p) for p in POSTS]})


@app.get("/media/<path:filename>")
def media(filename: str):
    """Serve demo media (e.g. the feed video) from backend/data."""
    return send_from_directory(config.DATA_DIR, filename)


@app.get("/post-analysis/<post_id>")
def post_analysis(post_id: str):
    post = POSTS_BY_ID.get(post_id)
    if post is None:
        return jsonify({"error": "unknown post id"}), 404
    merged = _merged_post(post)
    return jsonify({
        "id": post_id,
        "text": post["text"],
        "classification": merged["classification"],
        "analysis": merged["analysis"],
        "flagged": merged["flagged"],
    })


@app.post("/rebuild-cache")
def rebuild_cache_endpoint():
    """Trigger a full live rebuild (local classifier + Gemini) and overwrite the
    cache. This is the ONLY endpoint that incurs API cost. Results are live
    immediately -- it updates the in-memory cache, no restart needed."""
    from rebuild import rebuild_cache

    try:
        summary = rebuild_cache(CACHE, POSTS)
    except Exception as exc:  # noqa: BLE001
        log.error("rebuild failed: %s", exc)
        return jsonify({"status": "error", "error": str(exc)}), 503
    return jsonify({"status": "ok", **summary})


@app.post("/classify")
def classify():
    """Hate-only classification of arbitrary text (live, content-only)."""
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    from classifier import get_classifier

    try:
        return jsonify(get_classifier().classify(text))
    except Exception as exc:  # noqa: BLE001
        log.error("classify failed: %s", exc)
        return jsonify({"error": "classifier unavailable", "detail": str(exc)}), 503


@app.post("/analyze")
def analyze():
    """Manipulation detection + educational analysis of arbitrary text (live)."""
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "empty text"}), 400
    from analyzer import detect_and_analyze

    return jsonify(detect_and_analyze(text))


@app.get("/stats")
def stats():
    posts = [_merged_post(p) for p in POSTS]
    flagged = [p for p in posts if p["flagged"]]
    tech_counter: Counter = Counter()
    confidences = []
    high_conf = 0
    for p in flagged:
        cls = p["classification"] or {}
        confidences.append(cls.get("confidence", 0.0))
        if cls.get("high_confidence"):
            high_conf += 1
        for t in (p["analysis"] or {}).get("techniques", []):
            tech_counter[t] += 1

    distribution = {t: tech_counter.get(t, 0) for t in config.ALLOWED_TECHNIQUES if tech_counter.get(t)}
    most_common = tech_counter.most_common(1)
    most_common_technique = most_common[0][0] if most_common else None
    most_common_label = (
        config.TECHNIQUE_LABELS.get(most_common_technique, most_common_technique)
        if most_common_technique else "—"
    )

    return jsonify({
        "totals": {
            "posts": len(POSTS),
            "flagged": len(flagged),
            "benign": len(POSTS) - len(flagged),
        },
        "technique_distribution": distribution,
        "most_common_technique": most_common_technique,
        "confidences": {
            "mean_flagged": round(sum(confidences) / len(confidences), 3) if confidences else 0,
            "max": round(max(confidences), 3) if confidences else 0,
            "min": round(min(confidences), 3) if confidences else 0,
            "high_confidence_count": high_conf,
        },
        "model": {
            "hate_model": config.PRIMARY_MODEL,
            "manipulation_model": config.MANIP_MODEL,
            "llm_provider": config.LLM_PROVIDER,
            "analyzer_model": config.GEMINI_MODEL if config.LLM_PROVIDER == "gemini" else config.GROQ_MODEL,
            "verifier_model": config.VERIFIER_MODEL,
            "flag_threshold": config.FLAG_THRESHOLD,
            "manipulation_threshold": config.MANIP_THRESHOLD,
            "high_confidence": config.HIGH_CONFIDENCE,
        },
        # Data-driven snapshot. The right-rail widget now renders from the
        # extension's live page scan; this stays as an honest API view.
        "insights": {
            "scanned": len(POSTS),
            "posts_analyzed": len(POSTS),
            "patterns_detected": len(distribution),
            "most_common_pattern": most_common_label,
        },
        "mode": "cached",
    })


@app.get("/activation-target")
def get_activation_target():
    return jsonify(load_activation())


@app.post("/activation-target")
def set_activation_target():
    data = request.get_json(silent=True) or {}
    url = (data.get("target_url") or "").strip()
    enabled = bool(data.get("enabled", True))
    if not url:
        return jsonify({"error": "target_url is required"}), 400
    if not url.startswith("http://") or not _is_localhost(url):
        return jsonify({
            "error": "target_url must be a localhost address "
                     "(http://localhost/... or http://127.0.0.1/...)"
        }), 400
    return jsonify(save_activation(url, enabled))


@app.get("/")
def root():
    return jsonify({
        "service": "InfoShield backend",
        "routes": [
            "/health", "/feed", "/post-analysis/<id>", "/classify",
            "/analyze", "/stats", "/activation-target",
        ],
    })


if __name__ == "__main__":
    if config.RESET_ACTIVATION_ON_START:
        reset_activation()
        log.info("Activation reset to default on startup (fresh demo).")
    # Pre-warm the analysis cache in the background so activation is instant.
    threading.Thread(target=_warm_cache, daemon=True).start()
    log.info("InfoShield backend starting on http://%s:%d (provider=%s, cached)",
             config.HOST, config.PORT, config.LLM_PROVIDER)
    app.run(host=config.HOST, port=config.PORT, debug=False)
