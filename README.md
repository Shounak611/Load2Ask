# Load2Ask — Production-Grade Multimodal RAG & Context Engineering Platform

**Load2Ask** is a state-of-the-art, enterprise-ready Multimodal Retrieval-Augmented Generation (RAG) platform built with FastAPI, React + Vite, Neon PostgreSQL, Qdrant Cloud vector database, and Google Gemini LLMs.

Designed for sub-second retrieval performance, lost-in-the-middle context reordering, reciprocal rank fusion (RRF), cross-encoder re-ranking, and real-time streaming citations.

---

## Production Deployment Architecture

```text
                       INTERNET
                           │
                           ▼
                 ┌──────────────────┐
                 │      VERCEL      │
                 │ React + Vite     │
                 │ TypeScript       │
                 └────────┬─────────┘
                          │
                          │ HTTPS API (VITE_API_URL)
                          ▼
                 ┌──────────────────┐
                 │      RENDER      │
                 │ FastAPI          │
                 │ RAG Engine       │
                 │ Context Engine   │
                 │ Loaders          │
                 └───────┬───┬──────┘
                         │   │
             PostgreSQL  │   │ Vector Search
                         │   │
                         ▼   ▼
                    ┌──────┐ ┌─────────┐
                    │ NEON │ │ QDRANT  │
                    │ PGSQL│ │  CLOUD  │
                    └──────┘ └─────────┘
                         │
                         │
                         ▼
                  LLM / Embeddings
```

### Production Tech Stack
* **Frontend:** Vercel (React + Vite + TypeScript + Tailwind CSS)
* **Backend API:** Render (FastAPI + Uvicorn + Python 3.10+)
* **Relational Database:** Neon PostgreSQL (SQLAlchemy + Alembic Migrations)
* **Vector Store:** Qdrant Cloud (`qdrant-client`)
* **LLM Provider:** Google Gemini API
* **File Storage:** StorageProvider Abstraction (Ephemeral / AWS S3 Object Storage)

---

## Step-by-Step Production Deployment Guide

### Step 1: Create Neon PostgreSQL Database
1. Sign up at [Neon.tech](https://neon.tech) and create a new project (e.g. `load2ask-db`).
2. Copy the PostgreSQL Connection String (`DATABASE_URL`).
   Example:
   ```text
   postgresql://user:password@ep-sample-123456.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

### Step 2: Create Qdrant Cloud Cluster
1. Sign up at [Qdrant Cloud](https://cloud.qdrant.io/) and create a free tier cluster.
2. Note your **Cluster URL** (`QDRANT_URL`) and generate an **API Key** (`QDRANT_API_KEY`).
   Example:
   ```text
   QDRANT_URL=https://your-qdrant-cluster-id.us-east-1-0.aws.cloud.qdrant.io:6333
   QDRANT_API_KEY=your_qdrant_api_key
   QDRANT_COLLECTION=load2ask_documents
   ```

### Step 3: Deploy Backend to Render
1. Sign up at [Render.com](https://render.com) and create a **New Web Service**.
2. Connect your Git repository.
3. Configure service properties:
   * **Root Directory:** `backend`
   * **Build Command:** `pip install -r requirements.txt && alembic upgrade head`
   * **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   * **Health Check Path:** `/api/health`
4. Set Environment Variables on Render:
   * `ENVIRONMENT` = `production`
   * `DATABASE_URL` = `<your_neon_connection_string>`
   * `VECTOR_STORE_PROVIDER` = `qdrant`
   * `QDRANT_URL` = `<your_qdrant_cluster_url>`
   * `QDRANT_API_KEY` = `<your_qdrant_api_key>`
   * `QDRANT_COLLECTION` = `load2ask_documents`
   * `LLM_API_KEY` = `<your_google_gemini_api_key>`
   * `CORS_ORIGINS` = `https://<your-vercel-app>.vercel.app`
   * `FRONTEND_URL` = `https://<your-vercel-app>.vercel.app`
   * `STORAGE_PROVIDER` = `local` (or `s3`)

### Step 4: Deploy Frontend to Vercel
1. Sign up at [Vercel.com](https://vercel.com) and import your repository.
2. Select Root Directory as `frontend`.
3. Vercel automatically detects Vite settings:
   * **Build Command:** `npm run build`
   * **Output Directory:** `dist`
4. Add Environment Variable in Vercel settings:
   * `VITE_API_URL` = `https://<your-render-service>.onrender.com`
5. Deploy.

### Step 5: Configure CORS
Ensure `CORS_ORIGINS` in Render backend settings contains your exact Vercel production URL:
```text
CORS_ORIGINS=https://load2ask.vercel.app
```

### Step 6: Run Database Migrations
Database migrations execute automatically during the Render build phase via:
```bash
alembic upgrade head
```

### Step 7: Verify Qdrant Collection Initialization
The backend automatically verifies and creates the Qdrant collection (`load2ask_documents`) with cosine distance and vector dimensions matching your embedding model upon startup.

### Step 8: Test Complete Production Flow
Visit your Vercel deployment URL to test document ingestion, Qdrant vector retrieval, conversational chat, SSE streaming, and citations.

---

## Local Development Setup

### 1. Local Environment Setup
```bash
cp .env.example .env
```

### 2. Run with Docker Compose
```bash
docker compose up --build -d
```
* **Frontend App:** `http://localhost:3000`
* **Backend API Docs:** `http://localhost:8000/docs`
* **Qdrant Dashboard:** `http://localhost:6333/dashboard`

---

## Testing & Quality Assurance

Run the automated test suite:
```bash
.venv/bin/pytest backend/tests -v
```

Run RAG Benchmark Evaluation CLI:
```bash
python scripts/run_eval.py --top-k 25 --rerank-k 10 --context-budget 4000
```
