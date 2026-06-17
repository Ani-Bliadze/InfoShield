"""Central configuration for the InfoShield backend.

Everything tunable lives here: model ids, thresholds, file paths, ports, the
technique allowlist, and the Gemini system instruction. No secrets are stored
here -- the Gemini key is read from the environment (.env).
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"

load_dotenv(BASE_DIR.parent / ".env")

# --- Networking -----------------------------------------------------------
HOST = os.getenv("INFOSHIELD_HOST", "127.0.0.1")
PORT = int(os.getenv("INFOSHIELD_PORT", "5050"))
# The Vite dev server that hosts the landing + social pages.
FRONTEND_ORIGIN = os.getenv("INFOSHIELD_FRONTEND", "http://localhost:5173")

# --- Files ----------------------------------------------------------------
POSTS_FILE = DATA_DIR / "posts.json"
CACHE_FILE = DATA_DIR / "cache.json"
ACTIVATION_FILE = DATA_DIR / "activation.json"

# Reset activation to default (disabled) on each backend start so every demo run
# begins at the landing page's ACTIVATE button. Set =0 to keep the saved target.
RESET_ACTIVATION_ON_START = os.getenv("INFOSHIELD_RESET_ACTIVATION", "1") == "1"

# Bump when the analysis pipeline/output shape changes so an old cache.json is
# auto-discarded and rebuilt (rather than serving stale results).
CACHE_VERSION = 2

# --- Hate classifier ------------------------------------------------------
PRIMARY_MODEL = "cardiffnlp/twitter-roberta-base-hate-latest"
FALLBACK_MODEL = "Hate-speech-CNERG/dehatebert-mono-english"

FLAG_THRESHOLD = 0.60
HIGH_CONFIDENCE = 0.80
MAX_TOKENS = 512  # truncation ceiling for the classifier

# --- Manipulation classifier ----------------------------------------------
# Local manipulation/propaganda detector. Same role as the hate model: it
# detects first (gate), then the LLM explains why. Multi-label (sigmoid) -- the
# manipulation score is the strongest single technique probability. Falls back
# to a binary propaganda model if the primary is unavailable.
MANIP_MODEL = "synapti/nci-social-classifier-v3"
MANIP_FALLBACK_MODEL = "IDA-SERICS/PropagandaDetection"

# Probes used at startup to catch inverted label maps. Each must classify in
# the expected direction or the loader raises loudly.
SANITY_PROBES = [
    ("I love spending the afternoon reading in the park.", False),
    ("Have a wonderful day, everyone!", False),
    ("Those people are vermin and should be wiped out.", True),
]

# --- LLM providers (analysis + verifier) ----------------------------------
# Analysis provider runs the educational explanation. Default: Gemini.
LLM_PROVIDER = os.getenv("INFOSHIELD_LLM_PROVIDER", "gemini").strip().lower()

# Second-pass verifier (LLM-as-judge that overturns false positives). Runs on the
# stronger Gemini Pro model by default; analysis runs on the faster Flash model.
VERIFIER_PROVIDER = os.getenv("INFOSHIELD_VERIFIER_PROVIDER", LLM_PROVIDER).strip().lower()
VERIFIER_MODEL = os.getenv("INFOSHIELD_VERIFIER_MODEL", "gemini-3.1-pro-preview").strip()

# A post is flagged for manipulation when the local manipulation model's score is
# at/above this. The detector is tuned for RECALL (low threshold) because the
# verifier LLM removes the resulting false positives -- detector finds candidates,
# verifier confirms. Re-tune on a labeled subset (docs/EVALUATION.md).
MANIP_THRESHOLD = float(os.getenv("INFOSHIELD_MANIP_THRESHOLD", "0.35"))

# --- Groq -----------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# --- Gemini ---------------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = "gemini-3.5-flash"

ALLOWED_TECHNIQUES = [
    "fear_amplification",
    "scapegoating",
    "us_vs_them",
    "dehumanizing_language",
    "false_urgency",
    "emotional_manipulation",
    "identity_targeting",
    "ad_hominem",
]

# Human-readable labels for technique chips and the insights widget.
TECHNIQUE_LABELS = {
    "fear_amplification": "Fear Amplification",
    "scapegoating": "Scapegoating",
    "us_vs_them": "Us vs. Them",
    "dehumanizing_language": "Dehumanizing Language",
    "false_urgency": "False Urgency",
    "emotional_manipulation": "Emotional Manipulation",
    "identity_targeting": "Identity Targeting",
    "ad_hominem": "Ad Hominem",
}

MAX_EXPLANATION_CHARS = 400

# ===========================================================================
# LLM PROMPTS  -- edit the text below to tune what each LLM writes.
# {text} = the post; {kind}/{analysis} = filled for the verifier only.
# ===========================================================================

# Shared system instruction for the ANALYSIS pass (hate + manipulation).
ANALYSIS_SYSTEM_INSTRUCTION = (
    "You are an expert in media literacy and democratic discourse. You analyze "
    "text in a neutral, educational way -- helping citizens understand HOW content "
    "tries to influence them, not whether to agree with it. You never make political "
    "judgments, never accuse the author, and never use alarmist language. Respond "
    "ONLY with valid JSON, no markdown, no preamble."
)
GEMINI_SYSTEM_INSTRUCTION = ANALYSIS_SYSTEM_INSTRUCTION  # back-compat alias

# ---- (3) HATE-SPEECH analysis prompt -- used when the HATE model flags --------
HATE_ANALYSIS_PROMPT = (
    "A local classifier flagged the post below as likely HATE SPEECH. Judge it on "
    "the actual words. If the post is ordinary -- a joke, personal opinion, hot take, "
    "life update, or factual statement -- and does NOT genuinely attack or dehumanize "
    "a group, return an EMPTY techniques array and severity \"low\". Otherwise explain, "
    "neutrally and educationally, HOW it works. Return a single JSON object with:\n"
    "- techniques: array using ONLY these ids that apply: dehumanizing_language, "
    "identity_targeting, scapegoating, us_vs_them, fear_amplification, ad_hominem, "
    "false_urgency, emotional_manipulation.\n"
    "- emotional_triggers: the emotional levers it leans on.\n"
    "- explanation: a concise neutral explanation of how the language targets or "
    "dehumanizes a group.\n"
    "- recommendation: a calm, non-judgmental suggestion for the reader.\n"
    "- severity: low, medium, or high.\n"
    "- highlights: array of objects {{\"phrase\", \"type\", \"label\"}}; phrase copied "
    "VERBATIM from the text; type is one of the technique ids above.\n\n"
    "POST TEXT:\n\"\"\"\n{text}\n\"\"\""
)

# ---- (4) MANIPULATION analysis prompt -- used when the MANIPULATION model flags
MANIPULATION_ANALYSIS_PROMPT = (
    "A local classifier flagged the post below as likely MANIPULATION / propaganda. "
    "Judge it on the actual words. If the post is ordinary -- a joke, personal opinion, "
    "hot take, life update, or factual statement -- and does NOT genuinely try to "
    "manipulate, return an EMPTY techniques array and severity \"low\". Otherwise "
    "explain, neutrally and educationally, HOW it tries to influence the reader. "
    "Return a single JSON object with:\n"
    "- techniques: array using ONLY these ids that apply: fear_amplification, "
    "scapegoating, us_vs_them, dehumanizing_language, false_urgency, "
    "emotional_manipulation, identity_targeting, ad_hominem.\n"
    "- emotional_triggers: the emotional levers it leans on.\n"
    "- explanation: a concise neutral explanation of HOW it tries to influence.\n"
    "- recommendation: a calm, non-judgmental suggestion before sharing.\n"
    "- severity: low, medium, or high.\n"
    "- highlights: array of objects {{\"phrase\", \"type\", \"label\"}}; phrase copied "
    "VERBATIM from the text; type is one of the technique ids above.\n\n"
    "POST TEXT:\n\"\"\"\n{text}\n\"\"\""
)

# ---- (2) VERIFIER prompt -- second-pass judge that overturns false positives --
VERIFIER_SYSTEM_INSTRUCTION = (
    "You are a strict, fair reviewer of automated content analysis. You judge ONLY "
    "whether an analysis accurately and relevantly describes the given post. You are "
    "not political. Respond ONLY with valid JSON, no markdown."
)
VERIFIER_PROMPT = (
    "A post was automatically flagged as {kind} and the ANALYSIS below was produced. "
    "Decide whether that analysis is ACCURATE and RELEVANT to the post -- i.e. the "
    "post genuinely exhibits what the analysis claims.\n"
    "Be STRICT. Mark relevant=false (a false positive) if the post is an ordinary "
    "personal opinion, joke, hot take, life update, or factual statement, even if a "
    "technique could be loosely argued. Mark relevant=true ONLY when the post clearly "
    "and genuinely shows {kind}.\n"
    "Return JSON: {{\"relevant\": true|false, \"reason\": \"one short sentence\"}}.\n\n"
    "POST TEXT:\n\"\"\"\n{text}\n\"\"\"\n\n"
    "ANALYSIS (JSON):\n{analysis}"
)
