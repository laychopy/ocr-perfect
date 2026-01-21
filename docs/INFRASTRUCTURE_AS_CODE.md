# Infrastructure as Code (IaC) Plan

## Overview

This document outlines the plan to manage all OCR Perfect infrastructure using Pulumi with GitHub Actions for automated deployments. This enables:

- **Reproducibility:** Spin up identical environments with one command
- **Destruction:** Tear down all resources cleanly with `pulumi destroy`
- **Version Control:** Infrastructure changes tracked in Git
- **Automation:** Deploy on push to main branch

## Why Pulumi over Terraform?

| Feature | Pulumi | Terraform |
|---------|--------|-----------|
| Language | Python, TypeScript, Go | HCL (custom) |
| State Management | Pulumi Cloud (free tier) or self-hosted | Terraform Cloud or S3/GCS |
| GCP Support | Excellent | Excellent |
| Firebase Support | Good (via GCP provider) | Limited |
| Learning Curve | Lower (use familiar language) | Higher (learn HCL) |

**Recommendation:** Use Pulumi with Python (matches OCR pipeline language).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      GitHub Repository                          │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   infra/     │    │   backend/   │    │  frontend/   │      │
│  │   Pulumi     │    │   FastAPI    │    │   React      │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │               │
└─────────┼───────────────────┼───────────────────┼───────────────┘
          │                   │                   │
          ▼                   ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GitHub Actions                              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  on push to main:                                         │  │
│  │  1. pulumi preview / pulumi up (infra)                   │  │
│  │  2. docker build & push (backend)                        │  │
│  │  3. npm build & firebase deploy (frontend)               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼ (Workload Identity Federation - no keys!)
┌─────────────────────────────────────────────────────────────────┐
│                      Google Cloud                                │
│                                                                  │
│  Managed by Pulumi:                                             │
│  ├── Project APIs                                               │
│  ├── Firestore Database                                         │
│  ├── Cloud Storage Buckets                                      │
│  ├── Cloud Run Services                                         │
│  ├── Cloud Run Jobs                                             │
│  ├── Pub/Sub Topics                                             │
│  ├── IAM Service Accounts                                       │
│  └── Firebase (via gcloud commands in Pulumi)                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
ocr-pipeline/
├── infra/                        # Pulumi infrastructure
│   ├── __main__.py              # Main Pulumi program
│   ├── Pulumi.yaml              # Pulumi project config
│   ├── Pulumi.dev.yaml          # Dev stack config
│   ├── Pulumi.prod.yaml         # Prod stack config
│   ├── requirements.txt         # Pulumi dependencies
│   └── components/
│       ├── storage.py           # Cloud Storage resources
│       ├── firestore.py         # Firestore resources
│       ├── cloud_run.py         # Cloud Run services
│       ├── pubsub.py            # Pub/Sub resources
│       └── iam.py               # IAM and service accounts
├── .github/
│   └── workflows/
│       ├── infra.yml            # Infrastructure deployment
│       ├── backend.yml          # Backend deployment
│       └── frontend.yml         # Frontend deployment
└── ...
```

---

## GitHub Actions + Workload Identity Federation

### Why Workload Identity Federation?

- **No service account keys** stored in GitHub secrets
- **More secure:** Uses OIDC tokens, short-lived
- **Google recommended** approach

### Setup Steps

#### 1. Create Workload Identity Pool (one-time)

```bash
# Create identity pool
gcloud iam workload-identity-pools create "github-pool" \
  --location="global" \
  --display-name="GitHub Actions Pool" \
  --project=ocr-perfect

# Create provider for GitHub
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --project=ocr-perfect
```

#### 2. Create Service Account for GitHub Actions

```bash
# Create service account
gcloud iam service-accounts create "github-actions" \
  --display-name="GitHub Actions" \
  --project=ocr-perfect

# Grant necessary roles
gcloud projects add-iam-policy-binding ocr-perfect \
  --member="serviceAccount:github-actions@ocr-perfect.iam.gserviceaccount.com" \
  --role="roles/editor"

