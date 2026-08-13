import os
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.session import get_db
from app.schemas.health import HealthCheckResponse
from app.vectorstore.chroma_store import ChromaVectorStore
from app.core.config import settings
from app.core.logging import logger

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthCheckResponse, status_code=status.HTTP_200_OK)
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint checking Backend API, PostgreSQL, Vector DB, and System Configuration."""
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = f"unhealthy: {str(e)}"

    vector_status = "ok"
    try:
        vs = ChromaVectorStore()
        vs.collection.count()
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}")
        vector_status = f"unhealthy: {str(e)}"

    config_status = "ok"
    config_issues = []
    if not os.path.exists(settings.UPLOAD_DIRECTORY):
        config_issues.append(f"Upload directory '{settings.UPLOAD_DIRECTORY}' missing")

    if config_issues:
        config_status = f"warning: {', '.join(config_issues)}"

    overall_status = "ok" if (db_status == "ok" and vector_status == "ok" and config_status == "ok") else "degraded"

    return HealthCheckResponse(
        status=overall_status,
        version="1.0.0",
        database=db_status,
        vector_store=vector_status,
        configuration=config_status,
        details={
            "environment": settings.ENVIRONMENT,
            "vector_collection": settings.VECTOR_COLLECTION,
            "upload_dir": settings.UPLOAD_DIRECTORY,
            "chunk_size": settings.CHUNK_SIZE,
            "chunk_overlap": settings.CHUNK_OVERLAP,
            "retrieval_top_k": settings.RETRIEVAL_TOP_K,
            "rerank_top_k": settings.RERANK_TOP_K,
            "context_token_limit": settings.CONTEXT_TOKEN_LIMIT,
        }
    )

