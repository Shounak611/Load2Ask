from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.models.internal import DocumentChunk


class BaseContextEngine(ABC):
    """Abstract context engineering interface for context compression, windowing, and citation formatting."""

    @abstractmethod
    def build_context(self, chunks: List[DocumentChunk], max_tokens: int = 2048) -> Dict[str, Any]:
        pass