gcloud projects add-iam-policy-binding ocr-perfect \
  --member="serviceAccount:github-actions@ocr-perfect.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Allow GitHub Actions to impersonate this service account
gcloud iam service-accounts add-iam-policy-binding \
  "github-actions@ocr-perfect.iam.gserviceaccount.com" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/276562330509/locations/global/workloadIdentityPools/github-pool/attribute.repository/laychopy/ocr-perfect" \
  --project=ocr-perfect
```

#### 3. GitHub Actions Workflow

```yaml
# .github/workflows/infra.yml
name: Infrastructure

on:
  push:
    branches: [main]
    paths:
      - 'infra/**'
  pull_request:
    branches: [main]
    paths:
      - 'infra/**'

permissions:
  contents: read
  id-token: write  # Required for Workload Identity Federation

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Authenticate to Google Cloud
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: 'projects/276562330509/locations/global/workloadIdentityPools/github-pool/providers/github-provider'
          service_account: 'github-actions@ocr-perfect.iam.gserviceaccount.com'

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Pulumi
        uses: pulumi/actions@v5

      - name: Install dependencies
        run: |
          cd infra
          pip install -r requirements.txt

      - name: Pulumi Preview (PR)
        if: github.event_name == 'pull_request'
        run: |
          cd infra
          pulumi preview --stack dev
        env:
          PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}

      - name: Pulumi Up (Push to main)
        if: github.event_name == 'push'
        run: |
          cd infra
          pulumi up --yes --stack dev
        env:
          PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
```

---

## Pulumi Implementation

### Main Program (`infra/__main__.py`)

```python
"""OCR Perfect Infrastructure - Pulumi Program"""

import pulumi
from pulumi_gcp import storage, firestore, cloudrun, pubsub, projects

# Configuration
config = pulumi.Config()
project = config.require("gcp_project")
region = config.get("gcp_region") or "us-central1"

# Enable required APIs
apis = [
    "cloudresourcemanager.googleapis.com",
    "firebase.googleapis.com",
    "firestore.googleapis.com",
    "storage.googleapis.com",
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "pubsub.googleapis.com",
    "identitytoolkit.googleapis.com",
]

enabled_apis = []
for api in apis:
    service = projects.Service(
        f"api-{api.split('.')[0]}",
        service=api,
        project=project,
        disable_on_destroy=False,
    )
    enabled_apis.append(service)

# Cloud Storage Buckets
input_bucket = storage.Bucket(
    "input-bucket",
    name=f"{project}-input",
    location=region,
    uniform_bucket_level_access=True,
    lifecycle_rules=[
        storage.BucketLifecycleRuleArgs(
            action=storage.BucketLifecycleRuleActionArgs(type="Delete"),
            condition=storage.BucketLifecycleRuleConditionArgs(age=30),
        )
    ],
)

output_bucket = storage.Bucket(
    "output-bucket",
    name=f"{project}-output",
    location=region,
    uniform_bucket_level_access=True,
    lifecycle_rules=[
        storage.BucketLifecycleRuleArgs(
            action=storage.BucketLifecycleRuleActionArgs(type="Delete"),
            condition=storage.BucketLifecycleRuleConditionArgs(age=30),
        )
    ],
)

# Firestore Database
firestore_db = firestore.Database(
    "firestore-db",
    name="(default)",
    location_id=region,
    type="FIRESTORE_NATIVE",
    project=project,
)

# Pub/Sub Topic for job processing
jobs_topic = pubsub.Topic(
    "jobs-topic",
    name="ocr-jobs",
    project=project,
)

# Exports
pulumi.export("input_bucket", input_bucket.name)
pulumi.export("output_bucket", output_bucket.name)
pulumi.export("firestore_db", firestore_db.name)
pulumi.export("jobs_topic", jobs_topic.name)
```

### Stack Configuration (`infra/Pulumi.dev.yaml`)

```yaml
config:
  gcp:project: ocr-perfect
  gcp:region: us-central1
  ocr-perfect:gcp_project: ocr-perfect
  ocr-perfect:gcp_region: us-central1
