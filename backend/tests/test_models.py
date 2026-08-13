from app.models.database import (
    DocumentModel, DocumentChunkModel, ChatSessionModel, ChatMessageModel, IngestionJobModel
)


def test_document_and_chunk_models(db_session):
    doc = DocumentModel(
        filename="test_doc.txt",
        source_type="txt",
        title="Test Document",
        mime_type="text/plain",
        file_size=1024,
        doc_metadata={"author": "Test Author"}
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    assert doc.id is not None
    assert doc.status == "PENDING"

    chunk1 = DocumentChunkModel(
        document_id=doc.id,
        chunk_index=0,
        content="First chunk content",
        chunk_metadata={"section": 1}
    )
    chunk2 = DocumentChunkModel(
        document_id=doc.id,
        chunk_index=1,
        content="Second chunk content",
        chunk_metadata={"section": 2}
    )
    db_session.add_all([chunk1, chunk2])
    db_session.commit()

    assert len(doc.chunks) == 2
    assert doc.chunks[0].content == "First chunk content"


def test_chat_session_and_message_models(db_session):
    session = ChatSessionModel(title="Test Chat Session")
    db_session.add(session)
    db_session.commit()
    db_session.refresh(session)

    assert session.id is not None

    msg1 = ChatMessageModel(session_id=session.id, role="user", content="Hello RAG!")
    msg2 = ChatMessageModel(session_id=session.id, role="assistant", content="Hello! How can I help?")
    db_session.add_all([msg1, msg2])
    db_session.commit()

    assert len(session.messages) == 2
    assert session.messages[0].role == "user"


def test_ingestion_job_model(db_session):
    doc = DocumentModel(filename="job_doc.pdf", source_type="pdf")
    db_session.add(doc)
    db_session.commit()

    job = IngestionJobModel(document_id=doc.id, status="PROCESSING")
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    assert job.id is not None
    assert job.document_id == doc.id
    assert job.status == "PROCESSING"
