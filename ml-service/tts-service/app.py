"""FastAPI application scaffold for the TTS service."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from loguru import logger
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from common import settings  # noqa: E402  # pylint: disable=wrong-import-position


class TTSRequest(BaseModel):
    text: str
    language: str = 'en-US'
    voice_id: Optional[str] = None
    emotion: Optional[str] = None
    speed: float = 1.0


class TTSInitializeResponse(BaseModel):
    status: str
    detail: str


class TTSResponse(BaseModel):
    audio_url: str
    duration: float
    status: str


app = FastAPI(title='TTS Service', version='0.1.0')


@app.on_event('startup')
async def startup_event() -> None:
    """Placeholder for loading ML artifacts."""
    logger.info('Starting TTS service in {} mode', settings.environment)


@app.get('/ml/tts/health')
async def health_check() -> dict[str, str]:
    return {'status': 'ok', 'service': 'tts-service'}


@app.post('/ml/tts/initialize', response_model=TTSInitializeResponse)
async def initialize_models() -> TTSInitializeResponse:
    logger.info('Initializing TTS pipelines (placeholder)')
    return TTSInitializeResponse(status='ok', detail='TTS pipelines initialized')


@app.post('/ml/tts/predict', response_model=TTSResponse)
async def synthesize_speech(payload: TTSRequest) -> TTSResponse:
    logger.info('Received TTS request: {}', payload.model_dump())
    dummy_audio_url = 'https://example.com/audio/placeholder.wav'
    return TTSResponse(audio_url=dummy_audio_url, duration=5.2, status='success')
