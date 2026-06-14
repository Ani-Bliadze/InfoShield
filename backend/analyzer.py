"""Educational manipulation-technique analysis via Gemini.

Privacy: only the post *text* is ever sent to Gemini. Usernames, handles, and
any author metadata are never included. The SDK import is deferred so the
backend runs cache-first without `google-genai` installed.

If the key is missing, the SDK is absent, or Gemini fails/blocks/returns bad
JSON, this module degrades to a local heuristic analysis so the demo never
crashes.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Optional

from config import (
    ALLOWED_TECHNIQUES,
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_SYSTEM_INSTRUCTION,
    MAX_EXPLANATION_CHARS,
    TECHNIQUE_LABELS,
)

log = logging.getLogger("infoshield.analyzer")

ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "techniques": {
            "type": "array",
            "items": {"type": "string", "enum": ALLOWED_TECHNIQUES},
        },
        "emotional_triggers": {"type": "array", "items": {"type": "string"}},
        "explanation": {"type": "string"},
        "recommendation": {"type": "string"},
        "severity": {"type": "string", "enum": ["low", "medium", "high"]},
        "highlights": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "phrase": {"type": "string"},
                    "type": {"type": "string"},
                    "label": {"type": "string"},
                },
                "required": ["phrase", "type", "label"],
            },
        },
    },
    "required": [
        "techniques",
        "emotional_triggers",
        "explanation",
        "recommendation",
        "severity",
        "highlights",
    ],
}

_USER_PROMPT = (
    "Analyze the following social-media post text for manipulation techniques. "
    "Identify which techniques (from the allowed set) are present, the emotional "
    "triggers it leans on, a concise neutral explanation of HOW it tries to "
    "influence the reader, a calm non-judgmental recommendation, an overall "
    "severity, and the exact phrases (copied verbatim from the text) that "
    "illustrate each technique.\n\nPOST TEXT:\n\"\"\"\n{text}\n\"\"\""
)

_client = None
_client_tried = False


def _get_client():
    global _client, _client_tried
    if _client_tried:
        return _client
    _client_tried = True
    if not GEMINI_API_KEY:
        log.warning("GEMINI_API_KEY not set -- analyses will use local fallback.")
        return None
    try:
        from google import genai  # deferred

        _client = genai.Client(api_key=GEMINI_API_KEY)
        log.info("Gemini client initialized (model=%s).", GEMINI_MODEL)
    except Exception as exc:  # noqa: BLE001
        log.warning("Could not initialize Gemini client: %s", exc)
        _client = None
    return _client


def available() -> bool:
    return _get_client() is not None


# --- validation -----------------------------------------------------------
def _coerce_json(text: str) -> Optional[dict]:
    if not text:
        return None
    text = text.strip()
    # Strip accidental markdown fences.
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                return None
    return None


def validate_analysis(raw: dict, text: str) -> Optional[dict]:
    """Enforce allowlist, exact-substring highlights, no overlaps, length caps."""
    if not isinstance(raw, dict):
        return None
    lower = text.lower()

    techniques = [t for t in raw.get("techniques", []) if t in ALLOWED_TECHNIQUES]
    techniques = list(dict.fromkeys(techniques))  # de-dupe, keep order

    triggers = [str(t).strip() for t in raw.get("emotional_triggers", []) if str(t).strip()]
    triggers = list(dict.fromkeys(triggers))[:6]

    explanation = str(raw.get("explanation", "")).strip()[:MAX_EXPLANATION_CHARS]
    recommendation = str(raw.get("recommendation", "")).strip()[:200]

    severity = raw.get("severity")
    if severity not in ("low", "medium", "high"):
        severity = "medium"

    highlights = []
    used_spans: list[tuple[int, int]] = []
    for h in raw.get("highlights", []):
        if not isinstance(h, dict):
            continue
        phrase = str(h.get("phrase", "")).strip()
        if not phrase:
            continue
        idx = lower.find(phrase.lower())
        if idx == -1:  # must be an exact (case-insensitive) substring
            continue
        span = (idx, idx + len(phrase))
        if any(span[0] < e and s < span[1] for s, e in used_spans):  # overlap
            continue
        used_spans.append(span)
        htype = str(h.get("type", "")).strip() or "emotional_manipulation"
        label = str(h.get("label", "")).strip() or TECHNIQUE_LABELS.get(
            htype, htype.replace("_", " ").title()
        )
        # Use the exact original-case substring from the source text.
        exact = text[idx: idx + len(phrase)]
        highlights.append({"phrase": exact, "type": htype, "label": label})

    if not techniques and not highlights:
        return None
    return {
        "techniques": techniques,
        "emotional_triggers": triggers,
        "explanation": explanation,
        "recommendation": recommendation,
        "severity": severity,
        "highlights": highlights,
    }


# --- local fallback -------------------------------------------------------
_HEURISTICS = {
    "false_urgency": ["now", "before it", "immediately", "act now", "midnight", "by monday", "running out", "last chance", "don't wait"],
    "fear_amplification": ["destroy", "lose everything", "collapse", "disaster", "danger", "afraid", "terrify", "catastroph", "doom"],
    "us_vs_them": ["us against them", "they", "them", "elites", "those people", "our side", "their side", "wake up"],
    "scapegoating": ["blame", "fault", "because of them", "the reason", "responsible for"],
    "dehumanizing_language": ["vermin", "animals", "infest", "not like us", "parasite", "swarm", "flood"],
    "ad_hominem": ["idiot", "fool", "stupid", "liar", "sheep", "too foolish"],
    "emotional_manipulation": ["share this", "they don't want you", "hiding the truth", "stay angry", "open your eyes"],
}

_TRIGGER_WORDS = {
    "fear": ["destroy", "lose", "danger", "afraid", "collapse", "shut", "forever"],
    "anger": ["elites", "them", "liar", "blame", "angry"],
    "urgency": ["now", "before", "midnight", "monday", "immediately"],
    "belonging": ["us", "our values", "who we are", "community"],
}


def local_fallback_analysis(text: str) -> dict:
    """Deterministic heuristic analysis used when Gemini is unavailable."""
    lower = text.lower()
    techniques, highlights, used = [], [], []
    for tech, cues in _HEURISTICS.items():
        for cue in cues:
            idx = lower.find(cue)
            if idx == -1:
                continue
            if tech not in techniques:
                techniques.append(tech)
            span = (idx, idx + len(cue))
            if not any(span[0] < e and s < span[1] for s, e in used):
                used.append(span)
                highlights.append({
                    "phrase": text[idx: idx + len(cue)],
                    "type": tech,
                    "label": TECHNIQUE_LABELS.get(tech, tech.replace("_", " ").title()),
                })
            break
    triggers = [name for name, words in _TRIGGER_WORDS.items() if any(w in lower for w in words)]
    if not techniques:
        techniques = ["emotional_manipulation"]
    severity = "high" if len(techniques) >= 3 else "medium" if len(techniques) == 2 else "low"
    return {
        "techniques": techniques[:4],
        "emotional_triggers": triggers[:4] or ["emotional reaction"],
        "explanation": (
            "This post leans on emotionally charged language and framing that "
            "pushes a strong reaction rather than inviting reflection."
        ),
        "recommendation": "Take a moment before sharing and check whether the claim holds up calmly.",
        "severity": severity,
        "highlights": highlights[:6],
        "source": "local_fallback",
    }


# --- main entry -----------------------------------------------------------
def _call_gemini(text: str, strict: bool = False) -> Optional[dict]:
    client = _get_client()
    if client is None:
        return None
    from google.genai import types  # deferred

    prompt = _USER_PROMPT.format(text=text)
    if strict:
        prompt += (
            "\n\nIMPORTANT: Output MUST be a single valid JSON object matching the "
            "schema exactly. No markdown fences, no commentary."
        )
    try:
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=GEMINI_SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=ANALYSIS_SCHEMA,
                temperature=0.3,
            ),
        )
        return _coerce_json(getattr(resp, "text", "") or "")
    except Exception as exc:  # noqa: BLE001
        log.warning("Gemini call failed (strict=%s): %s", strict, exc)
        return None


def generate_analysis(text: str) -> dict:
    """Return a validated analysis dict; never raises for normal input."""
    if not text or not text.strip():
        return local_fallback_analysis("")

    raw = _call_gemini(text, strict=False)
    analysis = validate_analysis(raw, text) if raw else None
    if analysis is None:
        # One retry with stronger formatting instructions.
        raw = _call_gemini(text, strict=True)
        analysis = validate_analysis(raw, text) if raw else None
    if analysis is None:
        analysis = local_fallback_analysis(text)
    else:
        analysis["source"] = "gemini"
    return analysis