```

---

## Commands Reference

### Local Development

```bash
# Install Pulumi CLI
brew install pulumi

# Login to Pulumi Cloud (free tier)
pulumi login

# Initialize stack
cd infra
pulumi stack init dev

# Preview changes
pulumi preview

# Apply changes
pulumi up

# Destroy all resources
pulumi destroy

# View current state
pulumi stack output
```

### GitHub Secrets Required

| Secret | Description |
|--------|-------------|
| `PULUMI_ACCESS_TOKEN` | Token from Pulumi Cloud (app.pulumi.com) |

Note: GCP authentication uses Workload Identity Federation, no keys needed!

---

## Migration Plan

Since we already created resources manually, we need to import them:

```bash
# Import existing resources into Pulumi state
pulumi import gcp:storage/bucket:Bucket input-bucket ocr-perfect-input
pulumi import gcp:storage/bucket:Bucket output-bucket ocr-perfect-output
pulumi import gcp:firestore/database:Database firestore-db projects/ocr-perfect/databases/(default)
```

---

## Implementation Status

- [x] Create `infra/` directory with Pulumi program
- [x] Test `pulumi up` - creates all resources
- [x] Test `pulumi destroy` - deletes all resources
- [x] Test recreate - full cycle works
- [ ] Set up Workload Identity Federation in GCP (for GitHub Actions)
- [ ] Create GitHub Actions workflows
- [ ] Test deployment on push to main

---

## Quick Start (Local)

```bash
# Prerequisites
brew install pulumi
gcloud auth application-default login

# Navigate to infra directory
cd infra

# Login to Pulumi (local backend, no account needed)
pulumi login --local

# Create infrastructure
PULUMI_CONFIG_PASSPHRASE="" pulumi up --yes

# View outputs
PULUMI_CONFIG_PASSPHRASE="" pulumi stack output

# Destroy infrastructure
PULUMI_CONFIG_PASSPHRASE="" pulumi destroy --yes
```

---

## Resources Created by Pulumi

| Resource | Name | Description |
|----------|------|-------------|
| Storage Bucket | `ocr-perfect-input` | Uploaded PDFs (30 day lifecycle) |
| Storage Bucket | `ocr-perfect-output` | Processed results (30 day lifecycle) |
| Firestore DB | `(default)` | Job tracking database |
| Pub/Sub Topic | `ocr-jobs` | Job processing queue |
| Pub/Sub Topic | `ocr-jobs-dlq` | Dead letter queue |
| Service Account | `ocr-backend` | Backend API permissions |
| Service Account | `ocr-worker` | Worker job permissions |
| 11 APIs | Various | Required GCP services |

---

## Destroy Process

To completely tear down all infrastructure:

```bash
# From infra/ directory
cd infra
PULUMI_CONFIG_PASSPHRASE="" pulumi destroy --yes

# Note: Firestore has a ~2 minute cooldown before the name can be reused
```

**Warning:** This will delete all data in Firestore and Cloud Storage!

**Note:** The `(default)` Firestore database name has a cooldown period after deletion. Wait 2+ minutes before recreating.

---

## Tested Workflows

### Create Infrastructure
```
$ pulumi up --yes
+ 24 resources created
Duration: ~30s
```

### Destroy Infrastructure
```
$ pulumi destroy --yes
- 24 resources deleted
Duration: ~17s
```

### View Current State
```
$ pulumi stack output
backend_sa_email    ocr-backend@ocr-perfect.iam.gserviceaccount.com
dlq_topic_name      ocr-jobs-dlq
firestore_db_name   (default)
input_bucket_name   ocr-perfect-input
output_bucket_name  ocr-perfect-output
project             ocr-perfect
region              us-central1
worker_sa_email     ocr-worker@ocr-perfect.iam.gserviceaccount.com
```

---

## Cost Considerations

- **Pulumi:** Using local backend (free, no account needed)
- **GitHub Actions:** Free for public repos, 2000 min/month for private
- **GCP:** All services have free tiers, estimated $0-5/month for low usage
