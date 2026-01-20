"""Configuration"""
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    anthropic_api_key: Optional[str] = None
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "https://cloud.langfuse.com"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

def get_settings():
    return Settings()
