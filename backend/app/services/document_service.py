from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from fastapi import UploadFile

from app.models.database import DocumentModel, IngestionJobModel, DocumentChunkModel
from app.schemas.document import DocumentResponse, DocumentStatusResponse
from app.services.storage_service import StorageService
from app.ingestion.pipeline import IngestionPipeline
from app.loaders.web_loader import validate_url_ssrf
from app.loaders.factory import LoaderFactory
from app.vectorstore.chroma_store import ChromaVectorStore
from app.core.errors import DocumentNotFoundError, InvalidFileError
from app.core.logging import logger


class DocumentService:
    """Service handling multi-source document ingestion (files, URLs) and lifecycle operations."""

    def __init__(self, db: Session):
        self.db = db
        self.storage_service = StorageService()
        self.ingestion_pipeline = IngestionPipeline(db=db)
        self.vector_store = ChromaVectorStore()

    def upload_single_file(self, file: UploadFile) -> Tuple[DocumentModel, IngestionJobModel]:
        """
        Validate single file, save to storage, create Document ORM record,
        create IngestionJob ORM record, and execute full ingestion pipeline.
        """
        if not file.filename:
            raise InvalidFileError("Uploaded file has no filename.")

        # Validate that a loader exists for this format
        try:
            LoaderFactory.get_loader_for_file(file.filename)
        except Exception as e:
            raise InvalidFileError(f"Validation failed for file '{file.filename}': {str(e)}")

        # Save file to disk
        file_path, original_filename, file_size = self.storage_service.save_upload_file(file)

        ext = file.filename.split(".")[-1].lower() if "." in file.filename else "unknown"
        doc = DocumentModel(
            filename=original_filename,
            source_type=ext,
            source_uri=file_path,
            title=original_filename,
            mime_type=file.content_type,
            file_size=file_size,
            status="PENDING",
            doc_metadata={"original_name": original_filename, "storage_path": file_path}
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        # Prepare & execute ingestion job
        job = self.ingestion_pipeline.prepare_document_job(doc.id)
        job = self.ingestion_pipeline.process_document(doc.id)

        return doc, job

    def upload_multiple_files(self, files: List[UploadFile]) -> Tuple[List[DocumentModel], List[Dict[str, Any]]]:
        """
        Process multiple files independently.
        One failed document must not abort or corrupt successful documents.
        """
        successful_docs: List[DocumentModel] = []
        failed_uploads: List[Dict[str, Any]] = []

        for file in files:
            try:
                doc, job = self.upload_single_file(file)
                if doc.status == "COMPLETED":
                    successful_docs.append(doc)
                else:
                    failed_uploads.append({
                        "filename": file.filename,
                        "error": job.error or "Ingestion pipeline processing failed."
                    })
            except Exception as e:
                logger.error(f"Failed to ingest file '{file.filename}': {e}")
                failed_uploads.append({
                    "filename": file.filename,
                    "error": str(e)
                })

        return successful_docs, failed_uploads

    def ingest_url(self, url: str) -> Tuple[DocumentModel, IngestionJobModel]:
        """
        Ingest a web URL with SSRF protection:
        1. SSRF validation
        2. Create Document record
        3. Execute ingestion pipeline (fetch -> clean HTML -> chunk -> embed -> ChromaDB)
        """
        validated_url = validate_url_ssrf(url)

        doc = DocumentModel(
            filename=validated_url,
            source_type="web",
            source_uri=validated_url,
            title=validated_url,
            mime_type="text/html",
            file_size=0,
            status="PENDING",
            doc_metadata={"url": validated_url}
        )
        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        job = self.ingestion_pipeline.prepare_document_job(doc.id)
        job = self.ingestion_pipeline.process_document(doc.id)

        return doc, job

    def get_document(self, document_id: str) -> DocumentModel:
        """Retrieve a Document record by ID."""
        doc = self.db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
        if not doc:
            raise DocumentNotFoundError(f"Document with ID '{document_id}' not found.")
        return doc

    def get_document_status(self, document_id: str) -> DocumentStatusResponse:
        """Get ingestion status, job progress, and chunk statistics for a document."""
        doc = self.get_document(document_id)
        job = (
            self.db.query(IngestionJobModel)
            .filter(IngestionJobModel.document_id == document_id)
            .order_by(IngestionJobModel.started_at.desc())
            .first()
        )
        chunk_count = self.db.query(DocumentChunkModel).filter(DocumentChunkModel.document_id == document_id).count()

        return DocumentStatusResponse(
            document_id=doc.id,
            document_status=doc.status,
            job_id=job.id if job else None,
            job_status=job.status if job else None,
            error=job.error if job else None,
            started_at=job.started_at if job else None,
            completed_at=job.completed_at if job else None,
            chunk_count=chunk_count,
        )

    def list_documents(self, skip: int = 0, limit: int = 50) -> Tuple[List[DocumentModel], int]:
        """Retrieve paginated document list and total count."""
        total = self.db.query(DocumentModel).count()
        documents = self.db.query(DocumentModel).offset(skip).limit(limit).all()
        return documents, total

    def delete_document(self, document_id: str) -> bool:
        """Delete document from database, local file storage, and vector store."""
        doc = self.get_document(document_id)

        if doc.source_uri and doc.source_type != "web":
            self.storage_service.delete_file(doc.source_uri)

        try:
            self.vector_store.delete_document(document_id)
        except Exception as e:
            logger.warning(f"Error deleting vectors for document {document_id}: {e}")

        self.db.delete(doc)
        self.db.commit()
        logger.info(f"Document {document_id} and associated resources deleted successfully.")
        return True
