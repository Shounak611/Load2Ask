from app.embeddings.base import EmbeddingProvider
from app.embeddings.default_embedding import DefaultEmbeddingProvider
from app.core.config import settings


class EmbeddingFactory:
    """Factory for instantiating vector embedding providers."""

    @staticmethod
    def get_embedding_provider(provider_type: str = None) -> EmbeddingProvider:
        provider = provider_type or settings.EMBEDDING_PROVIDER
        # Currently defaults to DefaultEmbeddingProvider (SentenceTransformer / fallback)
        # Additional providers like OpenAI, Cohere, HuggingFace API can be registered here.
        return DefaultEmbeddingProvider()
