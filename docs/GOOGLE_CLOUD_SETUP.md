# Google Cloud Project Setup

This document records the steps taken to set up the Google Cloud project for OCR Perfect.

## Project Details

- **Project ID:** `ocr-perfect`
- **Project Name:** OCR Perfect
- **Owner:** softwarelaycho@gmail.com
- **Created:** 2026-01-20

## Setup Steps

### 1. Authentication

Authenticated with personal Google account:

```bash
gcloud auth login
```

### 2. Project Creation

Created a new Google Cloud project:

```bash
gcloud projects create ocr-perfect --name="OCR Perfect"
```

### 3. Set Active Project

Set the new project as the active project:

```bash
gcloud config set project ocr-perfect
```

### 4. Link Billing Account

Linked an existing billing account to enable paid services:

```bash
gcloud billing projects link ocr-perfect --billing-account=019834-6925AA-369469
```

### 5. Enable Required APIs

Enabled all necessary APIs for the application:

```bash
gcloud services enable \
  cloudresourcemanager.googleapis.com \
  firebase.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  pubsub.googleapis.com \
  identitytoolkit.googleapis.com \
  --project=ocr-perfect
```

### Enabled APIs Summary

| API | Purpose |
|-----|---------|
| Cloud Resource Manager | Project management |
| Firebase | Firebase services integration |
| Firestore | NoSQL database for job tracking |
| Cloud Storage | PDF file storage (input/output) |
| Cloud Run | Backend API hosting |
| Cloud Build | Container image building |
| Artifact Registry | Container image storage |
| Pub/Sub | Message queue for background jobs |
| Identity Toolkit | Firebase Authentication backend |

## Firebase Setup

### 6. Install Firebase CLI

```bash
npm install -g firebase-tools
firebase login
```

### 7. Add Firebase to GCP Project

```bash
firebase projects:addfirebase ocr-perfect
```

### 8. Create Firestore Database

```bash
gcloud firestore databases create --location=us-central1 --project=ocr-perfect
```

- **Location:** us-central1
- **Mode:** Native (Firestore)
- **Free tier:** Enabled

### 9. Create Cloud Storage Buckets

```bash
gcloud storage buckets create gs://ocr-perfect-input --location=us-central1 --project=ocr-perfect
gcloud storage buckets create gs://ocr-perfect-output --location=us-central1 --project=ocr-perfect
```

| Bucket | Purpose |
|--------|---------|
| `ocr-perfect-input` | Uploaded PDF files |
| `ocr-perfect-output` | Processed results |

### 10. Create Firebase Web App

```bash
firebase apps:create WEB "OCR Perfect Web" --project=ocr-perfect
```

- **App ID:** `1:276562330509:web:1ea1e68e28ba8cb02973c4`
- **Display name:** OCR Perfect Web

### Firebase SDK Configuration

```javascript
const firebaseConfig = {
  projectId: "ocr-perfect",
  appId: "1:276562330509:web:1ea1e68e28ba8cb02973c4",
  storageBucket: "ocr-perfect.firebasestorage.app",
  apiKey: "AIzaSyBQ_tNlu9w6Gr0oIq_f6kzKf0BBF_fZSvM",
  authDomain: "ocr-perfect.firebaseapp.com",
  messagingSenderId: "276562330509",
};
```

### 11. Enable Google Sign-In (Manual Step)

1. Go to [Firebase Console](https://console.firebase.google.com/project/ocr-perfect/authentication/providers)
2. Click "Get started" on Authentication
3. Select "Google" as a sign-in provider
4. Enable it and configure the project support email
5. Save

## Resources Created

| Resource | ID/Name | Location |
|----------|---------|----------|
| GCP Project | `ocr-perfect` | - |
| Firestore DB | `(default)` | us-central1 |
| Storage Bucket | `ocr-perfect-input` | us-central1 |
| Storage Bucket | `ocr-perfect-output` | us-central1 |
| Firebase Web App | `1:276562330509:web:...` | - |

## Next Steps

1. Enable Google Sign-In in Firebase Console
2. Deploy Firestore rules
3. Deploy Storage rules
4. Set up Cloud Run backend
5. Deploy frontend to Firebase Hosting

## Useful Commands

```bash
# Check current project
gcloud config get-value project

# List enabled APIs
gcloud services list --enabled --project=ocr-perfect

# View project info
gcloud projects describe ocr-perfect
```
