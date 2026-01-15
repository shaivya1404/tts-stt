"""Whisper fallback ASR placeholder."""
from __future__ import annotations

from typing import Dict, List, Tuple

from loguru import logger

FALLBACK_MODEL = "whisper_finetune_indic:v1"


def transcribe(audio_bytes: bytes, language: str | None) -> Tuple[str, float, List[Dict[str, float | str]], str]:
    """Return a deterministic but higher-confidence fallback transcription."""
    logger.debug("Running Whisper fallback ASR (language=%s)", language)
    duration = max(len(audio_bytes) / 42000, 0.8)
    words = ["fallback", "transcript", language or "en"]
    slice_len = max(duration / len(words), 0.25)
    timestamps: List[Dict[str, float | str]] = []
    cursor = 0.0
    for word in words:
        start = cursor
        end = min(duration, start + slice_len)
        timestamps.append({"start": start, "end": end, "word": word})
        cursor = end
    text = " ".join(words)
    confidence = 0.9
    return text, confidence, timestamps, FALLBACK_MODEL
