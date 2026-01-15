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
