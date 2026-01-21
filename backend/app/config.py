"""Application configuration using pydantic-settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # GCP Configuration
    gcp_project: str = "ocr-perfect"
    gcp_region: str = "us-central1"

    # Storage Buckets
    input_bucket: str = "ocr-perfect-input"
    output_bucket: str = "ocr-perfect-output"

    # Pub/Sub
    pubsub_topic: str = "ocr-jobs"

    # CORS
    allowed_origins: list[str] = [
        "https://ocr-perfect.web.app",
        "https://ocr-perfect.firebaseapp.com",
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    # File limits
    max_file_size_mb: int = 50
    allowed_extensions: list[str] = [".pdf"]

    # App settings
    debug: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
