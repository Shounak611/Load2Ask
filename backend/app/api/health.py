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
    """Health check endpoint for checking API, Database, and Vector Store connectivity."""
    db_status = "ok"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = f"unhealthy: {str(e)}"

    vector_status = "ok"
    try:
        vs = ChromaVectorStore()
        # Verify collection works
        vs.collection.count()
    except Exception as e:
        logger.error(f"Vector store health check failed: {e}")
        vector_status = f"unhealthy: {str(e)}"

    overall_status = "ok" if (db_status == "ok" and vector_status == "ok") else "degraded"

    return HealthCheckResponse(
        status=overall_status,
        version="1.0.0",
        database=db_status,
        vector_store=vector_status,
        details={
            "environment": settings.ENVIRONMENT,
            "vector_collection": settings.VECTOR_COLLECTION,
            "upload_dir": settings.UPLOAD_DIRECTORY,
        }
    )
