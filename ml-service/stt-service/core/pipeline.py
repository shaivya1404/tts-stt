"""Speech-to-text pipeline implementation skeleton."""
from __future__ import annotations

from typing import Any, Dict, List

from loguru import logger
from pydantic import BaseModel, Field

from common.config import Settings

from .aec import apply_aec
from .asr_conformer_rnnt import transcribe as conformer_transcribe
from .asr_whisper_fallback import transcribe as whisper_transcribe
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
    text: str
    language: str
    confidence: float
    timestamps: List[Dict[str, Any]]
    meta: Dict[str, Any] = Field(default_factory=dict)
    modelUsed: str | None = None


class STTPipeline:
    """Composable STT pipeline with placeholder components."""

    def __init__(self, settings: Settings, model_name: str = "conformer_rnnt_indic", model_version: str = "v1") -> None:
        self.settings = settings
        self.model_name = model_name
        self.model_version = model_version
        self.logger = logger.bind(component="stt_pipeline", model=model_name)

    def transcribe(self, audio_bytes: bytes, language_hint: str | None = None) -> SttResult:
        if not audio_bytes:
            raise ValueError("audio_bytes payload is empty")

        self.logger.info("Starting STT pipeline run (payload=%d bytes)", len(audio_bytes))
        preprocessed_audio, duration_seconds = preprocess(audio_bytes)
        denoised_audio = denoise(preprocessed_audio)
        echo_reduced_audio = apply_aec(denoised_audio)
        vad_segments = detect_speech_segments(echo_reduced_audio)
        language = detect_language(echo_reduced_audio, language_hint)

        text, confidence, timestamps, model_used = conformer_transcribe(echo_reduced_audio, language)
        fallback_used = False
        if confidence < 0.7:
            fb_text, fb_confidence, fb_timestamps, fb_model = whisper_transcribe(echo_reduced_audio, language)
            if fb_confidence >= confidence:
                text = fb_text
                confidence = fb_confidence
                timestamps = fb_timestamps
                model_used = fb_model
                fallback_used = True

        refined_text = refine_transcript(text, language)
        punctuated_text = add_punctuation(refined_text, language)
        truecased_text = apply_truecase(punctuated_text, language)
        normalized_text = apply_itn(truecased_text, language)
        quality_score = score_quality(normalized_text, confidence)

        meta = {
            "duration_seconds": duration_seconds,
            "segments": vad_segments,
            "quality_score": quality_score,
            "language_hint": language_hint,
            "fallback_used": fallback_used,
            "model_name": self.model_name,
            "model_version": self.model_version,
        }

        self.logger.info(
            "Finished STT pipeline run (model=%s, confidence=%.2f, fallback=%s)",
            model_used,
            confidence,
            fallback_used,
        )

        return SttResult(
            text=normalized_text,
            language=language,
            confidence=confidence,
            timestamps=timestamps,
            meta=meta,
            modelUsed=model_used,
        )
