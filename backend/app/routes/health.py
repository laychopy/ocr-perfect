"""Health check endpoint."""

from fastapi import APIRouter

from app.models.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns basic service health information.
    Used by Cloud Run for liveness/readiness probes.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        project="ocr-perfect",
    )
