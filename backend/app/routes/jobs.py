"""Job management endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status

from app.auth.firebase import get_current_user
from app.models.schemas import (
    DownloadResponse,
    JobCreateRequest,
    JobListResponse,
    JobResponse,
    JobStatus,
    OutputFormat,
    UploadResponse,
    UserInfo,
)
from app.services.firestore import get_firestore_service, FirestoreService
from app.services.storage import get_storage_service, StorageService
from app.services.pubsub import get_pubsub_service, PubSubService
from app.config import get_settings

router = APIRouter(prefix="/api", tags=["Jobs"])


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    output_format: OutputFormat = Form(default=OutputFormat.DOCX),
    user: UserInfo = Depends(get_current_user),
    storage: StorageService = Depends(get_storage_service),
    firestore: FirestoreService = Depends(get_firestore_service),
    pubsub: PubSubService = Depends(get_pubsub_service),
) -> UploadResponse:
    """
    Upload a PDF file for OCR processing.

    - Validates file type and size
    - Creates a job record
    - Generates signed upload URL
    - Publishes job to processing queue
    """
    settings = get_settings()

    # Validate file extension
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required",
        )

    file_ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if file_ext not in settings.allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {settings.allowed_extensions}",
        )

    # Read file content to get size and upload
    content = await file.read()
    file_size = len(content)

    # Validate file size
    max_size = settings.max_file_size_mb * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {settings.max_file_size_mb}MB",
        )

    # Generate job ID
    job_id = str(uuid.uuid4())

    # Get input path
    input_path = storage.get_file_path(user.uid, job_id, file.filename)

    # Create job in Firestore
    job = firestore.create_job(
        job_id=job_id,
        user_id=user.uid,
        filename=file.filename,
        file_size=file_size,
        output_format=output_format,
        input_path=input_path,
    )

    # Generate upload URL
    upload_url = storage.generate_upload_url(
        user_id=user.uid,
        job_id=job_id,
        filename=file.filename,
    )

    # Publish to Pub/Sub for processing
    pubsub.publish_job(
        job_id=job_id,
        user_id=user.uid,
        input_path=input_path,
        output_format=output_format.value,
    )

    return UploadResponse(
        job_id=job_id,
        upload_url=upload_url,
        message="Job created. Upload your file using the provided URL.",
    )


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    status_filter: Optional[JobStatus] = None,
    limit: int = 50,
    user: UserInfo = Depends(get_current_user),
    firestore: FirestoreService = Depends(get_firestore_service),
) -> JobListResponse:
    """
    List all jobs for the authenticated user.

    - Optional status filter
    - Ordered by creation date (newest first)
    """
    jobs = firestore.get_user_jobs(
        user_id=user.uid,
        limit=limit,
        status_filter=status_filter,
    )

    return JobListResponse(jobs=jobs, total=len(jobs))


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: str,
    user: UserInfo = Depends(get_current_user),
    firestore: FirestoreService = Depends(get_firestore_service),
) -> JobResponse:
    """
    Get details of a specific job.

    - User can only access their own jobs
    """
    job = firestore.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Check ownership
    if job.user_id != user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return job


@router.get("/jobs/{job_id}/download", response_model=DownloadResponse)
async def get_download_url(
    job_id: str,
    user: UserInfo = Depends(get_current_user),
    firestore: FirestoreService = Depends(get_firestore_service),
    storage: StorageService = Depends(get_storage_service),
) -> DownloadResponse:
    """
    Get a signed URL to download the processed file.

    - Only available for completed jobs
    - User can only download their own files
    """
    job = firestore.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Check ownership
    if job.user_id != user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Check status
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed. Current status: {job.status.value}",
        )

    # Generate output filename
    base_name = job.filename.rsplit(".", 1)[0]
    output_filename = f"{base_name}.{job.output_format.value}"

    # Generate download URL
    download_url = storage.generate_download_url(
        user_id=user.uid,
        job_id=job_id,
        filename=output_filename,
        bucket_type="output",
    )

    return DownloadResponse(
        download_url=download_url,
        filename=output_filename,
        expires_in=3600,  # 1 hour
    )


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str,
    user: UserInfo = Depends(get_current_user),
    firestore: FirestoreService = Depends(get_firestore_service),
    storage: StorageService = Depends(get_storage_service),
) -> None:
    """
    Delete a job and its associated files.

    - User can only delete their own jobs
    - Deletes both input and output files
    """
    # Check ownership
    owner = firestore.get_job_owner(job_id)

    if owner is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if owner != user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Delete files from storage
    storage.delete_job_files(user.uid, job_id)

    # Delete job document
    firestore.delete_job(job_id)
