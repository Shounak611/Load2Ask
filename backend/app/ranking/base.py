from abc import ABC, abstractmethod
from typing import List
from app.models.internal import DocumentChunk


class BaseReranker(ABC):
    """Abstract reranker interface for cross-encoder or neural reranking."""

    @abstractmethod
    def rerank(self, query: str, chunks: List[DocumentChunk], top_n: int = 5) -> List[DocumentChunk]:
        pass
