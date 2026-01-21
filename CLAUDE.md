# OCR Perfect - Implementation Plan

## Current Session Progress

### Completed
- [x] Authenticate gcloud with personal account
- [x] Create Google Cloud project (`ocr-perfect`)
- [x] Enable required GCP APIs
- [x] Link billing account
- [x] Configure Firebase (Auth + Firestore + Hosting)
- [x] Create Firestore database (us-central1)
- [x] Create Cloud Storage buckets (input/output)
- [x] Create Firebase Web App
- [x] Configure GitHub MCP
- [x] Create GitHub repository and push code
- [x] **Infrastructure as Code with Pulumi** (tested create/destroy cycle)
- [x] Enable Google Sign-In in Firebase Console
- [x] Backend API (FastAPI + Cloud Run) - DEPLOYED
- [x] Frontend (React + Firebase Hosting) - DEPLOYED

### Deployed URLs
- **Frontend:** https://ocr-perfect.web.app
- **Backend API:** https://ocr-perfect-backend-276562330509.us-central1.run.app
- **API Docs:** https://ocr-perfect-backend-276562330509.us-central1.run.app/docs

### Pending
- [ ] Set up GitHub Actions for automated deployment
- [ ] Implement Background Worker (Cloud Run Jobs)
- [ ] Implement OCR pipeline modules

---

## Project Status

**Completed foundations:**
- Geometry system (transforms, bboxes, coordinate spaces) - `src/ocr_perfect/geometry/`
- Intermediate Representation (models, ordering, provenance) - `src/ocr_perfect/ir/`
- Configuration system with presets - `src/ocr_perfect/config.py`
- Unit tests (~1,139 lines across 5 test files)

**Backend API (COMPLETED):**
- FastAPI app with CORS middleware
- Firebase Auth middleware for JWT verification
- Job management endpoints (upload, list, get, download, delete)
- Cloud Storage integration (signed URLs)
- Firestore integration (job CRUD)
- Pub/Sub integration (job queue)
- Deployed on Cloud Run

**Frontend App (COMPLETED):**
- React + Vite + TypeScript + Tailwind CSS
- Firebase Auth with Google Sign-In
- Login page with Google button
- Dashboard with upload and job list
- Real-time status updates (polling)
- Deployed on Firebase Hosting

**Infrastructure (COMPLETED):**
- Google Cloud Project: `ocr-perfect`
- Firestore database: us-central1
- Storage buckets: `ocr-perfect-input`, `ocr-perfect-output`
- Artifact Registry: `ocr-perfect`
- Cloud Run Service: `ocr-perfect-backend`
- Firebase Web App configured
- GitHub repository: https://github.com/laychopy/ocr-perfect
- All managed by Pulumi IaC

---

## Google Cloud Resources (Managed by Pulumi)

| Resource | ID/Name | Description |
|----------|---------|-------------|
| Project | `ocr-perfect` | Main project |
| Firestore | `(default)` | Jobs database |
| Storage | `ocr-perfect-input` | Uploaded PDFs |
| Storage | `ocr-perfect-output` | Processed files |
| Artifact Registry | `ocr-perfect` | Docker images |
| Cloud Run | `ocr-perfect-backend` | Backend API |
| Pub/Sub Topic | `ocr-jobs` | Job queue |
| Pub/Sub Topic | `ocr-jobs-dlq` | Dead letter queue |
| Service Account | `ocr-backend` | Backend permissions |
| Service Account | `ocr-worker` | Worker permissions |

### Pulumi Commands
```bash
cd infra
PULUMI_CONFIG_PASSPHRASE="" pulumi up --yes      # Create/Update
PULUMI_CONFIG_PASSPHRASE="" pulumi destroy --yes # Destroy
PULUMI_CONFIG_PASSPHRASE="" pulumi stack output  # View outputs
PULUMI_CONFIG_PASSPHRASE="" pulumi refresh --yes # Sync state
```

---

## TODO - OCR Pipeline Modules

### 1. Ingest Module
**Path:** `src/ocr_perfect/ingest/`
**Status:** Pending

- PDF loader using PyMuPDF
- Page iteration and rendering
- Vector text extraction from PDFs
- Trusted masking for MIXED PDFs
- Metadata extraction

### 2. Detection Module
**Path:** `src/ocr_perfect/detection/`
**Status:** Pending

- PDF type detection (TEXT, SCANNED, MIXED)
- Vector text coverage analysis
- Image content detection
- Text quality scoring
- Confidence thresholds for classification

### 3. Extraction Module
**Path:** `src/ocr_perfect/extraction/`
**Status:** Pending

- Vector text extraction from PDF objects
- Raster image extraction from pages
- Coordinate transformation to common space
- Font and styling information capture

### 4. Preprocessing Module
**Path:** `src/ocr_perfect/preprocessing/`
**Status:** Pending

- Deskew correction (Hough, projection, Tesseract methods)
- Denoise filters (NLM, bilateral, morphological)
- Contrast enhancement (CLAHE, histogram, gamma)
- Binarization (Otsu, adaptive, Sauvola)
- Image quality metrics

### 5. OCR Module
**Path:** `src/ocr_perfect/ocr/`
**Status:** Pending

- Tesseract OCR backend integration
- Google Document AI integration (optional)
- Google Cloud Vision integration (optional)
- Result parsing and confidence extraction
- Language support management
- Fallback backend logic

### 6. Layout Module
**Path:** `src/ocr_perfect/layout/`
**Status:** Pending

- Header/footer detection
- Column detection and multi-column handling
- Table detection (vector lines, raster morphology, ML, cloud)
- Region classification

### 7. Output Module
**Path:** `src/ocr_perfect/output/`
**Status:** Pending

- DOCX writer with formatting preservation
- JSON IR writer (per-page or full document)
- Searchable PDF generation
- hOCR output format
- Plain text writer

### 8. CLI and Pipeline
**Path:** `src/ocr_perfect/cli.py`, `src/ocr_perfect/pipeline.py`
**Status:** Pending

- Command-line interface (convert, batch, detect subcommands)
- Document processor orchestration
- Streaming page iteration
- Error handling and logging
- Progress reporting

---

## TODO - Background Worker

**Path:** `worker/`
**Status:** Pending

- Cloud Run Job entry point
- Pub/Sub trigger configuration
- OCR pipeline integration
- Error handling and retry logic
- Status updates to Firestore

---

## Documentation

- `docs/GOOGLE_CLOUD_SETUP.md` - GCP & Firebase setup steps
- `docs/MCP_SETUP.md` - MCP server configuration
- `docs/GITHUB_SETUP.md` - GitHub repository setup
- `docs/INFRASTRUCTURE_AS_CODE.md` - Pulumi IaC with tested workflows
- `docs/BACKEND_FRONTEND_PLAN.md` - Full stack architecture plan
- `docs/FIREBASE_AUTH_SETUP.md` - Google Sign-In configuration
- `docs/DEPLOYMENT.md` - Deployment guide and troubleshooting
- `PLAN.md` - Original architecture plan

---

## Quick Deployment Commands

```bash
# Full infrastructure
cd infra && PULUMI_CONFIG_PASSPHRASE="" pulumi up --yes

# Backend
cd backend && gcloud builds submit --tag us-central1-docker.pkg.dev/ocr-perfect/ocr-perfect/backend:v3 .

# Frontend
cd frontend && npm run build && cd .. && firebase deploy --only hosting

# Check backend
curl https://ocr-perfect-backend-276562330509.us-central1.run.app/
```
