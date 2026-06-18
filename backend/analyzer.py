"""Educational analysis (the explainer) + verifier (the judge).

The local models (hate + manipulation) decide WHETHER a post is flagged. This
module decides WHY:
  * analyze(text, kind)  -- runs the hate OR manipulation analysis prompt and
                            returns techniques / severity / explanation / highlights.
  * verify(text, analysis, kind) -- a second LLM pass that judges whether the
                            analysis is accurate/relevant; if not, the caller
                            overturns the flag (false positive).

Provider-agnostic (llm.py): Groq now, Gemini later. Privacy: only post text is
sent. If the LLM is unavailable, analyze() degrades to a local heuristic and
verify() fails open (keeps the original decision).
"""
from __future__ import annotations

import json
import logging
from typing import Optional

from config import (
    ALLOWED_TECHNIQUES,
    ANALYSIS_SYSTEM_INSTRUCTION,
    HATE_ANALYSIS_PROMPT,
    LEGAL_SOURCE_URLS,
    MANIPULATION_ANALYSIS_PROMPT,
    MAX_EXPLANATION_CHARS,
    REPHRASE_PROMPT,
    REPHRASE_SYSTEM_INSTRUCTION,
    TECHNIQUE_LABELS,
    VERIFIER_MODEL,
    VERIFIER_PROMPT,
    VERIFIER_PROVIDER,
    VERIFIER_SYSTEM_INSTRUCTION,
)
from llm import available, complete_json  # noqa: F401  (available re-exported)

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
        "bias_check": {"type": "string"},
        "citations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["techniques", "emotional_triggers", "explanation",
                 "recommendation", "severity", "highlights", "bias_check", "citations"],
}

_DEFAULT_BIAS_CHECK = (
    "Checked against Article 19 free-expression protections and non-discrimination "
    "safeguards; flagged only on concrete textual evidence."
)

_STRICT_SUFFIX = (
    "\n\nIMPORTANT: Output MUST be a single valid JSON object matching the schema "
    "exactly. No markdown fences, no commentary."
)


# --- validation -----------------------------------------------------------
def validate_analysis(raw: dict, text: str) -> Optional[dict]:
    """Enforce allowlist, exact-substring highlights, no overlaps, length caps.
    Returns None when there is nothing usable (triggers retry / fallback)."""
    if not isinstance(raw, dict):
        return None
    lower = text.lower()

    techniques = [t for t in raw.get("techniques", []) if t in ALLOWED_TECHNIQUES]
    techniques = list(dict.fromkeys(techniques))

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
        phrase = str(h.get("phrase") or h.get("text") or h.get("quote") or "").strip()
        if not phrase:
            continue
        idx = lower.find(phrase.lower())
        if idx == -1:
            continue
        span = (idx, idx + len(phrase))
        if any(span[0] < e and s < span[1] for s, e in used_spans):
            continue
        used_spans.append(span)
        htype = str(h.get("type", "")).strip() or "emotional_manipulation"
        label = str(h.get("label", "")).strip() or TECHNIQUE_LABELS.get(
            htype, htype.replace("_", " ").title()
        )
        highlights.append({"phrase": text[idx: idx + len(phrase)], "type": htype, "label": label})

    bias_check = str(raw.get("bias_check", "")).strip()[:300] or _DEFAULT_BIAS_CHECK
    allow = set(LEGAL_SOURCE_URLS)
    citations = [u for u in raw.get("citations", []) if isinstance(u, str) and u in allow]
    citations = list(dict.fromkeys(citations))[:5]

    if not techniques and not highlights and not explanation:
        return None
    return {
        "techniques": techniques,
        "emotional_triggers": triggers,
        "explanation": explanation,
        "recommendation": recommendation,
        "severity": severity,
        "highlights": highlights,
        "bias_check": bias_check,
        "citations": citations,
    }


# --- local fallback -------------------------------------------------------
_HEURISTICS = {
    "false_urgency": ["before it", "act now", "midnight", "by monday", "running out", "last chance", "don't wait", "act before"],
    "fear_amplification": ["destroy", "lose everything", "collapse", "disaster", "danger", "terrify", "catastroph", "doom", "ruin everything"],
    "us_vs_them": ["us against them", "those people", "our side", "their side", "wake up", "elites", "they don't want you"],
    "scapegoating": ["blame", "fault", "because of them", "the reason", "responsible for"],
    "dehumanizing_language": ["vermin", "animals", "infest", "parasite", "swarm", "subhuman", "filth"],
    "ad_hominem": ["idiot", "fool", "stupid", "liar", "sheep", "brainless"],
    "emotional_manipulation": ["share this", "they don't want you", "hiding the truth", "stay angry", "open your eyes", "screenshot this", "real parent"],
}

