"""FastAPI application for the modular TTS service."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List, Literal

from fastapi import FastAPI, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from common import (  # noqa: E402  # pylint: disable=wrong-import-position
    ModelInfo,
    configure_logging,
    get_active_models,
    register_model,
    set_model_status,
    settings,
)
from core import TTSPipeline, TTSPipelineInput  # noqa: E402


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1)
    language: str | None = None
    voice_id: str | None = None
    emotion: str | None = None
    speed: float = Field(default=1.0, gt=0.0, le=3.0)


class TTSResponse(BaseModel):
    audio_path: str
    duration: float | None = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    status: str = "success"


class StatusResponse(BaseModel):
    status: str
    detail: str
    models: List[Dict[str, Any]] = Field(default_factory=list)


MODEL_NAME = "vits_multispkr_indic"
MODEL_VERSION = "v1"
pipeline: TTSPipeline | None = None
app = FastAPI(title="TTS Service", version="0.3.0")


def _pipeline_input(payload: TTSRequest) -> TTSPipelineInput:
    return TTSPipelineInput(
        text=payload.text,
        language=payload.language,
        voice_id=payload.voice_id,
        emotion=payload.emotion,
        speed=payload.speed,
    )


def _model_path() -> str:
    return f"{settings.model_base_path}/tts/{MODEL_NAME}/{MODEL_VERSION}"


def _register_default_model(status: Literal["loading", "ready", "error"] = "ready") -> ModelInfo:
    model_info = ModelInfo(
        name=MODEL_NAME,
        type="tts",
        version=MODEL_VERSION,
        status=status,
        path=_model_path(),
        config={"device": settings.device},
    )
    return register_model(model_info)


async def _initialize_pipeline() -> None:
    global pipeline
    pipeline = TTSPipeline(settings=settings, model_name=MODEL_NAME, model_version=MODEL_VERSION)


@app.on_event("startup")
async def startup_event() -> None:
    configure_logging(settings.log_level)
    _register_default_model(status="loading")
    await _initialize_pipeline()
    set_model_status("tts", MODEL_NAME, MODEL_VERSION, "ready", path=_model_path())
    logger.info("TTS service started in {} mode", settings.environment)


@app.get("/ml/tts/health", response_model=StatusResponse)
async def health_check() -> StatusResponse:
    models = [model.model_dump() for model in get_active_models("tts")]
    return StatusResponse(status="ok", detail="tts-service healthy", models=models)


@app.get("/ml/tts/models")
async def list_models() -> Dict[str, Any]:
    return {"models": [model.model_dump() for model in get_active_models("tts")]}


@app.post("/ml/tts/initialize", response_model=StatusResponse)
async def initialize_models() -> StatusResponse:
    set_model_status("tts", MODEL_NAME, MODEL_VERSION, "loading")
    await _initialize_pipeline()
    set_model_status("tts", MODEL_NAME, MODEL_VERSION, "ready", path=_model_path())
    models = [model.model_dump() for model in get_active_models("tts")]
    return StatusResponse(status="ok", detail="TTS pipeline reinitialized", models=models)


@app.post("/ml/tts/reload", response_model=StatusResponse)
async def reload_models() -> StatusResponse:
    set_model_status("tts", MODEL_NAME, MODEL_VERSION, "loading")
    await asyncio.sleep(0.1)
    await _initialize_pipeline()
    set_model_status("tts", MODEL_NAME, MODEL_VERSION, "ready", path=_model_path())
    models = [model.model_dump() for model in get_active_models("tts")]
    return StatusResponse(status="ok", detail="TTS models reloaded", models=models)


@app.post("/ml/tts/predict", response_model=TTSResponse)
async def synthesize_speech(payload: TTSRequest) -> TTSResponse:
    if pipeline is None:
        raise HTTPException(status_code=503, detail="TTS pipeline not initialized")
    result = pipeline.synthesize(_pipeline_input(payload))
    if not result.audio_path:
        raise HTTPException(status_code=500, detail="Failed to synthesize audio")
    return TTSResponse(
        audio_path=result.audio_path,
        duration=result.duration,
        meta=result.meta,
        status="success",
    )
