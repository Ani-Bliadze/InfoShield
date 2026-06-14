"""InfoShield Flask backend.

Cache-first by design: on startup it serves a pre-built JSON cache so the demo
is instant and works fully offline. Heavy ML / Gemini code is imported lazily,
so this process starts with only Flask installed when serving from cache.
"""
from __future__ import annotations

import logging
from collections import Counter
from urllib.parse import urlparse

from flask import Flask, jsonify, request
from flask_cors import CORS

import config
from cache import (
    get_cache,
    load_activation,
    load_posts,
    save_activation,
    text_hash,
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
    """Attach cached classification + analysis to a raw post (author-agnostic)."""
    cached = CACHE.get(post["id"]) or {}
    return {
        **post,
        "classification": cached.get("classification"),
        "analysis": cached.get("analysis"),
        "flagged": bool((cached.get("classification") or {}).get("flagged")),
    }


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

    clf = get_classifier()
    return jsonify({
        "status": "ok",
        "service": "infoshield",
        "cache_mode": CACHE.mode,
        "cache_built_at": CACHE.meta.get("built_at"),
        "model": CACHE.meta.get("model") or config.PRIMARY_MODEL,
        "model_loaded": clf.loaded,
        "device": clf.device if clf.loaded else CACHE.meta.get("device", "unknown"),
        "posts": len(POSTS),
        "gemini_configured": bool(config.GEMINI_API_KEY),
    })


@app.get("/feed")
def feed():
    return jsonify({"posts": [_merged_post(p) for p in POSTS]})


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
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    key = text_hash(text)
    if key in CACHE.adhoc and "classification" in CACHE.adhoc[key]:
        return jsonify(CACHE.adhoc[key]["classification"])
    from classifier import get_classifier

    try:
        result = get_classifier().classify(text)
    except Exception as exc:  # noqa: BLE001
        log.error("classify failed: %s", exc)
        return jsonify({"error": "classifier unavailable", "detail": str(exc)}), 503
    CACHE.adhoc.setdefault(key, {})["classification"] = result
    return jsonify(result)


@app.post("/analyze")
def analyze():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    if not text:
        return jsonify({"error": "empty text"}), 400
    key = text_hash(text)
    if key in CACHE.adhoc and "analysis" in CACHE.adhoc[key]:
        return jsonify(CACHE.adhoc[key]["analysis"])
    from analyzer import generate_analysis

    analysis = generate_analysis(text)
    CACHE.adhoc.setdefault(key, {})["analysis"] = analysis
    return jsonify(analysis)


@app.get("/stats")
def stats():
    flagged = [_merged_post(p) for p in POSTS if (CACHE.get(p["id"]) or {}).get("classification", {}).get("flagged")]
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
            "name": CACHE.meta.get("model") or config.PRIMARY_MODEL,
            "device": CACHE.meta.get("device", "unknown"),
            "flag_threshold": config.FLAG_THRESHOLD,
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
        "cache_mode": CACHE.mode,
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
    log.info("InfoShield backend starting on http://%s:%d (cache=%s)",
             config.HOST, config.PORT, CACHE.mode)
    app.run(host=config.HOST, port=config.PORT, debug=False)
