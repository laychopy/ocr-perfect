"""
OCR Perfect Backend API

FastAPI application for OCR processing jobs.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import health, jobs


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    settings = get_settings()
    print(f"Starting OCR Perfect API (project: {settings.gcp_project})")
    yield
    # Shutdown
    print("Shutting down OCR Perfect API")


# Create FastAPI app
app = FastAPI(
    title="OCR Perfect API",
    description="Backend API for OCR document processing",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(jobs.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "OCR Perfect API",
        "version": "1.0.0",
        "docs": "/docs",
    }
