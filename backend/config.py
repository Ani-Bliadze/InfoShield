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
CACHE_VERSION = 4

# --- Hate classifier (multilingual) ---------------------------------------
# XLM-T multilingual offensive/hate detector (binary). Falls back to the proven
# English model if the multilingual download is unavailable.
PRIMARY_MODEL = "Andrazp/multilingual-hate-speech-robacofi"
FALLBACK_MODEL = "cardiffnlp/twitter-roberta-base-hate-latest"

FLAG_THRESHOLD = 0.40   # tuned for the XLM-T head (benign ~0.00, hate ~0.47-0.89)
HIGH_CONFIDENCE = 0.80
MAX_TOKENS = 512  # truncation ceiling for the classifier

# --- Manipulation classifier (multilingual) -------------------------------
# Multilingual mBART persuasion-technique detector (SemEval taxonomy, multi-label).
# The manipulation score is the strongest *concrete technique* probability
# (structural taxonomy nodes are excluded -- see manip_classifier). Falls back to
# the English propaganda model if unavailable.
MANIP_MODEL = "nishan-chatterjee/multilingual-persuasion-detection-from-text"
MANIP_FALLBACK_MODEL = "synapti/nci-social-classifier-v3"

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
# at/above this. The detector is tuned for RECALL because the verifier LLM removes
# the resulting false positives -- detector finds candidates, verifier confirms.
# Tuned for the mBART persuasion head (benign <=~0.46, manipulation >=~0.59).
MANIP_THRESHOLD = float(os.getenv("INFOSHIELD_MANIP_THRESHOLD", "0.50"))

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
# LLM PROMPTS  -- research-grounded, rights-preserving, JSON-only output.
# {text} = the post; {kind}/{analysis} = filled for the verifier only.
# Analysis/verifier/rephrase prompts go through str.format(): literal JSON braces
# are doubled {{ }}; only {text}/{kind}/{analysis} stay single. The SYSTEM strings
# are used directly (never .format()-ed), so their braces are literal.
# ===========================================================================

# Official human-rights / media-literacy sources the analysis may cite (allowlist
# only -- prevents hallucinated links).
LEGAL_SOURCE_URLS = [
    "https://treaties.un.org/doc/Treaties/1976/03/19760323%2006-17%20AM/Ch_IV_04.pdf",
    "https://www.ohchr.org/en/documents/general-comments-and-recommendations/general-comment-no34-article-19-freedoms-opinion-and",
    "https://www.ohchr.org/en/documents/outcome-documents/rabat-plan-action",
    "https://www.ohchr.org/en/documents/tools-and-resources/one-pager-incitement-hatred-rabat-threshold-test",
    "https://www.un.org/en/hate-speech/un-strategy-and-plan-of-action-on-hate-speech",
    "https://www.unesco.org/en/media-information-literacy",
    "https://www.unesco.org/en/articles/guidelines-governance-digital-platforms",
    "https://www.unesco.org/en/social-media4peace",
    "https://digitallibrary.un.org/record/3987886",
]

LEGAL_SOURCE_URLS_TEXT = "\n".join(f"- {url}" for url in LEGAL_SOURCE_URLS)

COMMON_JSON_RULES = (
    "Output EXACTLY one valid JSON object using double quotes for every key and string. "
    "No markdown, no code fences, no comments, no trailing commas, and no extra text before or after the JSON. "
    "Use exactly these keys and no others: "
    "{\"techniques\": [\"...\"], \"emotional_triggers\": [\"...\"], \"explanation\": \"...\", "
    "\"recommendation\": \"...\", \"severity\": \"low|medium|high\", "
    "\"highlights\": [{\"phrase\": \"...\", \"type\": \"...\", \"label\": \"...\"}], "
    "\"bias_check\": \"...\", \"citations\": [\"https://...\"]}. "
    "The arrays may be empty, but the keys must always be present. "
    "Every value in techniques must be one of the allowed technique ids. "
    "Every highlight.phrase must be copied VERBATIM from the post text. "
    "Keep explanation under 400 characters and recommendation to one calm sentence. "
    "bias_check must be a neutral sentence explaining how you checked the text against free-expression protections and non-discrimination safeguards. "
    "citations must contain 2 to 5 exact URLs, chosen ONLY from this allowlist, and ONLY if they are genuinely relevant to your reasoning:\n"
    f"{LEGAL_SOURCE_URLS_TEXT}\n"
    "If the content is protected or benign, cite the speech-protective sources you relied on."
)

