from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from app.models.internal import DocumentChunk


class VectorStore(ABC):
    """Abstract vector store interface for Load2Ask architecture."""

    @abstractmethod
    def add_documents(self, chunks: List[DocumentChunk]) -> None:
        """Add a list of document chunks to the vector database."""
        pass

    @abstractmethod
    def similarity_search(
        self, query: str, k: int = 4, filter: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """Perform a similarity search using a query string."""
        pass

    @abstractmethod
    def delete_document(self, document_id: str) -> None:
        """Delete all chunks associated with a specific document_id."""
        pass

    @abstractmethod
    def get_document(self, document_id: str) -> List[DocumentChunk]:
        """Retrieve all stored vector chunks for a specific document_id."""
        pass
