# TTS/STT Platform Monorepo

## Overview
The repository now provides the foundational scaffold for an enterprise-ready Text-to-Speech (TTS) and Speech-to-Text (STT) platform. It is organized as a monorepo so that backend services, machine learning microservices, frontend applications, infrastructure tooling, and documentation can evolve together in a consistent manner.

## High-Level Architecture
- **Backend API (Node.js + Express + TypeScript):** Serves as the main entry point for clients and other systems. It surfaces health and version endpoints today, and will host future orchestration logic connecting storage, queues, billing, and ML pipelines.
- **ML Services (Python + FastAPI):** Dedicated microservices for TTS and STT workloads. Each exposes basic health, initialization, and inference-style endpoints that will later connect to actual models.
- **Frontend (React + Vite + TypeScript):** A lightweight dashboard that validates end-to-end connectivity and provides a base for future operator and customer-facing experiences.
- **Infra (Docker, Docker Compose, nginx, k8s stubs coming later):** Container definitions for every service plus supporting databases and caches. Local developers can run everything via a single compose file.

## Repository Layout
```
backend/     → Node.js + Express + TypeScript API service
ml-service/  → Python FastAPI microservices for TTS & STT with shared config stubs
frontend/    → React + Vite + TypeScript dashboard
infra/       → Dockerfiles, docker-compose stack, nginx config, and Kubernetes manifest stubs
docs/        → Platform documentation & onboarding guides
first        → Legacy placeholder file retained for history
```

## Running Services Locally (without Docker)
### Backend API
```bash
cd backend
npm install
npm run dev
# Server listens on http://localhost:4000 by default
```

### TTS Service
```bash
cd ml-service/tts-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8001
```

### STT Service
```bash
cd ml-service/stt-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload --port 8002
```

### Frontend Dashboard
```bash
cd frontend
npm install
npm run dev
# Vite dev server runs on http://localhost:5173
```

Use the `.env.example` files inside `backend/` and `frontend/` as references for local configuration.

## Database & Prisma (Phase 2)
Phase 2 introduces the full persistence layer via Prisma + PostgreSQL. All schema definitions live in `backend/prisma/schema.prisma` and the generated SQL migration is committed under `backend/prisma/migrations/`.

Common commands:
```bash
cd backend
npm install
# Generate Prisma client
npm run prisma:generate
# Apply migrations to your local DB
npm run prisma:migrate
# Seed a default org + owner account
npm run prisma:seed
```
The seed step will create an `Acme Corp` organization with an owner account (`owner@acme.dev` / `ChangeMe123!`) and two baseline ML model rows so status endpoints return data. Update the corresponding `SEED_*` environment variables if you want to customize credentials.

## Auth & Security
- **JWT login** – `POST /api/v1/auth/login` accepts email/password (and an optional `orgSlug` if the same email exists in multiple orgs) and returns a Bearer token. Include it via `Authorization: Bearer <token>` for any dashboard/admin route.
- **API keys** – Owners/Admins can manage keys under `/api/v1/auth/api-keys`. Keys are shown once at creation time, hashed in the DB, and can be scoped to `tts` and/or `stt`. Supply them via the `x-api-key` header when calling job endpoints server-to-server.
- **RBAC** – Middleware enforces roles for sensitive operations (e.g., model reloads, API key management, voice cloning). Rate limiting is applied per org/API key with configurable windows in `.env`.

## REST API Endpoints (Phase 2)
All endpoints share the `/api/v1` prefix. Full OpenAPI docs are hosted at `http://localhost:4000/api/v1/docs` once the backend is running.

### TTS
| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/tts/synthesize` | JWT or API key (scope `tts`) | Synchronously synthesize text to speech. Returns job metadata plus audio URL.
| POST | `/tts/synthesize-batch` | JWT or API key (scope `tts`) | Submit multiple synthesis requests in one payload.
| GET | `/tts/voices` | JWT | List the organization’s voice profiles.
| POST | `/tts/voice-clone` | JWT (owner/admin/developer) | Upload a sample (`audio_sample`) to create a training voice profile. Audio is stored via the S3/MinIO adapter.

Sample cURL:
```bash
curl -X POST http://localhost:4000/api/v1/tts/synthesize \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "language": "en-US"}'
```

### STT
| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| POST | `/stt/transcribe` | JWT or API key (scope `stt`) | Upload a single audio file (`audio_file`) for transcription.
| POST | `/stt/batch-transcribe` | JWT or API key (scope `stt`) | Send multiple files (`audio_files`) and receive per-job IDs.
| POST | `/stt/transcribe-realtime` | JWT or API key (scope `stt`) | REST stub returning `501` until the realtime WebSocket endpoint ships in Phase 5.

### ML Model Management
| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/models/status` | JWT | Returns all ML models plus health from the FastAPI services.
| POST | `/models/reload` | JWT (owner/admin) | Calls `initialize` on both ML services and updates model rows.

### Analytics
| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/analytics/usage` | JWT | Aggregated usage (total TTS chars, STT seconds, daily rollups for the last 30 days).

Swagger definitions describe request/response shapes; refer to them for full field-level documentation.

## Running the Full Stack with Docker Compose
```bash
docker-compose -f infra/docker/docker-compose.dev.yml up --build
```
This command launches PostgreSQL, Redis, both ML services, the backend API, and the frontend dashboard. Once the containers are running you can check:
- Backend health: http://localhost:4000/health
- TTS service health: http://localhost:8001/ml/tts/health
- STT service health: http://localhost:8002/ml/stt/health
- Frontend dashboard: http://localhost:5173

The compose file wires service discovery (e.g., backend ↔ ML services) via container names, so cross-service health checks will work out of the box. Stop the stack with `Ctrl+C` or `docker-compose … down`.
