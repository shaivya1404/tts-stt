"""Language identification for STT pipeline.

TODO: Replace with speech-based LID leveraging short utterance embeddings.
"""
from __future__ import annotations

from loguru import logger


def detect_language(text: str, hint: str | None) -> str:
    """Return a reasonable spoken language estimate."""
    if hint:
        logger.debug("Using STT language hint: {}", hint)
        return hint
    logger.debug("Inferring language from content signature length {}", len(text))
    return "en-US"
