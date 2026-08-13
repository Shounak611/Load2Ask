# Load2Ask: Multimodal RAG + Context Engineering Platform

Load2Ask is a production-grade, modular Multimodal Retrieval-Augmented Generation (RAG) and Context Engineering platform backend.

---

## 🏗️ Architecture Overview

The system is built with a modular, decoupled architecture rather than a simplistic pipeline wrapper:

```
backend/
├── app/
│   ├── api/          # FastAPI routers and REST endpoints (health, documents)
│   ├── core/         # Settings configuration, logging, and centralized error handling
│   ├── database/     # SQLAlchemy engine, session management, and DB initialization
│   ├── models/       # Database ORM models & Internal data models (Document, Chunk)
│   ├── schemas/      # Pydantic API schemas
│   ├── loaders/      # Document Loader Registry (Factory, TXT, PDF, Image, Web, etc.)
│   ├── embeddings/   # Abstract Embedding Provider & Default SentenceTransformer Provider
│   ├── vectorstore/  # Abstract VectorStore Interface & ChromaDB Implementation
│   ├── services/     # Core business domain services (Document management, storage)
│   ├── ingestion/    # Document ingestion pipeline & job management
│   ├── retrieval/    # Modular retrieval interface (Part 2+)
│   ├── ranking/      # Reranking interface (Part 3+)
│   ├── context/      # Context engineering interface (Part 4+)
│   ├── llm/          # Abstract LLM Provider interface (Part 3+)
│   └── main.py       # FastAPI application entrypoint
├── tests/            # Pytest test suite
├── Dockerfile        # Backend container configuration
├── requirements.txt  # Python package dependencies
frontend/             # Placeholder for React/Vite/TS frontend (Part 2+)
scripts/              # Database migration and initialization scripts
docker-compose.yml    # Compose file for Backend, PostgreSQL, and ChromaDB
.env.example          # Environment variable template
```

---

## 🚀 Quickstart Guide

### 1. Environment Setup

Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 2. Local Python Environment

Create a virtual environment and install dependencies:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

### 3. Initialize Database

Run the DB init script (supports PostgreSQL or fallback SQLite):
```bash
python scripts/init_db.py
```

### 4. Start Backend Server

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation will be accessible at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 🐳 Docker Deployment

To spin up the entire backend stack (PostgreSQL + ChromaDB + FastAPI backend):

```bash
docker-compose up --build -d
```

Services:
- **FastAPI Backend**: `http://localhost:8000`
- **PostgreSQL**: `localhost:5432`
- **ChromaDB**: `http://localhost:8001`

---

## 🧪 Running Tests

Execute the automated test suite with pytest:

```bash
PYTHONPATH=backend .venv/bin/pytest backend/tests -v
```

---

## 📌 API Endpoints Summary (Part 1 Foundation)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | System health check (API, Database, Vector Store) |
| `POST` | `/api/documents/upload` | Upload document, validate format, store file, create Document and IngestionJob records |
| `GET` | `/api/documents` | List uploaded documents with pagination |
| `GET` | `/api/documents/{id}` | Get document metadata and chunk stats |
| `DELETE` | `/api/documents/{id}` | Delete document, disk file, and associated vector embeddings |

---

## 📑 Next Steps (Part 2 Scope)

- Full text chunking strategies & background ingestion pipeline worker
- Complete implementation of remaining document loaders (Image, DOCX, PPTX, CSV, XLSX, JSON, Markdown, HTML, Web URL)
- React + Vite + TypeScript + Tailwind CSS Frontend UI
