"""Grapheme to phoneme placeholder implementation.

TODO: Connect to actual G2P models per language/script.
"""
from __future__ import annotations

from loguru import logger


def text_to_phonemes(normalized_text: str, language: str) -> list[str]:
    """Convert normalized text into a sequence of pseudo-phonemes."""
    logger.debug("Converting text to phonemes for language {}", language)
    words = normalized_text.split()
    phonemes = [f"{word}-ph" for word in words]
    return phonemes
