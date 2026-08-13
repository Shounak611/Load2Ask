import hashlib
import math
from typing import List, Optional
from app.embeddings.base import EmbeddingProvider
from app.core.config import settings
from app.core.logging import logger


class DefaultEmbeddingProvider(EmbeddingProvider):
    """
    Production-grade lightweight embedding provider.
    Uses Google Gemini API or lazy-loaded SentenceTransformer, with fallback to feature vectorizer.
    Zero heavy top-level imports to ensure ultra-low memory footprint (<50MB RAM) on server boot.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", dimension: int = 384):
        self.model_name = model_name
        self.dimension = dimension
        self._model = None
        self._model_attempted = False
        self._use_gemini = False

    def _get_model(self):
        """Lazy-load embedding models on demand to maintain low memory footprint during app startup."""
        if not self._model_attempted:
            self._model_attempted = True

            # 1. Try Google Gemini API if key is present
            if (
                settings.LLM_API_KEY
                and settings.LLM_API_KEY not in ["your_google_gemini_api_key_here", "default_llm_key"]
            ):
                try:
                    import google.generativeai as genai
                    genai.configure(api_key=settings.LLM_API_KEY)
                    self._use_gemini = True
                    logger.info("Using Google Gemini API for lightweight cloud embeddings.")
                    return None
                except Exception as e:
                    logger.warning(f"Gemini embedding setup error: {e}")

            # 2. Lazy load SentenceTransformer locally if available
            try:
                from sentence_transformers import SentenceTransformer
                import torch
                torch.set_num_threads(1)
                logger.info(f"Lazy loading SentenceTransformer model: {self.model_name}")
                self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.warning(
                    f"Could not load SentenceTransformer model {self.model_name}: {e}. "
                    "Falling back to hash-based vectorizer."
                )
                self._model = None

        return self._model

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

    def _embed_gemini(self, text: str) -> Optional[List[float]]:
        """Embed text using Google Gemini Embedding API."""
        try:
            import google.generativeai as genai
            res = genai.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="retrieval_document"
            )
            embedding = res.get("embedding", [])
            # Truncate or pad to self.dimension
            if len(embedding) > self.dimension:
                return embedding[:self.dimension]
            elif len(embedding) < self.dimension:
                return embedding + [0.0] * (self.dimension - len(embedding))
            return embedding
        except Exception as e:
            logger.warning(f"Gemini API embedding failed: {e}. Falling back...")
            return None

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        model = self._get_model()

        if self._use_gemini:
            results = []
            for t in texts:
                emb = self._embed_gemini(t)
                results.append(emb if emb is not None else self._fallback_embed(t))
            return results

        if model is not None:
            try:
                embeddings = model.encode(texts, convert_to_numpy=True)
                return embeddings.tolist()
            except Exception as e:
                logger.error(f"Error embedding documents with SentenceTransformer: {e}")

        return [self._fallback_embed(t) for t in texts]

    def embed_query(self, text: str) -> List[float]:
        model = self._get_model()

        if self._use_gemini:
            emb = self._embed_gemini(text)
            if emb is not None:
                return emb

        if model is not None:
            try:
                embedding = model.encode(text, convert_to_numpy=True)
                return embedding.tolist()
            except Exception as e:
                logger.error(f"Error embedding query with SentenceTransformer: {e}")

        return self._fallback_embed(text)
