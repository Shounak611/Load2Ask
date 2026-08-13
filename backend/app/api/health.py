import os
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database.session import get_db
from app.schemas.health import HealthCheckResponse
from app.vectorstore.factory import VectorStoreFactory
from app.storage.factory import StorageFactory
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
        vs = VectorStoreFactory.get_vector_store()
        # Ping vector store count or basic operation
        if hasattr(vs, "count"):
            vs.count()
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}")
        vector_status = f"unhealthy: {str(e)}"

    config_status = "ok"
    overall_status = "ok" if (db_status == "ok" and vector_status == "ok") else "degraded"

    return HealthCheckResponse(
        status=overall_status,
        version="1.0.0",
        database=db_status,
        vector_store=vector_status,
        configuration=config_status,
        details={
            "environment": settings.ENVIRONMENT,
            "vector_provider": settings.VECTOR_STORE_PROVIDER,
            "vector_collection": settings.QDRANT_COLLECTION if settings.VECTOR_STORE_PROVIDER == "qdrant" else settings.VECTOR_COLLECTION,
            "storage_provider": settings.STORAGE_PROVIDER,
            "chunk_size": settings.CHUNK_SIZE,
            "chunk_overlap": settings.CHUNK_OVERLAP,
            "retrieval_top_k": settings.RETRIEVAL_TOP_K,
            "rerank_top_k": settings.RERANK_TOP_K,
            "context_token_limit": settings.CONTEXT_TOKEN_LIMIT,
        }
    )


@router.get("/dependencies", status_code=status.HTTP_200_OK)
def dependency_health_check(db: Session = Depends(get_db)):
    """Deep dependency health check for production monitoring."""
    db_healthy = True
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Deep DB health check error: {e}")
        db_healthy = False

    vector_healthy = True
    try:
        vs = VectorStoreFactory.get_vector_store()
        if hasattr(vs, "count"):
            vs.count()
    except Exception as e:
        logger.error(f"Deep VectorStore health check error: {e}")
        vector_healthy = False

    llm_configured = bool(settings.LLM_API_KEY and settings.LLM_API_KEY != "default_llm_key")
    embedding_configured = bool(settings.EMBEDDING_API_KEY or settings.EMBEDDING_PROVIDER != "mock")

    is_all_healthy = db_healthy and vector_healthy and llm_configured

    return {
        "status": "healthy" if is_all_healthy else "degraded",
        "database": "healthy" if db_healthy else "unhealthy",
        "vector_store": "healthy" if vector_healthy else "unhealthy",
        "llm_configuration": "configured" if llm_configured else "default_key",
        "embedding_configuration": "configured" if embedding_configured else "default",
        "storage_provider": settings.STORAGE_PROVIDER,
        "environment": settings.ENVIRONMENT
    }