# Shared system instruction for the ANALYSIS pass (hate + manipulation).
ANALYSIS_SYSTEM_INSTRUCTION = f"""
You are an expert analyst of media literacy, international human rights law, and algorithmic fairness.

Start from a speech-protective baseline. The right to freedom of opinion and expression is the default rule. Do not label content as hate speech or manipulation merely because it is offensive, emotional, partisan, sarcastic, unconventional, oppositional, or unpopular.

Apply these safeguards in every case:
- Protect political dissent, criticism of governments, parties, leaders, public institutions, religions as belief systems, ideologies, or public policies.
- Protect satire, humor, artistic expression, quotation, counterspeech, reporting, academic discussion, and historical or religious commentary unless the post itself clearly endorses hatred or coercive manipulation.
- Do not discriminate against minority dialects, colloquialisms, code-switching, transliteration, reclaimed language, disability-related speech patterns, youth slang, or culturally specific vernacular.
- Never infer hateful intent or manipulative intent from spelling, grammar, identity, nationality, religion, ethnicity, or language variety alone.
- If the evidence is mixed or ambiguous, prefer the less restrictive answer: empty techniques and severity "low".

For hate analysis, use the Rabat six-part threshold as a HIGH threshold for incitement: context, speaker, intent, content/form, extent, and likelihood including imminence. Negligence or mere offensiveness is not enough. Do not make legal conclusions; produce an educational assessment grounded in these standards.

For manipulation analysis, treat manipulation as a media-literacy judgment, not a criminal or legal accusation. Do not equate ordinary persuasion, activism, campaigning, moral argument, religious preaching, personal testimony, or emotional storytelling with manipulation unless the text itself clearly uses one or more of the allowed techniques in a way that pressures, dehumanizes, scapegoats, or polarizes.

{COMMON_JSON_RULES}
""".strip()
GEMINI_SYSTEM_INSTRUCTION = ANALYSIS_SYSTEM_INSTRUCTION  # back-compat alias

# ---- (3) HATE-SPEECH analysis prompt -- used when the HATE model flags --------
HATE_ANALYSIS_PROMPT = """
A local classifier flagged the post below as likely HATE SPEECH. Re-check the text carefully using international human rights standards that strongly protect freedom of expression.

Only identify hate-related techniques when the post itself clearly targets a protected group or a person as a proxy for a protected group through identity-based degradation, dehumanization, scapegoating, exclusion, or advocacy of discrimination, hostility, or violence. Use the Rabat threshold factors to calibrate severity: context, speaker, intent, content/form, extent, and likelihood/imminence.

Do NOT flag as hate merely because the text:
- expresses a political opinion, policy preference, protest slogan, or criticism of a state, government, party, movement, or religion as a doctrine;
- contains profanity, ridicule, satire, exaggeration, a quote, reportage, or counterspeech;
- uses minority dialect, cultural vernacular, reclaimed language, slang, code-switching, transliteration, or imperfect grammar;
- insults a specific individual without targeting a protected identity group.

Severity guide:
- low = protected, ambiguous, quoted, satirical, reported, counterspeech, or otherwise not a genuine identity-based attack.
- medium = clear identity-based hostility or degrading language, but incitement to discrimination, hostility, or violence is not strongly established.
- high = explicit or strongly implied advocacy or encouragement of discrimination, hostility, or violence, especially where Rabat factors show intent, directness, reach, and likelihood of harm.

Field meanings:
- techniques: array using ONLY these ids that truly apply: dehumanizing_language, identity_targeting, scapegoating, us_vs_them, fear_amplification, ad_hominem, false_urgency, emotional_manipulation.
- emotional_triggers: short phrases naming the emotions or social pressures actually used (e.g. fear, disgust, humiliation, anger, social exclusion, threat).
- explanation: concise neutral explanation of HOW the wording works. Do not call the author evil, criminal, extremist, or unlawful.
- recommendation: calm, non-judgmental reading advice for the audience.
- severity: low, medium, or high.
- highlights: array of objects {{"phrase": "...", "type": "...", "label": "..."}} where phrase is copied VERBATIM from the post, type is one allowed technique id, and label is a short human-readable label.
- bias_check: one neutral sentence stating that you checked the text against Article 19 free-expression protections, Rabat's high threshold for incitement, and non-discrimination safeguards for satire, quotation, counterspeech, and minority vernacular.
- citations: 2 to 5 exact allowlisted URLs supporting your reasoning. Use speech-protective sources when the text does NOT clearly cross the threshold.

Important decision rule: if the text is ordinary opinion, satire, banter, a life update, factual reporting, criticism of power, or otherwise does NOT genuinely attack or dehumanize a protected group, then return techniques as [], highlights as [], severity as "low", and explain briefly why the expression remains protected.

POST TEXT:
\"\"\"
{text}
\"\"\"
""".strip()

