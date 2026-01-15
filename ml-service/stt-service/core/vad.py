"""Voice activity detection placeholder.

TODO: Integrate WebRTC VAD / neural VAD for frame-level segmentation.
"""
from __future__ import annotations

from typing import List, Tuple

from loguru import logger


def detect_speech_segments(audio_bytes: bytes, duration_seconds: float = 3.5) -> List[Tuple[float, float]]:
    """Return dummy VAD segments covering the whole utterance."""
    logger.debug("Running VAD on {} bytes (duration≈{}s)", len(audio_bytes), duration_seconds)
    end_time = max(duration_seconds, 0.1)
    return [(0.0, end_time)]
