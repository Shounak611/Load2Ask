from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, HttpUrl, ConfigDict


class URLIngestRequest(BaseModel):
    url: str = Field(..., description="Web page URL to ingest into RAG system")


class DocumentStatusResponse(BaseModel):
    document_id: str
    document_status: str
    job_id: Optional[str] = None
    job_status: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    chunk_count: int = 0


class DocumentBase(BaseModel):
    filename: str
    source_type: str
    source_uri: Optional[str] = None
    title: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="doc_metadata")

    model_config = ConfigDict(populate_by_name=True)


class DocumentCreate(DocumentBase):
    pass


class DocumentChunkResponse(BaseModel):
    id: str
    document_id: str
    chunk_index: int
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict, alias="chunk_metadata")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DocumentResponse(DocumentBase):
    id: str
    status: str
    created_at: datetime
    updated_at: datetime
    chunk_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentResponse]


class MultiUploadResponse(BaseModel):
    message: str
    successful_uploads: List[DocumentResponse]
    failed_uploads: List[Dict[str, Any]]
