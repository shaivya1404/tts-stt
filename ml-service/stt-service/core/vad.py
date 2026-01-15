"""Voice activity detection placeholder.

TODO: Integrate WebRTC VAD / neural VAD for frame-level segmentation.
"""
from __future__ import annotations

from typing import List, Tuple

from loguru import logger


def detect_speech_segments(audio_bytes: bytes) -> List[Tuple[float, float]]:
    """Return dummy VAD segments."""
    logger.debug("Running VAD on {} bytes", len(audio_bytes))
    duration_seconds = max(len(audio_bytes) / 32000, 1.0)
    return [(0.0, duration_seconds)]
