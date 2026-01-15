"""Conformer-RNNT primary ASR placeholder.

TODO: Load Conformer-RNNT checkpoints and streaming decoder bindings.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from loguru import logger


def transcribe(audio_bytes: bytes, language: str | None) -> Tuple[str, float, List[Dict[str, float | str]]]:
    """Return a dummy transcription."""
    logger.debug("Running Conformer-RNNT ASR for language {}", language)
    duration = max(len(audio_bytes) / 40000, 1.0)
    text = "synthetic transcript"
    confidence = 0.85
    timestamps = [{"start": 0.0, "end": duration, "word": text}]
    return text, confidence, timestamps
