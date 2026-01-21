"""Firestore service for job management."""

from datetime import datetime
from typing import Optional

from google.cloud import firestore

from app.config import get_settings
from app.models.schemas import JobResponse, JobStatus, OutputFormat


class FirestoreService:
    """Service for Firestore operations."""

    def __init__(self):
        self.settings = get_settings()
        self.client = firestore.Client(project=self.settings.gcp_project)
        self.jobs_collection = self.client.collection("jobs")

    def create_job(
        self,
        job_id: str,
        user_id: str,
        filename: str,
        file_size: int,
        output_format: OutputFormat,
        input_path: str,
    ) -> JobResponse:
        """
        Create a new job document.

        Args:
            job_id: Unique job identifier
            user_id: Owner's user ID
            filename: Original filename
            file_size: File size in bytes
            output_format: Desired output format
            input_path: GCS path to input file

        Returns:
            Created job as JobResponse
        """
        now = datetime.utcnow()

        job_data = {
            "user_id": user_id,
            "status": JobStatus.PENDING.value,
            "filename": filename,
            "file_size": file_size,
            "output_format": output_format.value,
            "input_path": input_path,
            "output_path": None,
            "page_count": None,
            "created_at": now,
            "updated_at": now,
            "completed_at": None,
            "error_message": None,
        }

        self.jobs_collection.document(job_id).set(job_data)

        return JobResponse(
            id=job_id,
            user_id=user_id,
            status=JobStatus.PENDING,
            filename=filename,
            file_size=file_size,
            output_format=output_format,
            created_at=now,
            updated_at=now,
        )

    def get_job(self, job_id: str) -> Optional[JobResponse]:
        """
        Get a job by ID.

        Args:
            job_id: The job ID

        Returns:
            JobResponse if found, None otherwise
        """
        doc = self.jobs_collection.document(job_id).get()

        if not doc.exists:
            return None

        data = doc.to_dict()
        return JobResponse(
            id=doc.id,
            user_id=data["user_id"],
            status=JobStatus(data["status"]),
            filename=data["filename"],
            file_size=data["file_size"],
            output_format=OutputFormat(data["output_format"]),
            page_count=data.get("page_count"),
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            completed_at=data.get("completed_at"),
            error_message=data.get("error_message"),
        )

    def get_user_jobs(
        self,
        user_id: str,
        limit: int = 50,
        status_filter: Optional[JobStatus] = None,
    ) -> list[JobResponse]:
        """
        Get all jobs for a user.

        Args:
            user_id: The user's ID
            limit: Maximum number of jobs to return
            status_filter: Optional status filter

        Returns:
            List of JobResponse objects
        """
        query = self.jobs_collection.where("user_id", "==", user_id)

        if status_filter:
            query = query.where("status", "==", status_filter.value)

        query = query.order_by("created_at", direction=firestore.Query.DESCENDING)
        query = query.limit(limit)

        jobs = []
        for doc in query.stream():
            data = doc.to_dict()
            jobs.append(
                JobResponse(
                    id=doc.id,
                    user_id=data["user_id"],
                    status=JobStatus(data["status"]),
                    filename=data["filename"],
                    file_size=data["file_size"],
                    output_format=OutputFormat(data["output_format"]),
                    page_count=data.get("page_count"),
                    created_at=data["created_at"],
                    updated_at=data["updated_at"],
                    completed_at=data.get("completed_at"),
                    error_message=data.get("error_message"),
                )
            )

        return jobs

    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        error_message: Optional[str] = None,
        output_path: Optional[str] = None,
        page_count: Optional[int] = None,
    ) -> None:
        """
        Update job status.

        Args:
            job_id: The job ID
            status: New status
            error_message: Error message (if failed)
            output_path: Path to output file (if completed)
            page_count: Number of pages processed
        """
        update_data = {
            "status": status.value,
            "updated_at": datetime.utcnow(),
        }

        if status == JobStatus.COMPLETED:
            update_data["completed_at"] = datetime.utcnow()

        if error_message is not None:
            update_data["error_message"] = error_message

        if output_path is not None:
            update_data["output_path"] = output_path

        if page_count is not None:
            update_data["page_count"] = page_count

        self.jobs_collection.document(job_id).update(update_data)

    def delete_job(self, job_id: str) -> bool:
        """
        Delete a job document.

        Args:
            job_id: The job ID

        Returns:
            True if deleted, False if not found
        """
        doc_ref = self.jobs_collection.document(job_id)
        doc = doc_ref.get()

        if not doc.exists:
            return False

        doc_ref.delete()
        return True

    def get_job_owner(self, job_id: str) -> Optional[str]:
        """Get the owner (user_id) of a job."""
        doc = self.jobs_collection.document(job_id).get()
        if not doc.exists:
            return None
        return doc.to_dict().get("user_id")


# Singleton instance
_firestore_service: Optional[FirestoreService] = None


def get_firestore_service() -> FirestoreService:
    """Get or create Firestore service instance."""
    global _firestore_service
    if _firestore_service is None:
        _firestore_service = FirestoreService()
    return _firestore_service
