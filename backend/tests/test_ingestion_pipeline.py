import io
import pytest
from fastapi import status

from app.ingestion.normalizer import DocumentNormalizer
from app.ingestion.chunker import ConfigurableChunker
from app.models.internal import Document


def test_normalizer():
    raw_text = "Line 1 \r\n\r\n\r\n\r\nLine 2   \n\x00Control char"
    doc = Document(
        source_type="txt",
        source_name="test.txt",
        content=raw_text
    )
    norm_doc = DocumentNormalizer.normalize(doc)
    assert "\r" not in norm_doc.content
    assert "\x00" not in norm_doc.content
    assert "Line 1" in norm_doc.content
    assert "Line 2" in norm_doc.content


def test_configurable_chunker():
    chunker = ConfigurableChunker(chunk_size=10, chunk_overlap=2)
    doc = Document(
        id="doc-123",
        source_type="txt",
        source_name="sample.txt",
        content="Paragraph one text. " * 30,
        metadata={"section": "Intro"}
    )
    chunks = chunker.chunk_document(doc)
    assert len(chunks) > 1
    assert chunks[0].metadata["document_id"] == "doc-123"
    assert chunks[0].metadata["section"] == "Intro"


def test_multi_file_upload_and_status(client, tmp_upload_dir):
    # Upload 2 files: 1 valid TXT, 1 valid JSON
    file1_content = b"Content of valid TXT document for RAG ingestion pipeline testing."
    file2_content = b'{"name": "Valid JSON Document", "status": "active"}'

    response = client.post(
        "/api/documents/upload",
        files=[
            ("files", ("doc1.txt", io.BytesIO(file1_content), "text/plain")),
            ("files", ("doc2.json", io.BytesIO(file2_content), "application/json"))
        ]
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert len(data["successful_uploads"]) == 2
    assert len(data["failed_uploads"]) == 0

    doc1_id = data["successful_uploads"][0]["id"]

    # Test GET /api/documents/{id}/status endpoint
    status_res = client.get(f"/api/documents/{doc1_id}/status")
    assert status_res.status_code == status.HTTP_200_OK
    status_data = status_res.json()
    assert status_data["document_id"] == doc1_id
    assert status_data["document_status"] == "COMPLETED"
    assert status_data["job_status"] == "COMPLETED"
    assert status_data["chunk_count"] > 0


def test_multi_file_upload_error_isolation(client, tmp_upload_dir):
    # Upload 1 valid file and 1 unsupported invalid extension file
    valid_content = b"Valid txt content."
    invalid_content = b"Unknown format data."

    response = client.post(
        "/api/documents/upload",
        files=[
            ("files", ("valid.txt", io.BytesIO(valid_content), "text/plain")),
            ("files", ("invalid.unknown_ext_xyz", io.BytesIO(invalid_content), "application/octet-stream"))
        ]
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    # Ensure one document succeeded and the failed document did not corrupt/abort the valid upload
    assert len(data["successful_uploads"]) == 1
    assert len(data["failed_uploads"]) == 1
    assert data["failed_uploads"][0]["filename"] == "invalid.unknown_ext_xyz"


def test_duplicate_document_detection(client, tmp_upload_dir):
    content = b"Exact identical document content for duplicate detection test."

    res1 = client.post(
        "/api/documents/upload",
        files={"files": ("dup1.txt", io.BytesIO(content), "text/plain")}
    )
    assert res1.status_code == status.HTTP_201_CREATED
    doc1 = res1.json()["successful_uploads"][0]

    res2 = client.post(
        "/api/documents/upload",
        files={"files": ("dup2.txt", io.BytesIO(content), "text/plain")}
    )
    assert res2.status_code == status.HTTP_201_CREATED
    doc2 = res2.json()["successful_uploads"][0]

    # Verify doc2 metadata tagged duplicate_of pointing to doc1
    get_res = client.get(f"/api/documents/{doc2['id']}")
    assert get_res.status_code == status.HTTP_200_OK
    data = get_res.json()
    doc2_meta = data.get("metadata") or data.get("doc_metadata") or {}
    assert "duplicate_of" in doc2_meta
    assert doc2_meta["duplicate_of"] == doc1["id"]



def test_url_ingestion_ssrf_rejection(client):
    # Test SSRF rejection on localhost URL
    response = client.post(
        "/api/documents/url",
        json={"url": "http://127.0.0.1:8000/internal"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "SSRF" in response.json()["error"] or "forbidden" in response.json()["error"].lower()
