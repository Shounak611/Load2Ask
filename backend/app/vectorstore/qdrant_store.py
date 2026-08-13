import uuid
from typing import List, Optional, Dict, Any
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

from app.vectorstore.base import VectorStore
from app.models.internal import DocumentChunk
from app.embeddings.base import EmbeddingProvider
from app.embeddings.factory import EmbeddingFactory
from app.core.config import settings
from app.core.errors import VectorStoreError
from app.core.logging import logger


_shared_in_memory_client: Optional[QdrantClient] = None


class QdrantVectorStore(VectorStore):
    """Production-grade Qdrant Cloud & Local Vector Store implementation."""

    def __init__(
        self,
        collection_name: Optional[str] = None,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
    ):
        self.collection_name = collection_name or settings.QDRANT_COLLECTION or "load2ask_documents"
        self.url = url or settings.QDRANT_URL
        self.api_key = api_key or settings.QDRANT_API_KEY
        self.embedding_provider = embedding_provider or EmbeddingFactory.get_embedding_provider()

        self.client = self._init_qdrant_client()
        self._ensure_collection_initialized()

    def _init_qdrant_client(self) -> QdrantClient:
        """Initialize Qdrant client for Cloud, Remote URL, Local Path, or Shared In-Memory."""
        global _shared_in_memory_client
        try:
            if self.url:
                if self.url.startswith("http://") or self.url.startswith("https://"):
                    logger.info(f"Connecting to remote Qdrant instance at '{self.url}'")
                    return QdrantClient(url=self.url, api_key=self.api_key)
                else:
                    logger.info(f"Connecting to local disk Qdrant instance at '{self.url}'")
                    return QdrantClient(path=self.url)
            else:
                # Shared local in-memory Qdrant client across requests for dev/tests
                if _shared_in_memory_client is None:
                    logger.info("QDRANT_URL not set; initializing shared in-memory Qdrant instance.")
                    _shared_in_memory_client = QdrantClient(location=":memory:")
                return _shared_in_memory_client
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant client: {e}")
            if _shared_in_memory_client is None:
                _shared_in_memory_client = QdrantClient(location=":memory:")
            return _shared_in_memory_client


    def _ensure_collection_initialized(self) -> None:
        """Check if collection exists; create with correct vector dimension & payload indexes if not."""
        try:
            exists = self.client.collection_exists(collection_name=self.collection_name)
            if not exists:
                # Sample 1 test query to determine vector dimension
                sample_embedding = self.embedding_provider.embed_query("test vector size check")
                vector_dim = len(sample_embedding)

                logger.info(
                    f"Creating Qdrant collection '{self.collection_name}' with vector dimension {vector_dim}"
                )
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=vector_dim,
                        distance=models.Distance.COSINE
                    )
                )

                # Create payload index for fast document_id and source_type filtering
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="document_id",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="source_type",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                logger.info(f"Qdrant collection '{self.collection_name}' created successfully with indexes.")
            else:
                logger.info(f"Qdrant collection '{self.collection_name}' already exists.")
        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection initialization: {e}")
            raise VectorStoreError(f"Failed to initialize Qdrant collection: {str(e)}")

    def _convert_id_to_uuid(self, chunk_id: str) -> str:
        """Ensure chunk ID is a valid UUID string for Qdrant compatibility."""
        try:
            return str(uuid.UUID(chunk_id))
        except ValueError:
            return str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk_id))

    def add_documents(self, chunks: List[DocumentChunk]) -> None:
        """Add document chunks to Qdrant vector store with full metadata preservation."""
        if not chunks:
            return

        try:
            texts = [chunk.content for chunk in chunks]
            embeddings = self.embedding_provider.embed_documents(texts)

            points = []
            for chunk, embedding in zip(chunks, embeddings):
                point_id = self._convert_id_to_uuid(chunk.id)
                meta = dict(chunk.metadata or {})

                # Ensure canonical metadata fields exist
                payload = {
                    "document_id": chunk.document_id,
                    "chunk_id": chunk.id,
                    "chunk_index": chunk.chunk_index,
                    "content": chunk.content,
                    "source_type": meta.get("source_type", "unknown"),
                    "source_name": meta.get("source_name") or meta.get("original_name") or "unknown",
                    "source_uri": meta.get("source_uri") or meta.get("storage_path") or "",
                    "page_number": meta.get("page_number"),
                    "section": meta.get("section"),
                    **meta
                }

                points.append(
                    models.PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload=payload
                    )
                )

            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Successfully upserted {len(chunks)} points to Qdrant collection '{self.collection_name}'")
        except Exception as e:
            logger.error(f"Failed to add documents to Qdrant: {e}")
            raise VectorStoreError(f"Failed to add documents to Qdrant vector store: {str(e)}")

    def similarity_search(
        self, query: str, k: int = 4, filter: Optional[Dict[str, Any]] = None, filter_doc_id: Optional[str] = None
    ) -> List[DocumentChunk]:
        """Perform similarity search on Qdrant vector store."""
        try:
            query_embedding = self.embedding_provider.embed_query(query)

            must_conditions = []
            target_doc_id = filter_doc_id or (filter.get("document_id") if filter else None)
            if target_doc_id:
                must_conditions.append(
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=target_doc_id)
                    )
                )

            if filter:
                for key, val in filter.items():
                    if key != "document_id" and val is not None:
                        must_conditions.append(
                            models.FieldCondition(
                                key=key,
                                match=models.MatchValue(value=val)
                            )
                        )

            query_filter = models.Filter(must=must_conditions) if must_conditions else None

            # Qdrant client search call (using query_points / search)
            if hasattr(self.client, "search"):
                try:
                    search_result = self.client.search(
                        collection_name=self.collection_name,
                        query_vector=query_embedding,
                        limit=k,
                        query_filter=query_filter
                    )
                except AttributeError:
                    res = self.client.query_points(
                        collection_name=self.collection_name,
                        query=query_embedding,
                        limit=k,
                        query_filter=query_filter
                    )
                    search_result = res.points
            else:
                res = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_embedding,
                    limit=k,
                    query_filter=query_filter
                )
                search_result = res.points

            chunks: List[DocumentChunk] = []
            for hit in search_result:
                payload = hit.payload or {}
                chunk_id = payload.get("chunk_id", str(hit.id))
                doc_id = payload.get("document_id", "")
                chunk_idx = payload.get("chunk_index", 0)
                content = payload.get("content", "")

                chunks.append(
                    DocumentChunk(
                        id=chunk_id,
                        document_id=doc_id,
                        chunk_index=chunk_idx,
                        content=content,
                        metadata=payload
                    )
                )
            return chunks

        except Exception as e:
            logger.error(f"Error performing similarity search in Qdrant store: {e}")
            raise VectorStoreError(f"Qdrant similarity search failed: {str(e)}")

    def delete_document(self, document_id: str) -> None:
        """Delete all vector points associated with document_id."""
        try:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="document_id",
                                match=models.MatchValue(value=document_id)
                            )
                        ]
                    )
                )
            )
            logger.info(f"Deleted Qdrant vector points for document_id={document_id}")
        except Exception as e:
            logger.error(f"Error deleting document {document_id} from Qdrant: {e}")
            raise VectorStoreError(f"Failed to delete document vectors from Qdrant: {str(e)}")

    def get_document(self, document_id: str) -> List[DocumentChunk]:
        """Retrieve all stored vector chunks for document_id."""
        try:
            scroll_result, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id)
                        )
                    ]
                ),
                limit=1000
            )

            chunks: List[DocumentChunk] = []
            for point in scroll_result:
                payload = point.payload or {}
                chunk_id = payload.get("chunk_id", str(point.id))
                chunk_idx = payload.get("chunk_index", 0)
                content = payload.get("content", "")

                chunks.append(
                    DocumentChunk(
                        id=chunk_id,
                        document_id=document_id,
                        chunk_index=chunk_idx,
                        content=content,
                        metadata=payload
                    )
                )
            # Sort by chunk_index
            chunks.sort(key=lambda c: c.chunk_index)
            return chunks
        except Exception as e:
            logger.error(f"Error getting document vectors for {document_id} from Qdrant: {e}")
            raise VectorStoreError(f"Failed to get document vectors from Qdrant: {str(e)}")

    def count(self) -> int:
        """Return point count in Qdrant collection."""
        try:
            res = self.client.get_collection(collection_name=self.collection_name)
            return res.points_count or 0
        except Exception as e:
            logger.error(f"Error getting point count from Qdrant: {e}")
            return 0
