"""Punctuation restoration placeholder.

TODO: Replace with transformer-based punctuation restoration.
"""
from __future__ import annotations

from loguru import logger


def add_punctuation(text: str, language: str) -> str:
    """Add basic punctuation."""
    logger.debug("Adding punctuation for language {}", language)
    return text if text.endswith(".") else f"{text}."
