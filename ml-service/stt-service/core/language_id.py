"""Language identification placeholder for the STT pipeline."""
from __future__ import annotations

from loguru import logger


LANGUAGE_FALLBACK = "en-IN"


def detect_language(audio_bytes: bytes, hint: str | None) -> str:
    """Return the hint when present, otherwise emit a deterministic pseudo prediction."""
    if hint:
        logger.debug("Using provided language hint: %s", hint)
        return hint

    fingerprint = len(audio_bytes) % 4
    prediction = {
        0: "en-IN",
        1: "hi-IN",
        2: "ta-IN",
        3: "en-US",
    }.get(fingerprint, LANGUAGE_FALLBACK)
    logger.debug("Detected language %s (fingerprint=%s)", prediction, fingerprint)
    return prediction
