"""MOSNet quality estimation placeholder.

TODO: Connect MOSNet/UTMOS quality assessment for monitoring.
"""
from __future__ import annotations

from loguru import logger


def estimate_mos(waveform: bytes) -> float:
    """Return a pseudo MOS score for diagnostics."""
    score = 4.0 if waveform else 0.0
    logger.debug("Estimating MOS score: {}", score)
    return score
