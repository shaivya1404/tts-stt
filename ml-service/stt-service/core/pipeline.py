"""Modular STT pipeline placeholder.

TODO: Swap in production ASR, denoising, and LM components.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from loguru import logger
from pydantic import BaseModel, Field

from common.config import Settings

from .aec import apply_aec
from .asr_conformer_rnnt import transcribe as primary_transcribe
from .asr_whisper_fallback import transcribe as fallback_transcribe
from .audio_preprocess import preprocess
from .itn import apply_itn
from .language_id import detect_language
from .language_model import refine_transcript
from .punctuation import add_punctuation
from .quality_scoring import score_quality
from .rnnoise_wrapper import denoise
from .truecasing import apply_truecase
from .vad import detect_speech_segments


class SttResult(BaseModel):
    """Structured result returned by the STT pipeline."""

    text: str
    language: str
    confidence: float
    timestamps: List[Dict[str, float | str]]
    meta: Dict[str, Any] = Field(default_factory=dict)
    modelUsed: str | None = None


class STTPipeline:
    """STT inference pipeline orchestrator."""

    def __init__(self, settings: Settings, model_name: str = "conformer_rnnt_indic", model_version: str = "v1") -> None:
        self.settings = settings
        self.model_name = model_name
        self.model_version = model_version
        self.logger = logger.bind(pipeline="stt")

    def _maybe_run_fallback(
        self,
        audio_bytes: bytes,
        language: str,
        primary_conf: float,
    ) -> Optional[Tuple[str, float, List[Dict[str, float | str]], str]]:
        if primary_conf >= 0.7:
            return None
        return fallback_transcribe(audio_bytes, language)

    def transcribe(self, audio_bytes: bytes, language_hint: str | None = None) -> SttResult:
        self.logger.info("Starting STT transcription for {} bytes", len(audio_bytes))
        processed_audio, duration_seconds = preprocess(audio_bytes)
        denoised_audio = denoise(processed_audio)
        echo_free_audio = apply_aec(denoised_audio)
        segments = detect_speech_segments(echo_free_audio, duration_seconds)
        language = detect_language(echo_free_audio, language_hint)

        primary_text, primary_conf, primary_timestamps, primary_model = primary_transcribe(echo_free_audio, language)
        fallback_result = self._maybe_run_fallback(echo_free_audio, language, primary_conf)

        text = primary_text
        confidence = primary_conf
        timestamps = primary_timestamps
        model_used = primary_model
        used_fallback = False
        fallback_model_name = fallback_result[3] if fallback_result else None

        if fallback_result and fallback_result[1] > primary_conf:
            text, confidence, timestamps, model_used = fallback_result
            used_fallback = True

        refined = refine_transcript(text, language)
        punctuated = add_punctuation(refined, language)
        truecased = apply_truecase(punctuated, language)
        normalized = apply_itn(truecased, language)
        quality_score = score_quality(normalized, confidence)

        meta = {
            "duration_seconds": duration_seconds,
            "segments": segments,
            "quality_score": quality_score,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "used_fallback": used_fallback,
            "language_hint": language_hint,
            "primary_model": primary_model,
            "fallback_model": fallback_model_name,
        }

        self.logger.info(
            "Finished STT transcription with confidence {:.2f} using model {}",
            confidence,
            model_used,
        )

        return SttResult(
            text=normalized,
            language=language,
            confidence=confidence,
            timestamps=timestamps,
            meta=meta,
            modelUsed=model_used,
        )
