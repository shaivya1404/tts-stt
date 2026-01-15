"""Conformer-RNNT primary ASR placeholder."""
from __future__ import annotations

from typing import Dict, List, Tuple

from loguru import logger

PRIMARY_MODEL = "conformer_rnnt_indic:v1"


def _build_timestamps(duration: float, words: List[str]) -> List[Dict[str, float | str]]:
    if not words:
        return [{"start": 0.0, "end": duration, "word": ""}]
    slice_len = max(duration / len(words), 0.25)
    cursor = 0.0
    segments: List[Dict[str, float | str]] = []
    for word in words:
        start = cursor
        end = min(duration, start + slice_len)
        segments.append({"start": start, "end": end, "word": word})
        cursor = end
    return segments


def transcribe(audio_bytes: bytes, language: str | None) -> Tuple[str, float, List[Dict[str, float | str]], str]:
    """Return a deterministic transcription stub for the Conformer RNNT model."""
    logger.debug("Running Conformer-RNNT primary ASR (language=%s)", language)
    duration = max(len(audio_bytes) / 40000, 1.0)
    tokens = ["hello", "from", language or "en", "pipeline"]
    timestamps = _build_timestamps(duration, tokens)
    text = " ".join(tokens)
    confidence = 0.82
    return text, confidence, timestamps, PRIMARY_MODEL
