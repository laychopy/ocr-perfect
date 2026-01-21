"""Cloud Storage service for file operations."""

from datetime import timedelta
from typing import Optional

from google.cloud import storage

from app.config import get_settings


class StorageService:
    """Service for Cloud Storage operations."""

    def __init__(self):
        self.settings = get_settings()
        self.client = storage.Client(project=self.settings.gcp_project)
        self.input_bucket = self.client.bucket(self.settings.input_bucket)
        self.output_bucket = self.client.bucket(self.settings.output_bucket)

    def generate_upload_url(
        self,
        user_id: str,
        job_id: str,
        filename: str,
        content_type: str = "application/pdf",
        expiration_minutes: int = 15,
    ) -> str:
        """
        Generate a signed URL for uploading a file.

        Args:
            user_id: The user's ID
            job_id: The job ID
            filename: Original filename
            content_type: MIME type of the file
            expiration_minutes: URL expiration time

        Returns:
            Signed upload URL
        """
        blob_path = f"{user_id}/{job_id}/{filename}"
        blob = self.input_bucket.blob(blob_path)

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="PUT",
            content_type=content_type,
        )

        return url

    def generate_download_url(
        self,
        user_id: str,
        job_id: str,
        filename: str,
        bucket_type: str = "output",
        expiration_minutes: int = 60,
    ) -> str:
        """
        Generate a signed URL for downloading a file.

        Args:
            user_id: The user's ID
            job_id: The job ID
            filename: The filename to download
            bucket_type: "input" or "output"
            expiration_minutes: URL expiration time

        Returns:
            Signed download URL
        """
        bucket = self.output_bucket if bucket_type == "output" else self.input_bucket
        blob_path = f"{user_id}/{job_id}/{filename}"
        blob = bucket.blob(blob_path)

        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="GET",
        )

        return url

    def get_file_path(self, user_id: str, job_id: str, filename: str) -> str:
        """Get the GCS path for a file."""
        return f"gs://{self.settings.input_bucket}/{user_id}/{job_id}/{filename}"

    def get_output_path(self, user_id: str, job_id: str, filename: str) -> str:
        """Get the GCS path for an output file."""
        return f"gs://{self.settings.output_bucket}/{user_id}/{job_id}/{filename}"

    def delete_job_files(self, user_id: str, job_id: str) -> None:
        """
        Delete all files associated with a job.

        Args:
            user_id: The user's ID
            job_id: The job ID
        """
        prefix = f"{user_id}/{job_id}/"

        # Delete from input bucket
        blobs = self.input_bucket.list_blobs(prefix=prefix)
        for blob in blobs:
            blob.delete()

        # Delete from output bucket
        blobs = self.output_bucket.list_blobs(prefix=prefix)
        for blob in blobs:
            blob.delete()

    def file_exists(
        self, user_id: str, job_id: str, filename: str, bucket_type: str = "input"
    ) -> bool:
        """Check if a file exists in storage."""
        bucket = self.output_bucket if bucket_type == "output" else self.input_bucket
        blob_path = f"{user_id}/{job_id}/{filename}"
        blob = bucket.blob(blob_path)
        return blob.exists()


# Singleton instance
_storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Get or create storage service instance."""
    global _storage_service
    if _storage_service is None:
        _storage_service = StorageService()
    return _storage_service
