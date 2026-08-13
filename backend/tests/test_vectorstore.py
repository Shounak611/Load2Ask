import uuid
import pytest
from app.vectorstore.chroma_store import ChromaVectorStore
from app.models.internal import DocumentChunk
from app.embeddings.default_embedding import DefaultEmbeddingProvider


def test_chroma_vector_store(tmp_path):
    embedding_provider = DefaultEmbeddingProvider()
    store = ChromaVectorStore(
        collection_name="test_collection",
        persist_directory=str(tmp_path / "chroma"),
        embedding_provider=embedding_provider
    )

    doc_id = str(uuid.uuid4())
    chunk1 = DocumentChunk(
        document_id=doc_id,
        chunk_index=0,
        content="FastAPI is a modern web framework for building APIs with Python.",
        metadata={"category": "framework"}
    )
    chunk2 = DocumentChunk(
        document_id=doc_id,
        chunk_index=1,
        content="ChromaDB is an open source AI-native vector database.",
        metadata={"category": "database"}
    )

    # 1. Add documents
    store.add_documents([chunk1, chunk2])

    # 2. Get document
    retrieved = store.get_document(doc_id)
    assert len(retrieved) == 2

    # 3. Similarity search
    results = store.similarity_search("vector database", k=2)
    assert len(results) > 0
    assert any("ChromaDB" in r.content for r in results)

    # 4. Delete document
    store.delete_document(doc_id)
    retrieved_after_del = store.get_document(doc_id)
    assert len(retrieved_after_del) == 0
