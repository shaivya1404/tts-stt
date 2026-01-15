"""FastAPI application scaffold for the STT service."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, UploadFile
from loguru import logger
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from common import settings  # noqa: E402  # pylint: disable=wrong-import-position


class Timestamp(BaseModel):
    start: float
    end: float
    word: str


class STTInitializeResponse(BaseModel):
    status: str
    detail: str


class STTResponse(BaseModel):
    text: str
    language: str
    confidence: float
    timestamps: List[Timestamp]


app = FastAPI(title='STT Service', version='0.1.0')


@app.on_event('startup')
async def startup_event() -> None:
    logger.info('Starting STT service in {} mode', settings.environment)


@app.get('/ml/stt/health')
async def health_check() -> dict[str, str]:
    return {'status': 'ok', 'service': 'stt-service'}


@app.post('/ml/stt/initialize', response_model=STTInitializeResponse)
async def initialize_models() -> STTInitializeResponse:
    logger.info('Initializing STT pipelines (placeholder)')
    return STTInitializeResponse(status='ok', detail='STT pipelines initialized')


@app.post('/ml/stt/transcribe', response_model=STTResponse)
async def transcribe_audio(file: UploadFile = File(...)) -> STTResponse:
    content = await file.read()
    logger.info('Received STT transcription request for {} ({} bytes)', file.filename, len(content))
    timestamps = [
        Timestamp(start=0.0, end=1.0, word='hello'),
        Timestamp(start=1.0, end=2.0, word='world'),
    ]
    return STTResponse(
        text='hello world',
        language='en-US',
        confidence=0.98,
        timestamps=timestamps,
    )
