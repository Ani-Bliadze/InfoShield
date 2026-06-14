# =============================================================================
# PRIVACY BY DESIGN -- InfoShield local classifier
# -----------------------------------------------------------------------------
# This module classifies the *content* of a post and nothing else. It never
# receives, stores, or considers usernames, handles, display names, avatars,
# follower counts, or any author identity. Classification is content-only and
# author-agnostic by construction: the only input is a string of post text.
# All inference runs locally; no text leaves the machine from this module.
# =============================================================================
"""Local hate-speech / harmful-content classifier.

Heavy ML imports (torch, transformers) are deferred until the model is actually
loaded so the backend can start in cache-first mode without them installed.
"""
from __future__ import annotations

import logging
import time
from typing import Optional

from config import (
    FALLBACK_MODEL,
    FLAG_THRESHOLD,
    HIGH_CONFIDENCE,
    MAX_TOKENS,
    PRIMARY_MODEL,
    SANITY_PROBES,
)

log = logging.getLogger("infoshield.classifier")

# Resolving which output index is the "harmful" class is subtle: labels like
# "NOT-HATE" / "NON_HATE" contain the substring "hate", so naive substring
# matching inverts the map. We detect negation by TOKEN (split on space/_/-) and
# only then look for a hate-like substring.
_HATE_SUBSTR = ("hate", "toxic", "offensive", "abusive", "hateful")
_NEG_TOKENS = {"not", "non", "none", "neither", "normal", "neutral", "clean", "no", "ok", "negative"}


class HateClassifier:
    """Lazy, device-aware wrapper around a HF sequence-classification model."""

    def __init__(self) -> None:
        self._pipeline = None
        self._tokenizer = None
        self._model = None
        self._hate_index: Optional[int] = None
        self.model_name: Optional[str] = None
        self.device: str = "cpu"
        self.warmup_ms: Optional[float] = None
        self.loaded: bool = False

    # -- loading -----------------------------------------------------------
    def load(self) -> None:
        if self.loaded:
            return
        import torch  # deferred
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
        )

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        if self.device == "cpu":
            log.warning("CUDA not available -- running classifier on CPU (slower).")
        else:
            log.info("CUDA available -- running classifier on GPU.")

        last_err: Optional[Exception] = None
        for name in (PRIMARY_MODEL, FALLBACK_MODEL):
            try:
                log.info("Loading classifier '%s' ...", name)
                self._tokenizer = AutoTokenizer.from_pretrained(name)
                self._model = AutoModelForSequenceClassification.from_pretrained(name)
                self._model.to(self.device)
                self._model.eval()
                self.model_name = name
                self._resolve_hate_index()
                break
            except Exception as exc:  # noqa: BLE001 - try fallback
                log.warning("Failed to load '%s': %s", name, exc)
                last_err = exc
                self._model = None
        if self._model is None:
            raise RuntimeError(f"Could not load any classifier model: {last_err}")

        self._warmup()
        self._sanity_check()
        self.loaded = True

    def _resolve_hate_index(self) -> None:
        import re

        id2label = {int(k): v.lower() for k, v in self._model.config.id2label.items()}
        for idx, label in id2label.items():
            tokens = set(re.split(r"[\s_\-]+", label))
            is_negated = bool(tokens & _NEG_TOKENS)
            is_hate = any(h in label for h in _HATE_SUBSTR)
            if is_hate and not is_negated:  # e.g. "hate" yes, "not-hate" no
                self._hate_index = idx
                break
        if self._hate_index is None:
            # Binary models without descriptive labels: assume index 1 = positive.
            self._hate_index = 1 if len(id2label) == 2 else max(id2label)
        log.info("Resolved label map %s -> hate index %d", id2label, self._hate_index)

    # -- inference ---------------------------------------------------------
    def _hate_probability(self, text: str) -> tuple[float, bool, dict]:
        import torch

        enc = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=MAX_TOKENS,
            return_overflowing_tokens=False,
        )
        truncated = bool(enc["input_ids"].shape[1] >= MAX_TOKENS)
        enc = {k: v.to(self.device) for k, v in enc.items() if k in ("input_ids", "attention_mask")}
        with torch.no_grad():
            logits = self._model(**enc).logits[0]
            probs = torch.softmax(logits, dim=-1).cpu().tolist()
        id2label = self._model.config.id2label
        raw = {id2label[i]: round(float(p), 4) for i, p in enumerate(probs)}
        return float(probs[self._hate_index]), truncated, raw

    def classify(self, text: str) -> dict:
        """Return a content-only classification dict for `text`."""
        if not text or not text.strip():
            # Empty / whitespace -> NOT_HATE without a model call.
            return {
                "label": "NOT_HATE",
                "flagged": False,
                "confidence": 0.0,
                "high_confidence": False,
                "truncated": False,
                "raw_scores": {},
                "model": self.model_name,
            }
        if not self.loaded:
            self.load()
        prob, truncated, raw = self._hate_probability(text)
        flagged = prob >= FLAG_THRESHOLD
        return {
            "label": "HATE" if flagged else "NOT_HATE",
            "flagged": flagged,
            "confidence": round(prob, 4),
            "high_confidence": prob >= HIGH_CONFIDENCE,
            "truncated": truncated,
            "raw_scores": raw,
            "model": self.model_name,
        }

    # -- startup checks ----------------------------------------------------
    def _warmup(self) -> None:
        start = time.perf_counter()
        self._hate_probability("This is a warmup inference for InfoShield.")
        self.warmup_ms = round((time.perf_counter() - start) * 1000, 1)
        log.info("Warmup inference on %s took ~%.1f ms", self.device, self.warmup_ms)

    def _sanity_check(self) -> None:
        """Run label-mapping probes; fail loudly if the map looks inverted."""
        failures = []
        for text, expect_hate in SANITY_PROBES:
            prob, _, _ = self._hate_probability(text)
            got_hate = prob >= FLAG_THRESHOLD
            mark = "ok" if got_hate == expect_hate else "MISMATCH"
            log.info("Sanity probe (%s): expect_hate=%s prob=%.3f", mark, expect_hate, prob)
            if got_hate != expect_hate:
                failures.append((text, expect_hate, prob))
        if failures:
            raise RuntimeError(
                "Classifier label-mapping sanity check FAILED -- labels may be "
                f"inverted. Failures: {failures}"
            )
        log.info("Label-mapping sanity check passed.")


# Module-level singleton (lazy).
_classifier: Optional[HateClassifier] = None


def get_classifier() -> HateClassifier:
    global _classifier
    if _classifier is None:
        _classifier = HateClassifier()
    return _classifier
