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

# --- Classifier -----------------------------------------------------------
PRIMARY_MODEL = "cardiffnlp/twitter-roberta-base-hate-latest"
FALLBACK_MODEL = "Hate-speech-CNERG/dehatebert-mono-english"

FLAG_THRESHOLD = 0.60
HIGH_CONFIDENCE = 0.80
MAX_TOKENS = 512  # truncation ceiling for the classifier

# Probes used at startup to catch inverted label maps. Each must classify in
# the expected direction or the loader raises loudly.
SANITY_PROBES = [
    ("I love spending the afternoon reading in the park.", False),
    ("Have a wonderful day, everyone!", False),
    ("Those people are vermin and should be wiped out.", True),
]

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

GEMINI_SYSTEM_INSTRUCTION = (
    "You are an expert in media literacy and democratic discourse. You analyze "
    "text for manipulation techniques in a neutral, educational way -- helping "
    "citizens understand HOW content tries to influence them, not whether to "
    "agree with it. You never make political judgments, never accuse the author, "
    "and never use alarmist language. Respond ONLY with valid JSON, no markdown, "
    "no preamble."
)
