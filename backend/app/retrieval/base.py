from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.models.internal import DocumentChunk


class BaseRetriever(ABC):
    """Abstract retriever interface for standard, hybrid, or multi-query retrieval."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5, filters: Dict[str, Any] = None) -> List[DocumentChunk]:
        pass
