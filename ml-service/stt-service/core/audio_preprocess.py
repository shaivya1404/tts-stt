"""Audio preprocessing stage placeholder.

TODO: Insert resampling, loudness normalization, and channel mixing.
"""
from __future__ import annotations

from loguru import logger


def preprocess(audio_bytes: bytes) -> bytes:
    """Apply simple gain normalization placeholder."""
    logger.debug("Preprocessing audio bytes ({} bytes)", len(audio_bytes))
    return audio_bytes
