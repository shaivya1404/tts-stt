"""Modular STT pipeline placeholder.

TODO: Swap in production ASR, denoising, and LM components.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from loguru import logger

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


@dataclass(slots=True)
class STTPipelineResult:
    text: str
    language: str
    confidence: float
    timestamps: List[Dict[str, float | str]]
    meta: Dict[str, Any] = field(default_factory=dict)


class STTPipeline:
    """STT inference pipeline orchestrator."""

    def __init__(self, settings: Settings, model_name: str = "conformer_rnnt_indic", model_version: str = "v1") -> None:
        self.settings = settings
        self.model_name = model_name
        self.model_version = model_version
        self.logger = logger.bind(pipeline="stt")

    def transcribe(self, audio_bytes: bytes, language_hint: str | None = None) -> STTPipelineResult:
        self.logger.info("Starting STT transcription for {} bytes", len(audio_bytes))
        preprocessed = preprocess(audio_bytes)
        denoised = denoise(preprocessed)
        echo_free = apply_aec(denoised)
        segments = detect_speech_segments(echo_free)
        segment_signature = " ".join([f"{start:.2f}-{end:.2f}" for start, end in segments])
        language = detect_language(segment_signature, language_hint)
        primary_text, primary_conf, primary_segments = primary_transcribe(echo_free, language)
        used_fallback = False
        if primary_conf < 0.75 or not primary_text:
            fallback_text, fallback_conf, fallback_segments = fallback_transcribe(echo_free, language)
            text = fallback_text
            confidence = fallback_conf
            timestamps = fallback_segments
            used_fallback = True
        else:
            text = primary_text
            confidence = primary_conf
            timestamps = primary_segments
        refined = refine_transcript(text, language)
        punctuated = add_punctuation(refined, language)
        truecased = apply_truecase(punctuated, language)
        normalized = apply_itn(truecased, language)
        quality_score = score_quality(normalized, confidence)
        meta = {
            "segments": segments,
            "quality_score": quality_score,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "used_fallback": used_fallback,
            "language_hint": language_hint,
        }
        self.logger.info("Finished STT transcription with confidence {:.2f}", confidence)
        return STTPipelineResult(
            text=normalized,
            language=language,
            confidence=confidence,
            timestamps=timestamps,
            meta=meta,
        )
