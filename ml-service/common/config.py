import os
from pydantic import BaseModel


class Settings(BaseModel):
    environment: str = os.getenv('ENVIRONMENT', 'development')
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')
    model_registry_url: str = os.getenv('MODEL_REGISTRY_URL', 'local://models')


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
