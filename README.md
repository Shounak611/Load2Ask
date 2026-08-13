# Load2Ask — Production-Grade Multimodal RAG & Context Engineering Platform

**Load2Ask** is a state-of-the-art, enterprise-ready Multimodal Retrieval-Augmented Generation (RAG) platform built with FastAPI, Python 3.10+, SQLite/PostgreSQL, ChromaDB vector store, and Google Gemini LLMs.

Designed for reliability, security, observability, and sub-second retrieval performance, Load2Ask supports multi-document query processing, multi-turn conversational query resolution, hybrid retrieval (dense + lexical BM25), reciprocal rank fusion (RRF), cross-encoder re-ranking, lost-in-the-middle context reordering, and an automated evaluation framework.

---

## Key Features & Architecture

```
[ Upload / URL ] → [ SSRF & Mime Guard ] → [ Multimodal Extractors ]
                                                   ↓
[ Citation Tracking ] ← [ LLM Generation ] ← [ Context Engine ]
                                                   ↑
                                      [ Hybrid Retrieval (Dense + BM25) ]
                                                   ↑
                                    [ Query Analyzer & Expansion ]
```

### Core Architecture Components
1. **Multimodal Document Loaders**: Secure extraction for PDF, TXT, OCR Images (PNG/JPG/JPEG), Website URLs (with SSRF protection), DOCX, PPTX, CSV, XLSX, JSON, and Markdown.
2. **Chunking & Storage**: Token-aware text chunking with configurable overlap, stored in ChromaDB (dense vectors) and SQL DB (PostgreSQL / SQLite metadata & job management).
3. **Conversational Query Intelligence**: Multi-turn entity extraction resolving pronouns (*it, its, that*) and comparative expressions (*which one is faster*) using recent conversation history.
4. **Hybrid Retrieval**: Dense vector similarity search combined with BM25 keyword matching via Reciprocal Rank Fusion (RRF) and metadata score boosting.
5. **Cross-Encoder Re-ranking & Deduplication**: Secondary semantic re-ranking for top candidates followed by cosine/Jaccard similarity deduplication.
6. **Context Engine & Token Budgeting**: Lost-in-the-middle context reordering (placing high-relevance chunks at context boundaries) and strict LLM token window budgeting.
7. **Observability & Telemetry**: Structured JSON logging capturing step-by-step latencies, chunk counts, token usage, and automatic sensitive credential redaction.
8. **Evaluation Framework**: Built-in benchmark evaluation suite tracking **Precision@K**, **Recall@K**, **MRR**, **Answer Relevance**, **Faithfulness**, and **Citation Correctness**.

---

## Quick Start (Local Development)

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (optional for containerized deployment)

### 2. Environment Setup
Create a `.env` file in the root directory:
```env
LLM_API_KEY=your_google_gemini_api_key
EMBEDDING_API_KEY=your_embedding_api_key
DATABASE_URL=sqlite:///./load2ask.db
VECTOR_DB_URL=./chroma_db
VECTOR_COLLECTION=load2ask_collection
UPLOAD_DIRECTORY=./uploads
CHUNK_SIZE=700
CHUNK_OVERLAP=100
MAX_FILE_SIZE_MB=50

RETRIEVAL_TOP_K=25
RERANK_TOP_K=10
CONTEXT_TOKEN_LIMIT=4000
DENSE_WEIGHT=0.6
LEXICAL_WEIGHT=0.4
RELEVANCE_THRESHOLD=0.15
DEDUPLICATION_THRESHOLD=0.82
```

### 3. Install Dependencies & Initialize Database
```bash
# Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

# Run Alembic Database Migrations
cd backend
alembic upgrade head
cd ..
```

### 4. Run Backend Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --app-dir backend
```

### 5. Run Frontend Development Server
```bash
cd frontend
npm install
npm run dev
```
Navigate to `http://localhost:5173` (or `http://localhost:3000` via Nginx).

---

## Deployment with Docker Compose

To deploy the entire production stack (Frontend, Backend, PostgreSQL, ChromaDB):

```bash
# Build and start all services
docker compose up --build -d

# Check service health
docker compose ps
```

Service endpoints:
- **Frontend App**: `http://localhost:3000`
- **Backend API Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/api/health`

---

## API Reference

### Health Check
- `GET /api/health`: Returns health status of Backend API, Database, Vector Store, and Configuration.

### Document Management
- `POST /api/documents/upload`: Upload file (PDF, TXT, Image, DOCX, PPTX, CSV, XLSX, JSON, MD).
- `POST /api/documents/ingest-url`: Ingest external website URL (protected against SSRF).
- `GET /api/documents`: List ingested documents.
- `GET /api/documents/{id}/status`: Track document parsing and vector indexing status.
- `DELETE /api/documents/{id}`: Cascade delete document, chunks, and vector embeddings.

### RAG Query & Streaming
- `POST /api/query`: Execute full RAG pipeline returning JSON response with citations and debug info.
- `POST /api/query/stream`: Server-Sent Events (SSE) streaming RAG responses for real-time frontend token rendering.

### Evaluation Framework
- `POST /api/eval/run?top_k=25&rerank_k=10&context_budget=4000`: Run automated RAG evaluation over benchmark test dataset.

Or via CLI:
```bash
python scripts/run_eval.py --top-k 25 --rerank-k 10 --context-budget 4000
```

---

## Evaluation Metrics

The evaluation framework measures 6 core quality metrics:
- **Precision@K**: Proportion of top-K retrieved sources that are relevant.
- **Recall@K**: Proportion of ground-truth sources retrieved in top-K.
- **MRR (Mean Reciprocal Rank)**: Reciprocal rank of the first relevant retrieved source.
- **Answer Relevance**: Semantic/Jaccard similarity between generated answer and ground truth.
- **Faithfulness**: Fact-checking metric measuring grounding of generated statements in retrieved context.
- **Citation Correctness**: Verification of cited source documents against ground truth sources.

---

## Security & Reliability Controls

- **SSRF Protection**: `WebLoader` blocks internal IP ranges (127.0.0.1, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, AWS metadata IPs) and dangerous protocols.
- **File Security**: Extension whitelist validation, path traversal prevention (`resolve()` checking), null-byte removal, filename sanitization, and 50MB file size limit.
- **API Protection**: Rate-limiting middleware (60 reqs/min per IP) and optional API Key headers (`X-API-Key`).
- **Observability**: Structured JSON logging with automatic redaction of sensitive credentials (`api_key`, `password`, `secret`, `auth_token`).

---

## Testing

Run the full pytest suite:
```bash
pytest backend/tests -v
```

All 35 unit & integration tests verify end-to-end functionality across loaders, chunkers, hybrid retrieval, re-ranking, context budgeting, and API endpoints.
