"""Text normalization placeholder for the TTS pipeline.

TODO: Wire up proper rule-based + ML text normalization stack.
"""
from __future__ import annotations

from loguru import logger


def normalize_text(text: str, language: str) -> str:
    """Normalize text using rule-based heuristics."""
    logger.debug("Normalizing text for language {}", language)
    normalized = " ".join(text.strip().split())
    return normalized
