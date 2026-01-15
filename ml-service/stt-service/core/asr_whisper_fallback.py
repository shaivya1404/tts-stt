"""Whisper fallback ASR placeholder.

TODO: Integrate Whisper (or internal fallback) for multilingual robustness.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from loguru import logger


def transcribe(audio_bytes: bytes, language: str | None) -> Tuple[str, float, List[Dict[str, float | str]]]:
    """Fallback transcription with lower latency expectations."""
    logger.debug("Running Whisper fallback for language {}", language)
    duration = max(len(audio_bytes) / 45000, 0.6)
    text = "fallback transcript"
    confidence = 0.7
    timestamps = [{"start": 0.0, "end": duration, "word": text}]
    return text, confidence, timestamps
