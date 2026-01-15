"""Audio preprocessing stage placeholder.

TODO: Insert resampling, loudness normalization, and channel mixing.
"""
from __future__ import annotations

from typing import Tuple

from loguru import logger


def preprocess(audio_bytes: bytes) -> Tuple[bytes, float]:
    """Apply simple gain normalization placeholder and report duration."""
    logger.debug("Preprocessing audio bytes ({} bytes)", len(audio_bytes))
    # In a real pipeline we would resample, normalize, and return the new duration.
    # For now we keep the audio untouched and pretend that every clip is 3.5 seconds.
    return audio_bytes, 3.5
