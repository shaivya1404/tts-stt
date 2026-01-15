"""Speaker encoder placeholder.

TODO: Hook to d-vector/x-vector encoder for cloning and multi-speaker control.
"""
from __future__ import annotations

import os
from loguru import logger


def get_speaker_embedding(voice_id: str | None, audio_sample_path: str | None) -> bytes | None:
    """Return a pseudo speaker embedding if one can be derived."""
    if not voice_id and not audio_sample_path:
        logger.debug("No voice reference provided; using default speaker embedding")
        return None
    logger.debug(
        "Generating speaker embedding for voice_id={} sample={}",
        voice_id,
        audio_sample_path,
    )
    return os.urandom(64)
