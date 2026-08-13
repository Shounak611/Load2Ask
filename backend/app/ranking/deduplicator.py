from typing import List, Tuple, Set
from app.models.internal import DocumentChunk
from app.core.logging import logger


class Deduplicator:
    """Deduplication module removing exact duplicates, near-duplicates, and redundant context chunks."""

    @staticmethod
    def _jaccard_similarity(text1: str, text2: str) -> float:
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union)

    @classmethod
    def deduplicate(
        cls,
        items: List[Tuple[DocumentChunk, float]],
        similarity_threshold: float = 0.82
    ) -> List[Tuple[DocumentChunk, float]]:
        """Filter out duplicate and near-duplicate chunks based on Jaccard content similarity."""
        deduped: List[Tuple[DocumentChunk, float]] = []
        seen_contents: Set[str] = set()

        for chunk, score in items:
            normalized_content = chunk.content.strip().lower()

            # Exact duplicate check
            if normalized_content in seen_contents:
                continue

            # Near-duplicate Jaccard similarity check against already accepted chunks
            is_near_duplicate = False
            for existing_chunk, _ in deduped:
                sim = cls._jaccard_similarity(normalized_content, existing_chunk.content.strip().lower())
                if sim >= similarity_threshold:
                    is_near_duplicate = True
                    break

            if not is_near_duplicate:
                seen_contents.add(normalized_content)
                deduped.append((chunk, score))

        logger.info(f"Deduplicator reduced {len(items)} chunks to {len(deduped)} unique chunks.")
        return deduped
