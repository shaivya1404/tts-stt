"""RNNoise denoising placeholder.

TODO: Wire up RNNoise or neural denoiser bindings for real cleaning.
"""
from __future__ import annotations

from loguru import logger


def denoise(audio_bytes: bytes) -> bytes:
    """Apply placeholder RNNoise filtering."""
    logger.debug("Applying RNNoise denoiser")
    return audio_bytes
