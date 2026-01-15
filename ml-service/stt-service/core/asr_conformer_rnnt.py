"""Conformer-RNNT primary ASR placeholder.

TODO: Load Conformer-RNNT checkpoints and streaming decoder bindings.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

from loguru import logger


MODEL_NAME = "conformer_rnnt_indic_v1"


def transcribe(audio_bytes: bytes, language: str | None) -> Tuple[str, float, List[Dict[str, float | str]], str]:
    """Return a dummy transcription."""
    logger.debug("Running Conformer-RNNT ASR for language {}", language or "und")
    duration = max(len(audio_bytes) / 40000.0, 0.75)
    words = ["synthetic", "transcript", language or "unknown"]
    text = " ".join(words)
    confidence = 0.68
    timestamps = [
        {"start": 0.0, "end": duration / 2, "word": words[0]},
        {"start": duration / 2, "end": duration, "word": " ".join(words[1:])},
    ]
    return text, confidence, timestamps, MODEL_NAME
