"""Pydantic models for API request/response schemas."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    """Job processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class OutputFormat(str, Enum):
    """Supported output formats."""

    DOCX = "docx"
    JSON = "json"
    TXT = "txt"
    PDF = "pdf"


# Request Models
class JobCreateRequest(BaseModel):
    """Request to create a new job."""

    output_format: OutputFormat = OutputFormat.DOCX


# Response Models
class UserInfo(BaseModel):
    """Authenticated user information."""

    uid: str
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None


class JobResponse(BaseModel):
    """Job response model."""

    id: str
    user_id: str
    status: JobStatus
    filename: str
    file_size: int
    output_format: OutputFormat
    page_count: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Response for listing jobs."""

    jobs: list[JobResponse]
    total: int


class UploadResponse(BaseModel):
    """Response after uploading a file."""

    job_id: str
    upload_url: str
    message: str = "File uploaded successfully"


class DownloadResponse(BaseModel):
    """Response with download URL."""

    download_url: str
    filename: str
    expires_in: int = Field(description="URL expiration in seconds")


class ErrorResponse(BaseModel):
    """Error response model."""

    detail: str
    code: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "1.0.0"
    project: str = "ocr-perfect"
