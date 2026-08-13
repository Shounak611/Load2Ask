import re
from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session
from rank_bm25 import BM25Okapi

from app.models.database import DocumentChunkModel
from app.models.internal import DocumentChunk


class BM25Retriever:
    """Lexical keyword retriever using BM25Okapi over stored document chunks."""

    def __init__(self, db: Session):
        self.db = db

    def tokenize(self, text: str) -> List[str]:
        """Simple lowercase word tokenization."""
        return re.findall(r'\b\w+\b', text.lower())

    def search(
        self,
        query: str,
        top_k: int = 20,
        filter_doc_id: Optional[str] = None,
        filter_page: Optional[int] = None,
        filter_source_type: Optional[str] = None
    ) -> List[Tuple[DocumentChunk, float]]:
        """Perform BM25 search over database chunks matching metadata constraints."""
        db_query = self.db.query(DocumentChunkModel)

        if filter_doc_id:
            db_query = db_query.filter(DocumentChunkModel.document_id == filter_doc_id)

        db_chunks = db_query.all()
        if not db_chunks:
            return []

        # Apply in-memory metadata filtering if constraints are present
        filtered_chunks = []
        for c in db_chunks:
            meta = c.chunk_metadata or {}
            if filter_page is not None and meta.get("page_number") != filter_page:
                continue
            if filter_source_type is not None and meta.get("source_type") != filter_source_type:
                continue
            filtered_chunks.append(c)

        if not filtered_chunks:
            filtered_chunks = db_chunks

        # Tokenize corpus and initialize BM25
        corpus = [self.tokenize(c.content) for c in filtered_chunks]
        tokenized_query = self.tokenize(query)

        if not tokenized_query or not any(corpus):
            return []

        bm25 = BM25Okapi(corpus)
        scores = bm25.get_scores(tokenized_query)

        # Pair chunks with scores
        scored_results: List[Tuple[DocumentChunk, float]] = []
        for i, score in enumerate(scores):
            if score > 0.0:
                c_model = filtered_chunks[i]
                internal_chunk = DocumentChunk(
                    id=c_model.id,
                    document_id=c_model.document_id,
                    content=c_model.content,
                    chunk_index=c_model.chunk_index,
                    metadata=dict(c_model.chunk_metadata or {})
                )
                scored_results.append((internal_chunk, float(score)))

        # Sort by score descending and return top_k
        scored_results.sort(key=lambda x: x[1], reverse=True)
        return scored_results[:top_k]
