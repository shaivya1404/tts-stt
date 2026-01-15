"""Audio preprocessing placeholder for the STT pipeline."""
from __future__ import annotations

from typing import Tuple

from loguru import logger


def preprocess(audio_bytes: bytes) -> Tuple[bytes, float]:
    """Return lightly processed audio and a synthetic duration estimate."""
    duration_seconds = max(len(audio_bytes) / (16000 * 2), 0.5)
    logger.debug("Preprocessing audio (%d bytes) => %.2f seconds", len(audio_bytes), duration_seconds)
    return audio_bytes, duration_seconds
