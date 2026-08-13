import hashlib
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.models.database import DocumentModel, DocumentChunkModel, IngestionJobModel

from app.models.internal import Document, DocumentChunk
from app.loaders.factory import LoaderFactory
from app.ingestion.normalizer import DocumentNormalizer
from app.ingestion.chunker import ConfigurableChunker
from app.vectorstore.chroma_store import ChromaVectorStore
from app.core.logging import logger
from app.core.errors import Load2AskException


class IngestionPipeline:
    """
    Complete end-to-end multi-source ingestion pipeline:
    Source -> Loader -> Normalization -> Chunking -> Metadata -> Embedding -> ChromaDB & SQL DB.
    """

    def __init__(self, db: Session, vector_store: Optional[ChromaVectorStore] = None):
        self.db = db
        self.vector_store = vector_store or ChromaVectorStore()
        self.normalizer = DocumentNormalizer()
        self.chunker = ConfigurableChunker()

    def prepare_document_job(self, document_id: str) -> IngestionJobModel:
        """Create and record an initial pending IngestionJob in DB."""
        job = IngestionJobModel(
            document_id=document_id,
            status="PENDING",
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        logger.info(f"Prepared IngestionJob {job.id} for document {document_id}")
        return job

    def process_document(self, document_id: str) -> IngestionJobModel:
        """
        Execute full ingestion pipeline for a document_id:
        1. Fetch document from SQL DB
        2. Execute appropriate loader
        3. Normalize document content
        4. Check for duplicates using content sha256 hash
        5. Split into configurable chunks
        6. Add embeddings to ChromaDB vector store
        7. Persist DocumentChunk records in SQL DB
        8. Update IngestionJob status to COMPLETED (or FAILED on error)
        """
        doc_model = self.db.query(DocumentModel).filter(DocumentModel.id == document_id).first()
        if not doc_model:
            raise Load2AskException(f"Document {document_id} not found in database.")

        job = self.db.query(IngestionJobModel).filter(IngestionJobModel.document_id == document_id).order_by(IngestionJobModel.started_at.desc()).first()
        if not job:
            job = self.prepare_document_job(document_id)

        job.status = "PROCESSING"
        job.started_at = datetime.now(timezone.utc)
        doc_model.status = "PROCESSING"
        self.db.commit()

        try:
            # 1. Load document using LoaderFactory
            source = doc_model.source_uri or doc_model.filename
            if doc_model.source_type == "web":
                loader = LoaderFactory.get_loader("web")
            else:
                loader = LoaderFactory.get_loader_for_file(doc_model.filename)

            raw_doc: Document = loader.load(source, metadata=dict(doc_model.doc_metadata or {}))
            raw_doc.id = doc_model.id

            # 2. Normalize content
            norm_doc: Document = self.normalizer.normalize(raw_doc)

            # Update Document title & metadata in DB if available
            if norm_doc.metadata.get("title"):
                doc_model.title = norm_doc.metadata["title"]

            content_hash = hashlib.sha256(norm_doc.content.encode("utf-8")).hexdigest()
            meta = dict(doc_model.doc_metadata or {})
            meta["content_hash"] = content_hash
            doc_model.doc_metadata = meta
            flag_modified(doc_model, "doc_metadata")

            # 3. Duplicate detection
            existing_doc = (
                self.db.query(DocumentModel)
                .filter(DocumentModel.id != document_id)
                .filter(DocumentModel.status == "COMPLETED")
                .all()
            )
            is_duplicate = False
            for prev in existing_doc:
                if prev.doc_metadata and prev.doc_metadata.get("content_hash") == content_hash:
                    logger.info(f"Duplicate document detected! Matches document {prev.id}")
                    is_duplicate = True
                    meta["duplicate_of"] = prev.id
                    doc_model.doc_metadata = meta
                    flag_modified(doc_model, "doc_metadata")
                    break


            # 4. Chunk document
            chunks: List[DocumentChunk] = self.chunker.chunk_document(norm_doc)
            logger.info(f"Document {document_id} split into {len(chunks)} chunks.")

            # 5. Clear previous chunks if any
            self.db.query(DocumentChunkModel).filter(DocumentChunkModel.document_id == document_id).delete()
            self.vector_store.delete_document(document_id)

            # 6. Add to Vector Store & SQL DB
            if chunks:
                self.vector_store.add_documents(chunks)

                db_chunks = []
                for chunk in chunks:
                    db_chunk = DocumentChunkModel(
                        id=chunk.id,
                        document_id=document_id,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        chunk_metadata=chunk.metadata
                    )
                    db_chunks.append(db_chunk)

                self.db.add_all(db_chunks)

            # 7. Update Job & Document status to COMPLETED
            job.status = "COMPLETED"
            job.completed_at = datetime.now(timezone.utc)
            doc_model.status = "COMPLETED"
            self.db.commit()
            self.db.refresh(job)
            logger.info(f"IngestionJob {job.id} completed successfully for document {document_id}.")
            return job

        except Exception as e:
            self.db.rollback()
            logger.error(f"Ingestion failed for document {document_id}: {e}")
            job.status = "FAILED"
            job.error = str(e)
            job.completed_at = datetime.now(timezone.utc)
            doc_model.status = "FAILED"
            self.db.commit()
            return job
