# Backend & Frontend Implementation Plan

## Overview

This document outlines the implementation plan for the OCR Perfect web application:
- **Backend:** FastAPI on Cloud Run
- **Frontend:** React + Vite on Firebase Hosting

---

## Phase 1: Backend API (FastAPI)

### 1.1 Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Environment configuration
│   ├── dependencies.py      # Dependency injection (auth, db)
│   ├── auth/
│   │   ├── __init__.py
│   │   └── firebase.py      # Firebase token verification
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── health.py        # Health check endpoint
│   │   ├── jobs.py          # Job CRUD endpoints
│   │   └── files.py         # Upload/download endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py       # Pydantic models
│   └── services/
│       ├── __init__.py
│       ├── storage.py       # Cloud Storage operations
│       ├── firestore.py     # Firestore operations
│       └── pubsub.py        # Pub/Sub publishing
├── requirements.txt
├── Dockerfile
└── .env.example
```

### 1.2 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/health` | Health check | No |
| POST | `/api/upload` | Upload PDF, create job | Yes |
| GET | `/api/jobs` | List user's jobs | Yes |
| GET | `/api/jobs/{id}` | Get job details | Yes |
| GET | `/api/jobs/{id}/download` | Get signed download URL | Yes |
| DELETE | `/api/jobs/{id}` | Delete job and files | Yes |

### 1.3 Data Models

```python
# Job Status
class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# Job Model (Firestore)
class Job:
    id: str
    user_id: str
    status: JobStatus
    input_file: str          # gs://bucket/path
    output_file: str | None  # gs://bucket/path (when completed)
    filename: str            # Original filename
    file_size: int           # Bytes
    page_count: int | None   # After processing
    output_format: str       # docx, json, txt
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    error_message: str | None
```

### 1.4 Authentication Flow

```
Frontend                    Backend                     Firebase
   │                           │                           │
   │  1. Google Sign-In        │                           │
   │ ─────────────────────────────────────────────────────>│
   │                           │                           │
   │  2. ID Token              │                           │
   │ <─────────────────────────────────────────────────────│
   │                           │                           │
   │  3. API Request + Token   │                           │
   │ ─────────────────────────>│                           │
   │                           │  4. Verify Token          │
   │                           │ ─────────────────────────>│
   │                           │                           │
   │                           │  5. User Info             │
   │                           │ <─────────────────────────│
   │                           │                           │
   │  6. Response              │                           │
   │ <─────────────────────────│                           │
```

### 1.5 Upload Flow

```
1. Frontend sends POST /api/upload with PDF file
2. Backend verifies Firebase token
3. Backend generates signed upload URL for Cloud Storage
4. Backend creates job document in Firestore (status: pending)
5. Backend publishes message to Pub/Sub (job_id)
6. Backend returns job_id to frontend
7. Worker picks up job from Pub/Sub
8. Worker updates status to "processing"
9. Worker processes PDF
10. Worker uploads result to Cloud Storage
11. Worker updates status to "completed"
```

### 1.6 Dependencies

```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.6
firebase-admin>=6.4.0
google-cloud-storage>=2.14.0
google-cloud-firestore>=2.14.0
google-cloud-pubsub>=2.19.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
python-dotenv>=1.0.0
```

---

## Phase 2: Frontend (React)

### 2.1 Project Structure

