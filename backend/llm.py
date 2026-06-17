"""Provider-agnostic JSON completion for InfoShield.

`complete_json(system, user, provider=None, model=None)` -> parsed dict (or None).
Provider defaults to `config.LLM_PROVIDER` ("groq" now, "gemini" later) but can be
overridden per call -- the verifier uses this to (later) run on a different/best
model than the analysis. Heavy SDK imports are deferred; missing key/SDK -> None
so callers fall back gracefully.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Optional

from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GROQ_API_KEY,
    GROQ_MODEL,
    LLM_PROVIDER,
)

log = logging.getLogger("infoshield.llm")

_clients: dict[str, object] = {}  # provider -> client (or None once tried & failed)
_tried: set[str] = set()


def _coerce_json(text: str) -> Optional[dict]:
    """Best-effort: parse a JSON object, tolerating stray markdown fences."""
    if not text:
        return None
    text = text.strip()
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


def _has_key(provider: str) -> bool:
    return bool(GEMINI_API_KEY) if provider == "gemini" else bool(GROQ_API_KEY)


def available(provider: Optional[str] = None) -> bool:
    """True if the (default or given) provider has a key configured."""
    return _has_key(provider or LLM_PROVIDER)


def _get_client(provider: str):
    if provider in _clients:
        return _clients[provider]
    _tried.add(provider)
    client = None
    try:
        if provider == "gemini":
            if GEMINI_API_KEY:
                from google import genai  # deferred

                client = genai.Client(api_key=GEMINI_API_KEY)
                log.info("Gemini client initialized.")
            else:
                log.warning("GEMINI_API_KEY not set -- gemini calls unavailable.")
        else:  # groq
            if GROQ_API_KEY:
                from groq import Groq  # deferred

                client = Groq(api_key=GROQ_API_KEY)
                log.info("Groq client initialized.")
            else:
                log.warning("GROQ_API_KEY not set -- groq calls unavailable.")
    except Exception as exc:  # noqa: BLE001
        log.warning("Could not initialize %s client: %s", provider, exc)
        client = None
    _clients[provider] = client
    return client


# --- completion -----------------------------------------------------------
def complete_json(
    system: str,
    user: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    schema: Optional[dict] = None,
    temperature: float = 0.2,
) -> Optional[dict]:
    """Return a parsed JSON object from the chosen provider, or None on failure.

    `schema` is only used by Gemini (structured output); Groq uses JSON-object
    mode and relies on the prompt + downstream validation.
    """
    provider = (provider or LLM_PROVIDER).lower()
    result = _complete_one(provider, system, user, model, schema, temperature)
    if result is not None:
        return result
    # Resilience: if the chosen provider fails (e.g. Gemini out of credits), fall
    # back to the other provider using its default model so the demo keeps working.
    other = "groq" if provider == "gemini" else "gemini"
    if _has_key(other):
        log.info("Provider '%s' failed; falling back to '%s'.", provider, other)
        return _complete_one(other, system, user, None, schema, temperature)
    return None


def _complete_one(provider, system, user, model, schema, temperature):
    client = _get_client(provider)
    if client is None:
        return None
    if provider == "gemini":
        return _gemini_complete(client, system, user, model or GEMINI_MODEL, schema, temperature)
    return _groq_complete(client, system, user, model or GROQ_MODEL, temperature)


def _groq_complete(client, system: str, user: str, model: str, temperature: float) -> Optional[dict]:
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=temperature,
        )
        return _coerce_json(resp.choices[0].message.content or "")
    except Exception as exc:  # noqa: BLE001
        log.warning("Groq call failed: %s", exc)
        return None


def _gemini_complete(client, system: str, user: str, model: str, schema: Optional[dict], temperature: float) -> Optional[dict]:
    try:
        from google.genai import types  # deferred

        cfg = types.GenerateContentConfig(
            system_instruction=system,
            response_mime_type="application/json",
            temperature=temperature,
        )
        if schema:
            cfg.response_schema = schema
        resp = client.models.generate_content(model=model, contents=user, config=cfg)
        return _coerce_json(getattr(resp, "text", "") or "")
    except Exception as exc:  # noqa: BLE001
        log.warning("Gemini call failed: %s", exc)
        return None
