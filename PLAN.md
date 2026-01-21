# OCR Perfect - Full Stack Plan

## Fase 0: Configuración de MCPs

### GitHub MCP Setup

1. **Crear Personal Access Token en GitHub:**
   - Ir a GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
   - Crear token con permisos: `repo`, `workflow`, `read:org`

2. **Instalar GitHub MCP en Claude Code:**
   ```bash
   claude mcp add github -e GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxxx -- npx -y @modelcontextprotocol/server-github
   ```

3. **Verificar conexión:**
   ```bash
   claude mcp list
   ```

### Google Cloud MCP Setup

1. **Requisitos previos:**
   - Tener `gcloud` CLI instalado
   - Estar autenticado: `gcloud auth login`
   - Tener un proyecto: `gcloud config set project PROJECT_ID`

2. **Instalar Google Cloud MCP:**
   ```bash
   claude mcp add gcloud -- npx -y @anthropic-ai/gcloud-mcp
   ```

   O el oficial de Google:
   ```bash
   claude mcp add gcloud -- npx -y @google-cloud/gcloud-mcp
   ```

---

## Fase 1: Crear Repositorio GitHub

Una vez configurado el MCP de GitHub:
- Crear repositorio `ocr-perfect` (o el nombre que prefieras)
- Inicializar con el código actual
- Configurar branch protection si es necesario

---

## Fase 2: Arquitectura Full Stack

### Visión General

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│              (Firebase Hosting / Cloud Run)                      │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  Login   │  │  Upload  │  │  Status  │  │ Download │        │
│  │  Google  │  │   PDF    │  │  Track   │  │  Result  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND API                                 │
│                    (Cloud Run)                                   │
│                                                                  │
│  POST /upload    GET /jobs/{id}    GET /download/{id}           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Firebase   │    │    Cloud     │    │   Firestore  │
│     Auth     │    │   Storage    │    │   (Jobs DB)  │
│              │    │              │    │              │
│ Google Sign  │    │ input/       │    │ job status   │
│    In        │    │ output/      │    │ user jobs    │
└──────────────┘    └──────────────┘    └──────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   BACKGROUND PROCESSOR                           │
│              (Cloud Run Jobs / Cloud Tasks)                      │
│                                                                  │
│  1. Download PDF from Storage                                    │
│  2. Run OCR Pipeline                                             │
│  3. Upload result to Storage                                     │
│  4. Update job status in Firestore                               │
│  5. (Optional) Send notification                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Componentes Detallados

#### 1. Autenticación (Firebase Auth)
- **Proveedor:** Google Sign-In
- **Flujo:** OAuth 2.0 con Firebase SDK
- **Almacenamiento:** Firebase maneja tokens automáticamente
- **Costo:** Gratis hasta 50k MAU

#### 2. Frontend (React + Vite)
- **Framework:** React 18 con TypeScript
- **UI:** Tailwind CSS + shadcn/ui (simple y moderno)
- **Hosting:** Firebase Hosting (gratis tier generoso)
- **Páginas:**
  - `/login` - Google Sign-In
  - `/dashboard` - Lista de trabajos del usuario
  - `/upload` - Subir PDF
  - `/job/:id` - Estado del trabajo + descarga

#### 3. Backend API (FastAPI en Cloud Run)
- **Framework:** FastAPI (Python, compatible con el pipeline)
- **Endpoints:**
  ```
  POST /api/upload          → Sube PDF, crea job, dispara procesamiento
  GET  /api/jobs            → Lista jobs del usuario
  GET  /api/jobs/{id}       → Estado de un job específico
  GET  /api/download/{id}   → URL firmada para descargar resultado
  ```
- **Auth:** Verificar Firebase ID token en cada request
- **Hosting:** Cloud Run (escala a 0 cuando no hay tráfico)

#### 4. Storage (Cloud Storage)
- **Buckets:**
  - `ocr-perfect-input/` - PDFs subidos
  - `ocr-perfect-output/` - Resultados procesados
- **Estructura:** `{user_id}/{job_id}/filename.pdf`
- **Lifecycle:** Auto-delete después de 30 días (configurable)

#### 5. Base de Datos (Firestore)
- **Colecciones:**
  ```
  users/{uid}
    - email
    - created_at
    - jobs_count

  jobs/{job_id}
    - user_id
    - status: "pending" | "processing" | "completed" | "failed"
    - input_file: "gs://bucket/path"
    - output_file: "gs://bucket/path" (cuando complete)
    - created_at
    - completed_at
    - error_message (si falla)
    - config: { preset, output_format, ... }
  ```