_TRIGGER_WORDS = {
    "fear": ["destroy", "lose", "danger", "afraid", "collapse", "forever"],
    "anger": ["elites", "blame", "liar", "angry"],
    "urgency": ["now", "before", "midnight", "monday", "immediately"],
    "belonging": ["us", "our values", "who we are", "community"],
}


def local_fallback_analysis(text: str) -> dict:
    """Deterministic heuristic analysis used when the LLM is unavailable."""
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
    n = len(techniques)
    triggers = [name for name, words in _TRIGGER_WORDS.items() if any(w in lower for w in words)]
    severity = "high" if n >= 3 else "medium" if n == 2 else "low"
    return {
        "techniques": techniques[:4] or ["emotional_manipulation"],
        "emotional_triggers": triggers[:4] or ["emotional reaction"],
        "explanation": (
            "This post leans on emotionally charged language and framing that "
            "pushes a strong reaction rather than inviting reflection."
        ),
        "recommendation": "Take a moment before sharing and check whether the claim holds up calmly.",
        "severity": severity,
        "highlights": highlights[:6],
        "bias_check": "Heuristic check (LLM unavailable); flags only explicit manipulative cues, free expression preserved.",
        "citations": [],
        "source": "local_fallback",
    }


def _empty_analysis() -> dict:
    return {
        "techniques": [], "emotional_triggers": [], "explanation": "",
        "recommendation": "", "severity": "low", "highlights": [],
        "bias_check": _DEFAULT_BIAS_CHECK, "citations": [], "source": "empty",
    }


# --- analysis (the explainer) ---------------------------------------------
def analyze(text: str, kind: str = "manipulation") -> dict:
    """Run the hate OR manipulation analysis prompt; never raises for normal input."""
    if not text or not text.strip():
        return _empty_analysis()
    template = HATE_ANALYSIS_PROMPT if kind == "hate" else MANIPULATION_ANALYSIS_PROMPT

    raw = complete_json(ANALYSIS_SYSTEM_INSTRUCTION, template.format(text=text), schema=ANALYSIS_SCHEMA)
    analysis = validate_analysis(raw, text) if raw else None
    if analysis is None:
        raw = complete_json(
            ANALYSIS_SYSTEM_INSTRUCTION, template.format(text=text) + _STRICT_SUFFIX, schema=ANALYSIS_SCHEMA
        )
        analysis = validate_analysis(raw, text) if raw else None
    if analysis is None:
        analysis = local_fallback_analysis(text)
    else:
        analysis["source"] = "llm"
    analysis["kind"] = kind
    return analysis


# --- verifier (the judge) -------------------------------------------------
def verify(text: str, analysis: dict, kind: str) -> dict:
    """Second-pass LLM judge. Returns {relevant, reason, checked}.

    Fails OPEN: if the verifier can't run, relevant=True (keep the flag).
    """
    payload = json.dumps(
        {k: analysis.get(k) for k in ("techniques", "explanation", "severity", "bias_check", "citations")},
        ensure_ascii=False,
    )
    # The configured verifier model id is Gemini-specific; only pass it when the
    # verifier provider is Gemini (otherwise use the provider's default model).
    vmodel = VERIFIER_MODEL if VERIFIER_PROVIDER == "gemini" else None
    raw = complete_json(
        VERIFIER_SYSTEM_INSTRUCTION,
        VERIFIER_PROMPT.format(kind=kind, text=text, analysis=payload),
        provider=VERIFIER_PROVIDER,
        model=vmodel or None,
        temperature=0.0,  # deterministic verdict
    )
    if not isinstance(raw, dict) or "relevant" not in raw:
        return {"relevant": True, "reason": "verifier unavailable", "checked": False}
    return {
        "relevant": bool(raw.get("relevant")),
        "reason": str(raw.get("reason", "")).strip()[:200],
        "checked": True,
    }


# --- rephrase (live compose-assist) ---------------------------------------
def rephrase(text: str) -> str:
    """Rewrite a draft to remove manipulation/hate while keeping the author's
    viewpoint. Returns the original text on failure (never raises, never censors)."""
    if not text or not text.strip():
        return text
    raw = complete_json(REPHRASE_SYSTEM_INSTRUCTION, REPHRASE_PROMPT.format(text=text))
    if isinstance(raw, dict):
        out = str(raw.get("rephrased") or "").strip()
        if out:
            return out
    return text


# Backwards-compatible alias for the /analyze endpoint.
def detect_and_analyze(text: str) -> dict:
    return analyze(text, "manipulation")
