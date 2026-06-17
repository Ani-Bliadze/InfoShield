# =============================================================================
# PRIVACY BY DESIGN -- InfoShield local manipulation classifier
# -----------------------------------------------------------------------------
# Content-only and author-agnostic, exactly like the hate classifier: the only
# input is the post text. All inference runs locally.
# =============================================================================
"""Local manipulation / propaganda detector (the manipulation GATE).

Mirrors classifier.py but for manipulation. The primary checkpoint is a
multi-label (sigmoid) propaganda-technique model -- the manipulation score is the
strongest single technique probability. The fallback is a binary propaganda model
(softmax over [not, propaganda]). Heavy ML imports are deferred.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Optional

from config import MANIP_FALLBACK_MODEL, MANIP_MODEL, MANIP_THRESHOLD, MAX_TOKENS

log = logging.getLogger("infoshield.manip")

_POS_SUBSTR = ("prop", "manip", "persuas", "label_")  # "label_n" => generic multi-label head
_NEG_TOKENS = {"no", "not", "non", "none", "clean", "neutral", "normal", "negative"}


class ManipulationClassifier:
    """Lazy, device-aware wrapper. Returns a manipulation probability in [0, 1]."""

    def __init__(self) -> None:
        self._tokenizer = None
        self._model = None
        self._multilabel = False
        self._pos_index: Optional[int] = None
        self._max_len = MAX_TOKENS
        self.model_name: Optional[str] = None
        self.device: str = "cpu"
        self.warmup_ms: Optional[float] = None
        self.loaded: bool = False

    def load(self) -> None:
        if self.loaded:
            return
        import torch  # deferred
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        last_err: Optional[Exception] = None
        for name in (MANIP_MODEL, MANIP_FALLBACK_MODEL):
            try:
                log.info("Loading manipulation model '%s' ...", name)
                self._tokenizer = AutoTokenizer.from_pretrained(name)
                self._model = AutoModelForSequenceClassification.from_pretrained(name)
                self._model.to(self.device)
                self._model.eval()
                self.model_name = name
                self._resolve_head()
                break
            except Exception as exc:  # noqa: BLE001 - try fallback
                log.warning("Failed to load '%s': %s", name, exc)
                last_err = exc
                self._model = None
        if self._model is None:
            raise RuntimeError(f"Could not load any manipulation model: {last_err}")

        self._warmup()
        self.loaded = True

    def _resolve_head(self) -> None:
        cfg = self._model.config
        n = getattr(cfg, "num_labels", 2) or 2
        problem = (getattr(cfg, "problem_type", "") or "").lower()
        # Respect the model's real context window (BERTweet is only 130 positions,
        # not 512) to avoid position-embedding index errors on long posts.
        mpe = getattr(cfg, "max_position_embeddings", MAX_TOKENS + 2) or (MAX_TOKENS + 2)
        self._max_len = min(MAX_TOKENS, max(16, mpe - 2))
        self._multilabel = problem == "multi_label_classification" or n > 2
        if self._multilabel:
            log.info("Manipulation head: multi-label (%d techniques), score = max sigmoid.", n)
            return
        # Binary: find the "propaganda/manipulation present" index.
        id2label = {int(k): str(v).lower() for k, v in cfg.id2label.items()}
        for idx, label in id2label.items():
            tokens = set(re.split(r"[\s_\-]+", label))
            is_pos = any(s in label for s in _POS_SUBSTR) and not (tokens & _NEG_TOKENS)
            if is_pos:
                self._pos_index = idx
                break
        if self._pos_index is None:
            self._pos_index = 1 if n == 2 else max(id2label)
        log.info("Manipulation head: binary, positive index %d (%s).",
                 self._pos_index, id2label)

    def _probability(self, text: str) -> tuple[float, bool]:
        import torch

        enc = self._tokenizer(text, return_tensors="pt", truncation=True, max_length=self._max_len)
        truncated = bool(enc["input_ids"].shape[1] >= self._max_len)
        enc = {k: v.to(self.device) for k, v in enc.items() if k in ("input_ids", "attention_mask")}
        with torch.no_grad():
            logits = self._model(**enc).logits[0]
            if self._multilabel:
                score = float(torch.sigmoid(logits).max().item())
            else:
                score = float(torch.softmax(logits, dim=-1)[self._pos_index].item())
        return score, truncated

    def classify(self, text: str) -> dict:
        if not text or not text.strip():
            return {"label": "CLEAR", "flagged": False, "confidence": 0.0,
                    "truncated": False, "model": self.model_name}
        if not self.loaded:
            self.load()
        prob, truncated = self._probability(text)
        flagged = prob >= MANIP_THRESHOLD
        return {
            "label": "MANIPULATION" if flagged else "CLEAR",
            "flagged": flagged,
            "confidence": round(prob, 4),
            "truncated": truncated,
            "model": self.model_name,
        }

    def _warmup(self) -> None:
        start = time.perf_counter()
        self._probability("This is a warmup inference for InfoShield.")
        self.warmup_ms = round((time.perf_counter() - start) * 1000, 1)
        log.info("Manipulation warmup on %s took ~%.1f ms", self.device, self.warmup_ms)


_manip: Optional[ManipulationClassifier] = None


def get_manip_classifier() -> ManipulationClassifier:
    global _manip
    if _manip is None:
        _manip = ManipulationClassifier()
    return _manip
