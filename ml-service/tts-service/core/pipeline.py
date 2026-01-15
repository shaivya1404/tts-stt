"""Modular placeholder pipeline for VITS + HiFi-GAN based TTS."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
from uuid import uuid4

from loguru import logger
from pydantic import BaseModel, Field

from common import Settings

from . import (
    audio_postprocess,
    g2p,
    language_id,
    quality_mosnet,
    speaker_encoder,
    style_emotion,
    text_normalization,
    vits_wrapper,
    vocoder_hifigan,
)


class TtsRequest(BaseModel):
    """Schema describing incoming synthesis payloads."""

    text: str = Field(..., min_length=1)
    language: str | None = None
    voice_id: str | None = None
    emotion: str | None = None
    speed: float = Field(default=1.0, gt=0.0, le=5.0)


class TtsResult(BaseModel):
    """Structured response emitted by the pipeline."""

    audio_path: str | None = None
    duration: float | None = None
    status: str = "success"
    meta: Dict[str, Any] = Field(default_factory=dict)


class TTSPipeline:
    """Orchestrates the VITS + HiFi-GAN + RNNoise style placeholder pipeline."""

    def __init__(self, settings: Settings, model_name: str = "vits_multispkr_indic", model_version: str = "v1") -> None:
        self.settings = settings
        self.model_name = model_name
        self.model_version = model_version
        self.logger = logger.bind(component="tts_pipeline", model=model_name, version=model_version)

    def synthesize(self, request: TtsRequest) -> TtsResult:
        self.logger.info("Starting synthesis (chars={}, voice={})", len(request.text), request.voice_id or "default")

        detected_language = language_id.detect_language(request.text, request.language)
        normalized_text = text_normalization.normalize_text(request.text, detected_language)
        phonemes = g2p.text_to_phonemes(normalized_text, detected_language)
        speaker_embedding = speaker_encoder.get_speaker_embedding(request.voice_id, None)
        style_params = style_emotion.apply_style_emotion(request.emotion, detected_language)
        style_params["speed"] = request.speed

        coarse_waveform, duration = vits_wrapper.synthesize_waveform(
            phonemes, speaker_embedding, style_params, detected_language
        )
        duration = duration / max(request.speed, 0.1)

        vocoded = vocoder_hifigan.vocode(coarse_waveform, detected_language)
        enhanced_audio = audio_postprocess.denoise_and_enhance(vocoded)
        mos_score = quality_mosnet.estimate_mos(enhanced_audio)

        filename = f"{request.voice_id or 'default'}_{uuid4().hex}.wav"
        output_dir = Path(self.settings.model_base_path) / "tts" / self.model_name / self.model_version / "synthesized"
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            fallback_dir = Path("/tmp/models") / "tts" / self.model_name / self.model_version / "synthesized"
            fallback_dir.mkdir(parents=True, exist_ok=True)
            output_dir = fallback_dir
        output_path = output_dir / filename

        meta = {
            "language": detected_language,
            "phoneme_count": len(phonemes),
            "style": style_params,
            "mos": mos_score,
            "model": self.model_name,
            "version": self.model_version,
            "char_count": len(request.text),
        }
        self.logger.info("Completed synthesis -> {} (duration ~{:.2f}s)", output_path, duration)

        return TtsResult(audio_path=str(output_path), duration=round(duration, 4), status="success", meta=meta)
