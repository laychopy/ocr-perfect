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

### Pending
- [ ] Enable Google Sign-In in Firebase Console (manual step)
- [ ] Set up GitHub Actions for IaC deployment
- [ ] Implement Backend API (FastAPI + Cloud Run)
- [ ] Implement Background Worker (Cloud Run Jobs)
- [ ] Implement Frontend (React + Firebase Hosting)
- [ ] Implement OCR pipeline modules

---

## Project Status

**Completed foundations:**
- Geometry system (transforms, bboxes, coordinate spaces) - `src/ocr_perfect/geometry/`
- Intermediate Representation (models, ordering, provenance) - `src/ocr_perfect/ir/`
- Configuration system with presets - `src/ocr_perfect/config.py`
- Unit tests (~1,139 lines across 5 test files)

**Infrastructure completed:**
- Google Cloud Project: `ocr-perfect`
- Firestore database: us-central1
- Storage buckets: `ocr-perfect-input`, `ocr-perfect-output`
- Firebase Web App configured
- GitHub MCP connected
- GitHub repository: https://github.com/laychopy/ocr-perfect

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

## TODO - Web Application

### Backend API (FastAPI)
**Path:** `backend/`
**Status:** Pending

- FastAPI app with Firebase Auth verification
- Endpoints: upload, jobs list, job status, download
- Cloud Storage integration
- Firestore integration
- Dockerfile for Cloud Run

### Background Worker
**Path:** `worker/`
**Status:** Pending

- Cloud Run Job entry point
- Pub/Sub trigger configuration
- OCR pipeline integration
- Error handling and retry logic
- Status updates to Firestore

### Frontend (React)
**Path:** `frontend/`
**Status:** Pending

- React + Vite + TypeScript setup
- Firebase Auth (Google Sign-In)
- Upload page with drag & drop
- Dashboard with job list
- Real-time status updates
- Download results

---

## Implementation Order

1. ~~Infrastructure setup~~ (DONE)
2. Create GitHub repository
3. Backend API (FastAPI)
4. Frontend (React)
5. Background Worker (Cloud Run Jobs)
6. OCR Pipeline modules

---

## Architecture Notes

- All modules use the IR models from `src/ocr_perfect/ir/models.py`
- Coordinates flow through TransformChain for sub-pixel accuracy
- Configuration is managed via `AppConfig` with preset support
- Three coordinate spaces: PDF (72 DPI), RASTER, PREPROCESSED

## Google Cloud Resources (Managed by Pulumi)

| Resource | ID/Name | Location |
|----------|---------|----------|
| Project | `ocr-perfect` | - |
| Firestore | `(default)` | us-central1 |
| Storage | `ocr-perfect-input` | us-central1 |
| Storage | `ocr-perfect-output` | us-central1 |
| Pub/Sub Topic | `ocr-jobs` | - |
| Pub/Sub Topic | `ocr-jobs-dlq` | - |
| Service Account | `ocr-backend` | - |
| Service Account | `ocr-worker` | - |
| Firebase App | `1:276562330509:web:...` | - |

### Pulumi Commands
```bash
cd infra
PULUMI_CONFIG_PASSPHRASE="" pulumi up --yes      # Create
PULUMI_CONFIG_PASSPHRASE="" pulumi destroy --yes # Destroy
PULUMI_CONFIG_PASSPHRASE="" pulumi stack output  # View outputs
```

## Documentation

- `docs/GOOGLE_CLOUD_SETUP.md` - GCP & Firebase setup steps
- `docs/MCP_SETUP.md` - MCP server configuration
- `docs/GITHUB_SETUP.md` - GitHub repository setup
- `docs/INFRASTRUCTURE_AS_CODE.md` - Pulumi IaC plan with GitHub Actions
- `PLAN.md` - Full stack architecture plan