# ---- (4) MANIPULATION analysis prompt -- used when the MANIPULATION model flags
MANIPULATION_ANALYSIS_PROMPT = """
A local classifier flagged the post below as likely MANIPULATION / propaganda. Re-check the text as an educational media-literacy task while preserving freedom of expression.

This is NOT a legal judgment and NOT a fact-check. Judge only whether the wording itself clearly uses one or more of the allowed narrative techniques to pressure, polarize, scapegoat, dehumanize, or emotionally steer the reader.

Do NOT label as manipulation merely because the text:
- expresses a strong opinion, campaign message, activism, moral appeal, religious view, or political dissent;
- is emotional, humorous, sarcastic, poetic, speculative, or personal;
- comes from a marginalized community, uses a minority dialect or vernacular, or reflects translation artifacts;
- makes a controversial claim without, by itself, using a manipulative technique from the allowed list.

Treat the following as stronger evidence of manipulation only when clearly present in the actual wording: fear escalation without grounding, scapegoating, identity-based blame, us-versus-them framing, dehumanization, false urgency, ad hominem distraction, or emotionally coercive framing. If those signals are weak, speculative, or explainable as normal advocacy, return empty techniques and severity "low".

Severity guide:
- low = ordinary persuasion, opinion, advocacy, satire, or unclear evidence of manipulation.
- medium = one or more concrete techniques are present, but the pressure or polarization is limited.
- high = multiple explicit techniques used in a strong, coordinated, or highly coercive way, especially where identity-based blame or dehumanization sharply increases risk.

Field meanings:
- techniques: array using ONLY these ids that truly apply: fear_amplification, scapegoating, us_vs_them, dehumanizing_language, false_urgency, emotional_manipulation, identity_targeting, ad_hominem.
- emotional_triggers: short phrases naming the emotions or social pressures actually used.
- explanation: concise neutral explanation of HOW the wording tries to influence the reader. Focus on rhetoric, not truth adjudication.
- recommendation: calm, non-judgmental advice encouraging reflection or verification before reacting or sharing.
- severity: low, medium, or high.
- highlights: array of objects {{"phrase": "...", "type": "...", "label": "..."}} where phrase is copied VERBATIM from the post, type is one allowed technique id, and label is a short human-readable label.
- bias_check: one neutral sentence stating that you checked for false positives against Article 19 protections, satire, ordinary advocacy, cultural and linguistic nuance, and non-discrimination.
- citations: 2 to 5 exact allowlisted URLs supporting your reasoning. Use media-literacy and freedom-of-expression sources that actually match the decision.

Important decision rule: if the text is a joke, hot take, ordinary advocacy, personal opinion, factual statement, or emotional expression without clear manipulative technique, return techniques as [], highlights as [], severity as "low", and explain briefly why the expression should not be over-classified.

POST TEXT:
\"\"\"
{text}
\"\"\"
""".strip()

# ---- (2) VERIFIER prompt -- second-pass judge that overturns false positives --
VERIFIER_SYSTEM_INSTRUCTION = (
    "You are a strict, fair reviewer of automated content analysis. You judge ONLY "
    "whether an analysis accurately and relevantly describes the given post while "
    "respecting freedom of expression and non-discrimination. You are not political. "
    "Respond ONLY with valid JSON, no markdown."
)
VERIFIER_PROMPT = """
A post was automatically flagged as {kind} and the ANALYSIS below was produced.

Decide whether that analysis is ACCURATE and RELEVANT to the post.

Be STRICT and speech-protective. Mark relevant=false if the analysis overreaches, ignores Article 19 protections, ignores the Rabat high threshold where relevant, relies on stereotypes, mistakes dialect or vernacular for risk, treats satire or quotation as endorsement, or labels ordinary opinion, activism, reporting, humor, criticism of power, or a factual statement as hate/manipulation without clear textual evidence.

For hate cases, reject the analysis unless the post genuinely shows identity-based degradation, dehumanization, scapegoating, or advocacy/incitement. For manipulation cases, reject it unless the post genuinely uses concrete rhetorical techniques from the allowed list rather than ordinary persuasion.

You may also mark relevant=false if highlights are not verbatim, techniques are unsupported by the text, bias_check is inconsistent with the post, or citations are irrelevant or obviously invented.

Return JSON only: {{"relevant": true|false, "reason": "one short sentence"}}.

POST TEXT:
\"\"\"
{text}
\"\"\"

ANALYSIS (JSON):
{analysis}
""".strip()

# ---- (5) REPHRASE prompt -- live compose-assist: rewrite the user's own draft --
REPHRASE_SYSTEM_INSTRUCTION = (
    "You help people express their own point respectfully. You preserve the author's "
    "viewpoint, opinion, and legitimate criticism; you never censor, never flip the "
    "stance, and never add new claims. You only remove manipulative or hateful framing. "
    "Respond ONLY with valid JSON, no markdown."
)
REPHRASE_PROMPT = """
Rewrite the social-media post below so it makes the SAME point in a respectful, non-manipulative way.

Rules:
- Keep the author's core message, opinion, and any legitimate criticism of governments, institutions, policies, or ideas.
- Remove only manipulative or hateful framing: fear-mongering, false urgency, us-versus-them framing, scapegoating, dehumanizing or identity-based attacks, and ad hominem.
- Keep it natural, in the SAME language as the original, and similar length. Do not censor the viewpoint, do not moralize, do not add disclaimers, and do not invent facts.
- If the post is already respectful, return it essentially unchanged.

Return JSON only: {{"rephrased": "..."}}.

POST TEXT:
\"\"\"
{text}
\"\"\"
""".strip()
