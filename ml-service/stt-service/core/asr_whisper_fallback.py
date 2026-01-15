"""Whisper fallback ASR placeholder.

TODO: Integrate Whisper (or internal fallback) for multilingual robustness.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from loguru import logger


MODEL_NAME = "whisper_fallback_large_v1"


def transcribe(audio_bytes: bytes, language: str | None) -> Tuple[str, float, List[Dict[str, float | str]], str]:
    """Fallback transcription with lower latency expectations."""
    logger.debug("Running Whisper fallback for language {}", language or "und")
    duration = max(len(audio_bytes) / 45000.0, 0.6)
    words = ["fallback", "transcript", language or "unknown"]
    text = " ".join(words)
    confidence = 0.82
    timestamps = [
        {"start": 0.0, "end": duration, "word": text},
    ]
    return text, confidence, timestamps, MODEL_NAME
