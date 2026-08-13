from typing import List, Tuple, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.internal import DocumentChunk
from app.vectorstore.base import VectorStore
from app.vectorstore.factory import VectorStoreFactory
from app.retrieval.bm25 import BM25Retriever
from app.retrieval.query_analyzer import AnalyzedQuery
from app.core.logging import logger


class HybridRetriever:
    """Combines Dense Vector Retrieval and BM25 Lexical Retrieval with metadata filtering."""

    def __init__(self, db: Session, vector_store: Optional[VectorStore] = None):
        self.db = db
        self.vector_store = vector_store or VectorStoreFactory.get_vector_store()
        self.bm25_retriever = BM25Retriever(db)


    def retrieve(
        self,
        analyzed_query: AnalyzedQuery,
        top_k: int = 25,
        alpha: float = 0.6,
        beta: float = 0.4,
        filter_doc_id: Optional[str] = None
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Hybrid retrieval combining Dense Vector Search and Lexical BM25 Search.
        Applies metadata constraints (document_id, page_number, source_type).
        """
        query_str = analyzed_query.rewritten_query
        constraints = analyzed_query.constraints

        doc_id_filter = filter_doc_id or constraints.document_id
        page_filter = constraints.page_number
        stype_filter = constraints.source_type

        # 1. Dense Vector Retrieval
        dense_results: List[DocumentChunk] = []
        try:
            dense_results = self.vector_store.similarity_search(
                query=query_str,
                k=top_k,
                filter_doc_id=doc_id_filter
            )
        except Exception as e:
            logger.warning(f"Dense vector retrieval failed: {e}")

        # 2. BM25 Lexical Retrieval
        bm25_tuples: List[Tuple[DocumentChunk, float]] = []
        try:
            bm25_tuples = self.bm25_retriever.search(
                query=query_str,
                top_k=top_k,
                filter_doc_id=doc_id_filter,
                filter_page=page_filter,
                filter_source_type=stype_filter
            )
        except Exception as e:
            logger.warning(f"BM25 retrieval failed: {e}")

        # 3. Reciprocal Rank Fusion (RRF) & Normalized Scoring
        chunk_map: Dict[str, DocumentChunk] = {}
        rrf_scores: Dict[str, float] = {}
        k_rrf = 60

        # Process Dense results
        for rank, chunk in enumerate(dense_results, start=1):
            chunk_map[chunk.id] = chunk
            rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + alpha * (1.0 / (k_rrf + rank))

        # Process BM25 results
        for rank, (chunk, bm_score) in enumerate(bm25_tuples, start=1):
            chunk_map[chunk.id] = chunk
            rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + beta * (1.0 / (k_rrf + rank))

        # Metadata constraint boosting: if chunk metadata matches page_number constraint, add boost score
        for chunk_id, chunk in chunk_map.items():
            meta = chunk.metadata or {}
            if page_filter is not None and meta.get("page_number") == page_filter:
                rrf_scores[chunk_id] *= 1.5

        # Sort combined candidate list
        combined = [(chunk_map[cid], rrf_scores[cid]) for cid in rrf_scores]
        combined.sort(key=lambda x: x[1], reverse=True)

        logger.info(f"Hybrid retrieval returned {len(combined)} candidate chunks for query: '{query_str}'")
        return combined[:top_k]
