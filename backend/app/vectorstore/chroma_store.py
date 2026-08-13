from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.vectorstore.base import VectorStore
from app.models.internal import DocumentChunk
from app.embeddings.base import EmbeddingProvider
from app.embeddings.factory import EmbeddingFactory
from app.core.config import settings
from app.core.errors import VectorStoreError
from app.core.logging import logger


class ChromaVectorStore(VectorStore):
    """ChromaDB implementation of the VectorStore interface."""

    def __init__(
        self,
        collection_name: Optional[str] = None,
        persist_directory: Optional[str] = None,
        embedding_provider: Optional[EmbeddingProvider] = None,
    ):
        self.collection_name = collection_name or settings.VECTOR_COLLECTION
        self.persist_directory = persist_directory or settings.VECTOR_DB_URL
        self.embedding_provider = embedding_provider or EmbeddingFactory.get_embedding_provider()

        try:
            if self.persist_directory.startswith("http://") or self.persist_directory.startswith("https://"):
                # Remote HTTP client
                url = self.persist_directory.replace("http://", "").replace("https://", "")
                parts = url.split(":")
                host = parts[0]
                port = int(parts[1]) if len(parts) > 1 else 8000
                self.client = chromadb.HttpClient(host=host, port=port)
            else:
                # Persistent local storage / ephemeral client
                self.client = chromadb.PersistentClient(path=self.persist_directory)

            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"ChromaVectorStore initialized collection '{self.collection_name}' at '{self.persist_directory}'")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB store: {e}")
            # Fall back to ephemeral client if persistent directory fails
            try:
                self.client = chromadb.Client()
                self.collection = self.client.get_or_create_collection(name=self.collection_name)
                logger.warning("Fell back to ephemeral in-memory ChromaDB client.")
            except Exception as inner_e:
                raise VectorStoreError(f"Critical ChromaDB initialization failure: {inner_e}")

    def add_documents(self, chunks: List[DocumentChunk]) -> None:
        if not chunks:
            return

        try:
            ids = [chunk.id for chunk in chunks]
            texts = [chunk.content for chunk in chunks]
            embeddings = self.embedding_provider.embed_documents(texts)
            
            metadatas = []
            for chunk in chunks:
                meta = dict(chunk.metadata or {})
                meta["document_id"] = chunk.document_id
                meta["chunk_index"] = chunk.chunk_index
                metadatas.append(meta)

            self.collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            logger.info(f"Successfully added {len(chunks)} chunks to vector store.")
        except Exception as e:
            logger.error(f"Failed to add documents to Chroma vector store: {e}")
            raise VectorStoreError(f"Failed to add documents to vector store: {str(e)}")

    def similarity_search(
        self, query: str, k: int = 4, filter: Optional[Dict[str, Any]] = None, filter_doc_id: Optional[str] = None
    ) -> List[DocumentChunk]:
        try:
            query_embedding = self.embedding_provider.embed_query(query)
            kwargs = {
                "query_embeddings": [query_embedding],
                "n_results": k,
            }
            where_filter = dict(filter or {})
            if filter_doc_id:
                where_filter["document_id"] = filter_doc_id

            if where_filter:
                kwargs["where"] = where_filter

            results = self.collection.query(**kwargs)


            chunks: List[DocumentChunk] = []
            if results and results.get("ids") and results["ids"][0]:
                ids = results["ids"][0]
                documents = results["documents"][0] if results.get("documents") else [""] * len(ids)
                metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(ids)

                for idx, chunk_id in enumerate(ids):
                    meta = metadatas[idx] or {}
                    doc_id = meta.get("document_id", "")
                    chunk_idx = meta.get("chunk_index", 0)
                    content = documents[idx]

                    chunks.append(
                        DocumentChunk(
                            id=chunk_id,
                            document_id=doc_id,
                            chunk_index=chunk_idx,
                            content=content,
                            metadata=meta
                        )
                    )
            return chunks
        except Exception as e:
            logger.error(f"Error performing similarity search in Chroma store: {e}")
            raise VectorStoreError(f"Similarity search failed: {str(e)}")

    def delete_document(self, document_id: str) -> None:
        try:
            self.collection.delete(where={"document_id": document_id})
            logger.info(f"Deleted vector entries for document_id={document_id}")
        except Exception as e:
            logger.error(f"Error deleting document {document_id} from vector store: {e}")
            raise VectorStoreError(f"Failed to delete document vectors: {str(e)}")

    def get_document(self, document_id: str) -> List[DocumentChunk]:
        try:
            results = self.collection.get(where={"document_id": document_id})
            chunks: List[DocumentChunk] = []
            if results and results.get("ids"):
                ids = results["ids"]
                documents = results.get("documents", [""] * len(ids))
                metadatas = results.get("metadatas", [{}] * len(ids))

                for idx, chunk_id in enumerate(ids):
                    meta = metadatas[idx] or {}
                    chunks.append(
                        DocumentChunk(
                            id=chunk_id,
                            document_id=document_id,
                            chunk_index=meta.get("chunk_index", 0),
                            content=documents[idx],
                            metadata=meta
                        )
                    )
            return chunks
        except Exception as e:
            logger.error(f"Error getting document vectors for {document_id}: {e}")
            raise VectorStoreError(f"Failed to get document vectors: {str(e)}")
