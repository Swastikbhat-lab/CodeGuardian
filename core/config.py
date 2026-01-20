"""Configuration"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    anthropic_api_key: Optional[str] = None
    
    class Config:
        env_file = ".env"
        extra = "ignore"

def get_settings():
    return Settings()