```
frontend/
├── src/
│   ├── main.tsx             # Entry point
│   ├── App.tsx              # Main app with routing
│   ├── lib/
│   │   ├── firebase.ts      # Firebase config (exists)
│   │   └── api.ts           # API client
│   ├── hooks/
│   │   ├── useAuth.ts       # Auth state hook
│   │   └── useJobs.ts       # Jobs data hook
│   ├── components/
│   │   ├── Layout.tsx       # Page layout
│   │   ├── Navbar.tsx       # Navigation
│   │   ├── ProtectedRoute.tsx
│   │   ├── FileUpload.tsx   # Drag & drop upload
│   │   ├── JobCard.tsx      # Job status card
│   │   └── JobList.tsx      # Jobs list
│   ├── pages/
│   │   ├── Login.tsx        # Login page
│   │   ├── Dashboard.tsx    # Jobs dashboard
│   │   ├── Upload.tsx       # Upload page
│   │   └── JobDetail.tsx    # Single job view
│   └── types/
│       └── index.ts         # TypeScript types
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

### 2.2 Pages

| Page | Route | Description |
|------|-------|-------------|
| Login | `/login` | Google Sign-In button |
| Dashboard | `/` | List of user's jobs |
| Upload | `/upload` | Upload new PDF |
| Job Detail | `/jobs/:id` | Job status and download |

### 2.3 Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **React Router** - Routing
- **Firebase SDK** - Auth & Firestore listeners
- **Axios** - HTTP client

### 2.4 Key Features

1. **Google Sign-In**
   - One-click login with Google
   - Persistent auth state

2. **File Upload**
   - Drag & drop support
   - File type validation (PDF only)
   - Size limit check (50MB)
   - Upload progress indicator

3. **Real-time Updates**
   - Firestore onSnapshot listeners
   - Job status updates in real-time
   - No polling needed

4. **Download**
   - Signed URLs for secure download
   - Multiple output formats

---

## Phase 3: Deployment

### 3.1 Backend to Cloud Run

```bash
# Build and push image
gcloud builds submit --tag gcr.io/ocr-perfect/backend

# Deploy to Cloud Run
gcloud run deploy ocr-backend \
  --image gcr.io/ocr-perfect/backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account ocr-backend@ocr-perfect.iam.gserviceaccount.com \
  --set-env-vars "GCP_PROJECT=ocr-perfect,INPUT_BUCKET=ocr-perfect-input,OUTPUT_BUCKET=ocr-perfect-output"
```

### 3.2 Frontend to Firebase Hosting

```bash
cd frontend
npm run build
firebase deploy --only hosting
```

---

## Implementation Order

### Week 1: Backend Core
1. [ ] FastAPI project setup
2. [ ] Firebase Auth middleware
3. [ ] Health check endpoint
4. [ ] Upload endpoint + Storage integration
5. [ ] Jobs CRUD + Firestore integration
6. [ ] Pub/Sub publishing
7. [ ] Dockerfile
8. [ ] Local testing

### Week 2: Frontend Core
1. [ ] Vite + React + TypeScript setup
2. [ ] Tailwind CSS configuration
3. [ ] Firebase Auth integration
4. [ ] Login page
5. [ ] Protected routes
6. [ ] Dashboard with job list
7. [ ] Upload page with drag & drop
8. [ ] Real-time job updates

### Week 3: Deployment & Integration
1. [ ] Deploy backend to Cloud Run
2. [ ] Configure CORS
3. [ ] Deploy frontend to Firebase Hosting
4. [ ] End-to-end testing
5. [ ] Add to Pulumi (Cloud Run service)

---

## Environment Variables

### Backend (.env)
```
GCP_PROJECT=ocr-perfect
INPUT_BUCKET=ocr-perfect-input
OUTPUT_BUCKET=ocr-perfect-output
PUBSUB_TOPIC=ocr-jobs
ALLOWED_ORIGINS=https://ocr-perfect.web.app,http://localhost:5173
```

### Frontend (.env)
```
VITE_API_URL=https://ocr-backend-xxxxx.run.app
VITE_FIREBASE_API_KEY=AIzaSyBQ_tNlu9w6Gr0oIq_f6kzKf0BBF_fZSvM
VITE_FIREBASE_AUTH_DOMAIN=ocr-perfect.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=ocr-perfect
```

---

## Security Considerations

1. **Authentication**
   - All API endpoints (except health) require valid Firebase token
   - Token verification on every request

2. **Authorization**
   - Users can only access their own jobs
   - Firestore rules enforce user isolation

3. **File Validation**
   - PDF only
   - Max size: 50MB
   - Virus scanning (optional, via Cloud Functions)

4. **CORS**
   - Whitelist only allowed origins
   - No wildcards in production

5. **Secrets**
   - No hardcoded credentials
   - Use Secret Manager for sensitive config