#### 6. Background Processing (Cloud Run Jobs)
- **Trigger:** Pub/Sub message cuando se crea un job
- **Proceso:**
  1. Recibe job_id via Pub/Sub
  2. Descarga PDF de Cloud Storage
  3. Ejecuta pipeline OCR
  4. Sube resultado a Cloud Storage
  5. Actualiza Firestore con status "completed"
- **Timeout:** Configurable (hasta 24h para PDFs grandes)
- **Retry:** Automático con backoff exponencial

#### 7. Notificaciones
- **Opción Simple:** Polling desde frontend cada 5s
- **Opción Mejor:** Firestore realtime listeners (ya incluido)
- **Opción Premium:** Firebase Cloud Messaging (push notifications)

---

## Fase 3: Estructura del Proyecto

```
ocr-pipeline/
├── src/ocr_perfect/          # Pipeline OCR (existente)
├── frontend/                  # Nueva carpeta
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── backend/                   # Nueva carpeta
│   ├── app/
│   │   ├── main.py           # FastAPI app
│   │   ├── auth.py           # Firebase auth verification
│   │   ├── routes/
│   │   ├── models/
│   │   └── services/
│   ├── requirements.txt
│   └── Dockerfile
├── worker/                    # Nueva carpeta
│   ├── main.py               # Cloud Run Job entry point
│   ├── requirements.txt
│   └── Dockerfile
├── infrastructure/            # Nueva carpeta
│   ├── terraform/            # O Pulumi si prefieres
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── firebase/
│       └── firebase.json
├── config/                    # Existente
├── tests/                     # Existente
└── pyproject.toml            # Existente
```

---

## Fase 4: Costos Estimados (Google Cloud)

| Servicio | Free Tier | Costo Adicional |
|----------|-----------|-----------------|
| Firebase Auth | 50k MAU gratis | $0.0055/MAU después |
| Firebase Hosting | 10GB storage, 360MB/día | $0.026/GB después |
| Cloud Run | 2M requests/mes gratis | $0.00002/request |
| Cloud Storage | 5GB gratis | $0.020/GB/mes |
| Firestore | 1GB storage, 50k reads/día | $0.18/100k reads |
| Cloud Run Jobs | 240k vCPU-seconds gratis | $0.000024/vCPU-second |

**Para uso personal/bajo volumen: $0-5/mes**

---

## Fase 5: Plan de Implementación

### Sprint 1: Infraestructura Base
1. [ ] Configurar MCPs (GitHub + Google Cloud)
2. [ ] Crear repositorio en GitHub
3. [ ] Crear proyecto en Google Cloud
4. [ ] Configurar Firebase (Auth + Hosting + Firestore)
5. [ ] Crear buckets en Cloud Storage

### Sprint 2: Backend API
1. [ ] Crear FastAPI app básica
2. [ ] Implementar autenticación con Firebase
3. [ ] Endpoints: upload, jobs list, job status
4. [ ] Integración con Cloud Storage
5. [ ] Integración con Firestore
6. [ ] Dockerfile y deploy a Cloud Run

### Sprint 3: Background Worker
1. [ ] Crear Cloud Run Job
2. [ ] Configurar Pub/Sub trigger
3. [ ] Integrar pipeline OCR
4. [ ] Manejo de errores y retry
5. [ ] Actualización de status en Firestore

### Sprint 4: Frontend
1. [ ] Setup React + Vite + TypeScript
2. [ ] Implementar Firebase Auth (Google Sign-In)
3. [ ] Página de upload con drag & drop
4. [ ] Dashboard con lista de jobs
5. [ ] Vista de job con status realtime
6. [ ] Descarga de resultados
7. [ ] Deploy a Firebase Hosting

### Sprint 5: Pipeline OCR (Original)
1. [ ] Implementar módulos pendientes del pipeline
2. [ ] Tests de integración
3. [ ] Optimización de performance

---

## Decisiones Pendientes

Antes de empezar, necesito confirmar:

1. **Nombre del proyecto en Google Cloud:** ¿Usar `ocr-perfect` o tienes otro?

2. **Región preferida:**
   - `us-central1` (más barato)
   - `southamerica-east1` (São Paulo, más cercano)

3. **Formato de salida principal:**
   - DOCX (default)
   - JSON
   - PDF searchable
   - Múltiples opciones en UI?

4. **Límites de archivo:**
   - Tamaño máximo de PDF (¿50MB? ¿100MB?)
   - Páginas máximas por documento

5. **Retención de archivos:**
   - ¿Cuántos días guardar los PDFs y resultados?

---

## Referencias

- [GitHub MCP Server](https://github.com/github/github-mcp-server)
- [Google Cloud MCP](https://github.com/googleapis/gcloud-mcp)
- [Firebase Auth Docs](https://firebase.google.com/docs/auth)
- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [Claude Code MCP Docs](https://code.claude.com/docs/en/mcp)
