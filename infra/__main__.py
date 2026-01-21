"""
OCR Perfect Infrastructure - Pulumi Program

This program manages all Google Cloud resources for OCR Perfect:
- Cloud Storage buckets (input/output)
- Firestore database
- Pub/Sub topics for job processing
- Service accounts and IAM
- Required APIs

Usage:
    pulumi up      # Create/update infrastructure
    pulumi destroy # Delete all infrastructure
    pulumi preview # Preview changes without applying
"""

import pulumi
from pulumi_gcp import storage, firestore, pubsub, projects, serviceaccount

# =============================================================================
# Configuration
# =============================================================================

config = pulumi.Config()
gcp_config = pulumi.Config("gcp")

project = gcp_config.require("project")
region = gcp_config.get("region") or "us-central1"

# =============================================================================
# Enable Required APIs
# =============================================================================

required_apis = [
    "cloudresourcemanager.googleapis.com",
    "firebase.googleapis.com",
    "firestore.googleapis.com",
    "storage.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "pubsub.googleapis.com",
    "identitytoolkit.googleapis.com",
    "iam.googleapis.com",
    "iamcredentials.googleapis.com",
]

enabled_apis = {}
for api in required_apis:
    api_name = api.split(".")[0]
    enabled_apis[api_name] = projects.Service(
        f"api-{api_name}",
        service=api,
        project=project,
        disable_on_destroy=False,  # Don't disable APIs on destroy (safer)
    )

# =============================================================================
# Cloud Storage Buckets
# =============================================================================

# Input bucket for uploaded PDFs
input_bucket = storage.Bucket(
    "input-bucket",
    name=f"{project}-input",
    location=region,
    storage_class="STANDARD",
    uniform_bucket_level_access=True,
    public_access_prevention="enforced",
    versioning=storage.BucketVersioningArgs(enabled=False),
    lifecycle_rules=[
        storage.BucketLifecycleRuleArgs(
            action=storage.BucketLifecycleRuleActionArgs(type="Delete"),
            condition=storage.BucketLifecycleRuleConditionArgs(age=30),
        )
    ],
    opts=pulumi.ResourceOptions(depends_on=[enabled_apis["storage"]]),
)

# Output bucket for processed results
output_bucket = storage.Bucket(
    "output-bucket",
    name=f"{project}-output",
    location=region,
    storage_class="STANDARD",
    uniform_bucket_level_access=True,
    public_access_prevention="enforced",
    versioning=storage.BucketVersioningArgs(enabled=False),
    lifecycle_rules=[
        storage.BucketLifecycleRuleArgs(
            action=storage.BucketLifecycleRuleActionArgs(type="Delete"),
            condition=storage.BucketLifecycleRuleConditionArgs(age=30),
        )
    ],
    opts=pulumi.ResourceOptions(depends_on=[enabled_apis["storage"]]),
)

# =============================================================================
# Firestore Database
# =============================================================================

firestore_db = firestore.Database(
    "firestore-db",
    name="(default)",
    location_id=region,
    type="FIRESTORE_NATIVE",
    concurrency_mode="PESSIMISTIC",
    delete_protection_state="DELETE_PROTECTION_DISABLED",
    project=project,
    opts=pulumi.ResourceOptions(depends_on=[enabled_apis["firestore"]]),
)

# =============================================================================
# Pub/Sub for Job Processing
# =============================================================================

# Topic for new OCR jobs
jobs_topic = pubsub.Topic(
    "jobs-topic",
    name="ocr-jobs",
    project=project,
    opts=pulumi.ResourceOptions(depends_on=[enabled_apis["pubsub"]]),
)

# Dead letter topic for failed jobs
dlq_topic = pubsub.Topic(
    "dlq-topic",
    name="ocr-jobs-dlq",
    project=project,
    opts=pulumi.ResourceOptions(depends_on=[enabled_apis["pubsub"]]),
)

# =============================================================================
# Service Accounts
# =============================================================================

# Service account for Cloud Run backend API
backend_sa = serviceaccount.Account(
    "backend-sa",
    account_id="ocr-backend",
    display_name="OCR Backend Service Account",
    project=project,
    opts=pulumi.ResourceOptions(depends_on=[enabled_apis["iam"]]),
)

# Service account for Cloud Run worker jobs
worker_sa = serviceaccount.Account(
    "worker-sa",
    account_id="ocr-worker",
    display_name="OCR Worker Service Account",
    project=project,
    opts=pulumi.ResourceOptions(depends_on=[enabled_apis["iam"]]),
)

# =============================================================================
# IAM Bindings
# =============================================================================

# Backend SA permissions
backend_storage_binding = projects.IAMMember(
    "backend-storage-admin",
    project=project,
    role="roles/storage.objectAdmin",
    member=backend_sa.email.apply(lambda email: f"serviceAccount:{email}"),
)

backend_firestore_binding = projects.IAMMember(
    "backend-firestore-user",
    project=project,
    role="roles/datastore.user",
    member=backend_sa.email.apply(lambda email: f"serviceAccount:{email}"),
)

backend_pubsub_binding = projects.IAMMember(
    "backend-pubsub-publisher",
    project=project,
    role="roles/pubsub.publisher",
    member=backend_sa.email.apply(lambda email: f"serviceAccount:{email}"),
)

# Worker SA permissions
worker_storage_binding = projects.IAMMember(
    "worker-storage-admin",
    project=project,
    role="roles/storage.objectAdmin",
    member=worker_sa.email.apply(lambda email: f"serviceAccount:{email}"),
)

worker_firestore_binding = projects.IAMMember(
    "worker-firestore-user",
    project=project,
    role="roles/datastore.user",
    member=worker_sa.email.apply(lambda email: f"serviceAccount:{email}"),
)

# =============================================================================
# Exports
# =============================================================================

pulumi.export("project", project)
pulumi.export("region", region)
pulumi.export("input_bucket_name", input_bucket.name)
pulumi.export("input_bucket_url", input_bucket.url)
pulumi.export("output_bucket_name", output_bucket.name)
pulumi.export("output_bucket_url", output_bucket.url)
pulumi.export("firestore_db_name", firestore_db.name)
pulumi.export("jobs_topic_name", jobs_topic.name)
pulumi.export("jobs_topic_id", jobs_topic.id)
pulumi.export("dlq_topic_name", dlq_topic.name)
pulumi.export("backend_sa_email", backend_sa.email)
pulumi.export("worker_sa_email", worker_sa.email)
