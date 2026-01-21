"""Application configuration using pydantic-settings."""

from functools import lru_cache
from pydantic import computed_field
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

    # CORS (semicolon-separated string from env, parsed to list)
    allowed_origins_str: str = "https://ocr-perfect.web.app;https://ocr-perfect.firebaseapp.com;http://localhost:5173;http://localhost:3000"

    # File limits
    max_file_size_mb: int = 50
    allowed_extensions_str: str = ".pdf"

    # App settings
    debug: bool = False

    @computed_field
    @property
    def allowed_origins(self) -> list[str]:
        """Parse semicolon-separated allowed origins into list."""
        return [origin.strip() for origin in self.allowed_origins_str.split(";") if origin.strip()]

    @computed_field
    @property
    def allowed_extensions(self) -> list[str]:
        """Parse comma-separated extensions into list."""
        return [ext.strip() for ext in self.allowed_extensions_str.split(",") if ext.strip()]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
