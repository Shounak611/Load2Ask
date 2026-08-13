import hashlib
import math
from typing import List
from app.embeddings.base import EmbeddingProvider
from app.core.logging import logger

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


class DefaultEmbeddingProvider(EmbeddingProvider):
    """
    Configurable embedding provider.
    Uses SentenceTransformer if available, or falls back to a deterministic feature vector generator.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", dimension: int = 384):
        self.model_name = model_name
        self.dimension = dimension
        self._model = None

        if SentenceTransformer is not None:
            try:
                logger.info(f"Initializing SentenceTransformer model: {model_name}")
                self._model = SentenceTransformer(model_name)
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer model {model_name}: {e}. Falling back to hash-based vectorizer.")

    def _fallback_embed(self, text: str) -> List[float]:
        """Generate a deterministic normalized vector based on character hash for testing/offline use."""
        vec = [0.0] * self.dimension
        words = text.lower().split()
        if not words:
            return vec

        for word in words:
            h = int(hashlib.sha256(word.encode('utf-8')).hexdigest(), 16)
            idx = h % self.dimension
            val = ((h >> 8) % 1000) / 1000.0 - 0.5
            vec[idx] += val

        # Normalize vector to unit length
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 1e-9:
            vec = [x / norm for x in vec]
        return vec

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        if self._model is not None:
            try:
                embeddings = self._model.encode(texts, convert_to_numpy=True)
                return embeddings.tolist()
            except Exception as e:
                logger.error(f"Error embedding documents with SentenceTransformer: {e}")

        return [self._fallback_embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        if self._model is not None:
            try:
                embedding = self._model.encode(text, convert_to_numpy=True)
                return embedding.tolist()
            except Exception as e:
                logger.error(f"Error embedding query with SentenceTransformer: {e}")

        return self._fallback_embed(text)
