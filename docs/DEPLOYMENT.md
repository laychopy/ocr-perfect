# OCR Perfect - Deployment Guide

This document describes the complete deployment process for OCR Perfect, including the backend API on Cloud Run and the frontend on Firebase Hosting.

## Live URLs

- **Frontend:** https://ocr-perfect.web.app
- **Backend API:** https://ocr-perfect-backend-276562330509.us-central1.run.app
- **API Docs:** https://ocr-perfect-backend-276562330509.us-central1.run.app/docs

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Firebase Hosting)                   │
│                    https://ocr-perfect.web.app                   │
│                                                                  │
│   ┌────────────┐    ┌────────────┐    ┌────────────┐           │
│   │   Login    │───▶│  Dashboard │───▶│   Upload   │           │
│   │  (Google)  │    │  (Jobs)    │    │   (PDF)    │           │
│   └────────────┘    └────────────┘    └────────────┘           │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Backend API (Cloud Run)                         │
│      https://ocr-perfect-backend-xxx.us-central1.run.app        │
│                                                                  │
│   ┌────────────┐    ┌────────────┐    ┌────────────┐           │
│   │  FastAPI   │───▶│  Firebase  │───▶│  Services  │           │
│   │   Routes   │    │    Auth    │    │ (GCP SDK)  │           │
│   └────────────┘    └────────────┘    └────────────┘           │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Google Cloud Platform                         │
│                                                                  │
│   ┌────────────┐    ┌────────────┐    ┌────────────┐           │
│   │   Cloud    │    │ Firestore  │    │  Pub/Sub   │           │
│   │  Storage   │    │ (Jobs DB)  │    │ (Queue)    │           │
│   └────────────┘    └────────────┘    └────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Infrastructure as Code (Pulumi)

All GCP infrastructure is managed with Pulumi. See `infra/__main__.py`.

### Resources Managed by Pulumi

| Resource | Name | Description |
|----------|------|-------------|
| Storage Bucket | `ocr-perfect-input` | Uploaded PDFs (30 day lifecycle) |
| Storage Bucket | `ocr-perfect-output` | Processed results (30 day lifecycle) |
| Firestore DB | `(default)` | Job tracking database |
| Pub/Sub Topic | `ocr-jobs` | Job processing queue |
| Pub/Sub Topic | `ocr-jobs-dlq` | Dead letter queue |
| Artifact Registry | `ocr-perfect` | Docker images repository |
| Cloud Run Service | `ocr-perfect-backend` | Backend API |
| Service Account | `ocr-backend` | Backend API permissions |
| Service Account | `ocr-worker` | Worker job permissions |
| 12 APIs | Various | Required GCP services |

### Pulumi Commands

```bash
cd infra

# Preview changes
PULUMI_CONFIG_PASSPHRASE="" pulumi preview

# Apply changes
PULUMI_CONFIG_PASSPHRASE="" pulumi up --yes

# View current state
PULUMI_CONFIG_PASSPHRASE="" pulumi stack output

# Destroy all resources (DANGER!)
PULUMI_CONFIG_PASSPHRASE="" pulumi destroy --yes
```

---

## Backend Deployment

### Manual Deployment Steps

1. **Build and push Docker image:**
   ```bash
   cd backend
   gcloud builds submit --tag us-central1-docker.pkg.dev/ocr-perfect/ocr-perfect/backend:v3 .
   ```

2. **Deploy to Cloud Run (done by Pulumi or manually):**
   ```bash
   gcloud run deploy ocr-perfect-backend \
     --image us-central1-docker.pkg.dev/ocr-perfect/ocr-perfect/backend:v3 \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars "GCP_PROJECT=ocr-perfect" \
     --set-env-vars "GCP_REGION=us-central1" \
     --set-env-vars "INPUT_BUCKET=ocr-perfect-input" \
     --set-env-vars "OUTPUT_BUCKET=ocr-perfect-output" \
     --set-env-vars "PUBSUB_TOPIC=ocr-jobs" \
     --set-env-vars "ALLOWED_ORIGINS_STR=https://ocr-perfect.web.app;https://ocr-perfect.firebaseapp.com;http://localhost:5173" \
     --service-account ocr-backend@ocr-perfect.iam.gserviceaccount.com
   ```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GCP_PROJECT` | GCP project ID |
| `GCP_REGION` | GCP region |
| `INPUT_BUCKET` | Bucket for uploaded files |
| `OUTPUT_BUCKET` | Bucket for processed files |
| `PUBSUB_TOPIC` | Pub/Sub topic for jobs |
| `ALLOWED_ORIGINS_STR` | CORS origins (semicolon-separated) |

**Note:** Use semicolons (`;`) to separate CORS origins, not commas. Commas conflict with gcloud CLI argument parsing.

---

## Frontend Deployment

### Manual Deployment Steps

1. **Set API URL:**
   ```bash
   cd frontend
   echo "VITE_API_URL=https://ocr-perfect-backend-276562330509.us-central1.run.app" > .env
   ```

2. **Build:**
   ```bash
   npm install
   npm run build
   ```

3. **Deploy to Firebase Hosting:**
   ```bash
   cd ..  # project root
   firebase deploy --only hosting
   ```

### Firebase Configuration

Firebase Hosting configuration in `firebase.json`:
```json
{
  "hosting": {
    "public": "frontend/dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ]
  }
}
```

---

## Troubleshooting

### Cloud Run Container Fails to Start

**Symptom:** "The user-provided container failed to start and listen on the port"

**Common causes:**
1. **Configuration parsing error** - Check that environment variables are correctly formatted
2. **Missing dependencies** - Ensure all required packages are in requirements.txt
3. **Port mismatch** - Container must listen on PORT=8080

**Check logs:**
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ocr-perfect-backend" --limit=20
```

### Pydantic-Settings JSON Parsing Error

**Symptom:** `json.decoder.JSONDecodeError: Expecting value`

**Cause:** pydantic-settings tries to JSON-parse list fields from environment variables.

**Solution:** Use string fields with computed properties:
```python
# Instead of:
allowed_origins: list[str] = [...]

# Use:
allowed_origins_str: str = "url1;url2;url3"

@computed_field
@property
def allowed_origins(self) -> list[str]:
    return [x.strip() for x in self.allowed_origins_str.split(";") if x.strip()]
```

### gcloud --set-env-vars Syntax Error

**Symptom:** "Bad syntax for dict arg" when setting env vars with commas

**Cause:** gcloud interprets commas as key-value separators

**Solutions:**
1. Use multiple `--set-env-vars` flags
2. Use a different separator in values (semicolons work)
3. Use `--env-vars-file` with a YAML file

---

## Deployment Checklist

- [ ] Infrastructure is up (`pulumi up`)
- [ ] Docker image built and pushed
- [ ] Cloud Run service deployed
- [ ] Frontend built with correct API URL
- [ ] Firebase Hosting deployed
- [ ] Google Sign-In works
- [ ] API endpoints accessible
- [ ] CORS configured correctly

---

## Quick Commands Reference

```bash
# Full deployment from scratch
cd infra && PULUMI_CONFIG_PASSPHRASE="" pulumi up --yes
cd ../backend && gcloud builds submit --tag us-central1-docker.pkg.dev/ocr-perfect/ocr-perfect/backend:v3 .
cd ../frontend && npm run build && cd .. && firebase deploy --only hosting

# Check backend health
curl https://ocr-perfect-backend-276562330509.us-central1.run.app/

# View Pulumi outputs
cd infra && PULUMI_CONFIG_PASSPHRASE="" pulumi stack output
```
