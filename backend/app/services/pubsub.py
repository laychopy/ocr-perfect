"""Pub/Sub service for job queue management."""

import json
from typing import Optional

from google.cloud import pubsub_v1

from app.config import get_settings


class PubSubService:
    """Service for Pub/Sub operations."""

    def __init__(self):
        self.settings = get_settings()
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(
            self.settings.gcp_project, self.settings.pubsub_topic
        )

    def publish_job(
        self,
        job_id: str,
        user_id: str,
        input_path: str,
        output_format: str,
    ) -> str:
        """
        Publish a job to the processing queue.

        Args:
            job_id: The job ID
            user_id: The user's ID
            input_path: GCS path to input file
            output_format: Desired output format

        Returns:
            Message ID from Pub/Sub
        """
        message_data = {
            "job_id": job_id,
            "user_id": user_id,
            "input_path": input_path,
            "output_format": output_format,
        }

        # Encode message as JSON bytes
        data = json.dumps(message_data).encode("utf-8")

        # Publish message
        future = self.publisher.publish(
            self.topic_path,
            data,
            job_id=job_id,
            user_id=user_id,
        )

        # Wait for publish to complete and get message ID
        message_id = future.result()

        return message_id


# Singleton instance
_pubsub_service: Optional[PubSubService] = None


def get_pubsub_service() -> PubSubService:
    """Get or create Pub/Sub service instance."""
    global _pubsub_service
    if _pubsub_service is None:
        _pubsub_service = PubSubService()
    return _pubsub_service
