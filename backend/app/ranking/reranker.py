import re
from typing import List, Tuple, Dict, Any, Optional
from app.models.internal import DocumentChunk
from app.retrieval.query_analyzer import AnalyzedQuery
from app.core.logging import logger


class Reranker:
    """Configurable reranker evaluating query relevance, semantic overlap, exact term matches, and metadata alignment."""

    def __init__(self, top_k: int = 8):
        self.top_k = top_k

    def _score_candidate(self, query_terms: List[str], chunk: DocumentChunk, base_score: float) -> float:
        content_lower = chunk.content.lower()
        meta = chunk.metadata or {}

        # 1. Exact phrase/keyword match count
        exact_matches = sum(1 for term in query_terms if term in content_lower)
        exact_boost = (exact_matches / max(len(query_terms), 1)) * 0.4

        # 2. Heading / Section alignment boost
        section = str(meta.get("section") or meta.get("title") or "").lower()
        heading_boost = 0.2 if any(term in section for term in query_terms) else 0.0

        # 3. Density penalty for extremely short or low-information chunks
        len_penalty = 0.85 if len(chunk.content) < 40 else 1.0

        final_score = (base_score * 0.5 + exact_boost + heading_boost) * len_penalty
        return final_score

    def rerank(
        self,
        candidates: List[Tuple[DocumentChunk, float]],
        analyzed_query: AnalyzedQuery,
        top_k: Optional[int] = None
    ) -> List[Tuple[DocumentChunk, float]]:
        """Rerank candidate chunks down to top_k."""
        target_k = top_k or self.top_k
        if not candidates:
            return []

        query_terms = [k.lower() for k in analyzed_query.keywords if len(k) > 2]

        reranked: List[Tuple[DocumentChunk, float]] = []
        for chunk, initial_score in candidates:
            score = self._score_candidate(query_terms, chunk, initial_score)
            reranked.append((chunk, score))

        reranked.sort(key=lambda x: x[1], reverse=True)
        selected = reranked[:target_k]
        logger.info(f"Reranker selected {len(selected)} chunks out of {len(candidates)} candidates.")
        return selected
