from typing import List, Union
from fastapi import APIRouter, Depends, UploadFile, File, Query, status, Body
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.services.document_service import DocumentService
from app.schemas.document import (
    DocumentResponse, DocumentListResponse, URLIngestRequest,
    DocumentStatusResponse, MultiUploadResponse
)
from app.schemas.ingestion import IngestionJobResponse
from app.core.logging import logger

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_documents(
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload single or multiple document files for ingestion into the RAG vector store.
    Files are processed independently so that one failing document does not affect others.
    """
    service = DocumentService(db)
    successful_docs, failed_uploads = service.upload_multiple_files(files)

    success_responses = []
    for doc in successful_docs:
        resp = DocumentResponse.model_validate(doc)
        resp.chunk_count = len(doc.chunks)
        success_responses.append(resp)

    return MultiUploadResponse(
        message=f"Processed {len(files)} files: {len(successful_docs)} succeeded, {len(failed_uploads)} failed.",
        successful_uploads=success_responses,
        failed_uploads=failed_uploads,
    )


@router.post("/url", status_code=status.HTTP_201_CREATED)
def ingest_url(
    payload: URLIngestRequest,
    db: Session = Depends(get_db)
):
    """
    Ingest a web URL into the RAG system.
    Includes SSRF protection, main-content HTML cleaning, structure parsing, chunking, and embedding.
    """
    service = DocumentService(db)
    doc, job = service.ingest_url(payload.url)

    doc_response = DocumentResponse.model_validate(doc)
    doc_response.chunk_count = len(doc.chunks)

    return {
        "document": doc_response,
        "job": IngestionJobResponse.model_validate(job),
        "message": f"URL '{payload.url}' successfully fetched, cleaned, chunked, and embedded into vector store."
    }


@router.get("/{id}/status", response_model=DocumentStatusResponse, status_code=status.HTTP_200_OK)
def get_document_status(id: str, db: Session = Depends(get_db)):
    """Expose ingestion status, progress, error logs, and chunk statistics for a document."""
    service = DocumentService(db)
    return service.get_document_status(id)


@router.get("", response_model=DocumentListResponse, status_code=status.HTTP_200_OK)
def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """List documents with pagination."""
    service = DocumentService(db)
    docs, total = service.list_documents(skip=skip, limit=limit)

    response_docs = []
    for d in docs:
        resp = DocumentResponse.model_validate(d)
        resp.chunk_count = len(d.chunks)
        response_docs.append(resp)

    return DocumentListResponse(total=total, documents=response_docs)


@router.get("/{id}", response_model=DocumentResponse, status_code=status.HTTP_200_OK)
def get_document(id: str, db: Session = Depends(get_db)):
    """Get document details by document ID."""
    service = DocumentService(db)
    doc = service.get_document(id)
    resp = DocumentResponse.model_validate(doc)
    resp.chunk_count = len(doc.chunks)
    return resp


@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_document(id: str, db: Session = Depends(get_db)):
    """Delete document by ID from DB, disk storage, and vector store."""
    service = DocumentService(db)
    service.delete_document(id)
    return {"message": f"Document '{id}' deleted successfully.", "id": id}
