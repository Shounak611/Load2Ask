from typing import Optional
from app.vectorstore.base import VectorStore
from app.vectorstore.qdrant_store import QdrantVectorStore
from app.vectorstore.chroma_store import ChromaVectorStore
from app.core.config import settings
from app.core.logging import logger


class VectorStoreFactory:
    """Factory for selecting and instantiating the appropriate VectorStore implementation."""

    @staticmethod
    def get_vector_store(provider: Optional[str] = None) -> VectorStore:
        provider_name = (provider or settings.VECTOR_STORE_PROVIDER or "qdrant").lower()

        if provider_name == "qdrant":
            logger.info("Initializing QdrantVectorStore via factory.")
            return QdrantVectorStore()
        elif provider_name == "chroma":
            logger.info("Initializing ChromaVectorStore via factory.")
            return ChromaVectorStore()
        else:
            logger.warning(f"Unknown vector store provider '{provider_name}'. Defaulting to QdrantVectorStore.")
            return QdrantVectorStore()
