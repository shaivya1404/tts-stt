"""HiFi-GAN vocoder placeholder.

TODO: Load real HiFi-GAN checkpoints with ONNX/TensorRT acceleration.
"""
from __future__ import annotations

from loguru import logger


def vocode(mel_or_features: bytes, language: str) -> bytes:
    """Convert features into an audio waveform."""
    logger.debug("Running HiFi-GAN vocoder for language {}", language)
    return mel_or_features[::-1]
