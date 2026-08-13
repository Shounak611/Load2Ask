import io
from fastapi import status


def test_document_upload_and_crud(client, tmp_upload_dir):
    # 1. Test uploading a file
    file_content = b"This is a test document content for Load2Ask API."
    response = client.post(
        "/api/documents/upload",
        files={"files": ("test_upload.txt", io.BytesIO(file_content), "text/plain")}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "successful_uploads" in data
    assert len(data["successful_uploads"]) == 1
    doc = data["successful_uploads"][0]
    doc_id = doc["id"]
    assert doc["filename"] == "test_upload.txt"
    assert doc["status"] == "COMPLETED"

    # 2. Test get document by ID
    get_res = client.get(f"/api/documents/{doc_id}")
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["id"] == doc_id

    # 3. Test list documents
    list_res = client.get("/api/documents")
    assert list_res.status_code == status.HTTP_200_OK
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(d["id"] == doc_id for d in list_data["documents"])

    # 4. Test delete document
    del_res = client.delete(f"/api/documents/{doc_id}")
    assert del_res.status_code == status.HTTP_200_OK

    # Verify document is deleted
    get_after_del = client.get(f"/api/documents/{doc_id}")
    assert get_after_del.status_code == status.HTTP_404_NOT_FOUND


def test_invalid_file_upload(client):
    file_content = b"Unsupported format content"
    response = client.post(
        "/api/documents/upload",
        files={"files": ("test_file.unknown_ext_123", io.BytesIO(file_content), "application/octet-stream")}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert len(data["failed_uploads"]) == 1
    assert data["failed_uploads"][0]["filename"] == "test_file.unknown_ext_123"
