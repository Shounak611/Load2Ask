from dataclasses import field
from typing import Dict, Any, Optional
import uuid
from pydantic import BaseModel, Field


class Document(BaseModel):
    """Common internal representation of an ingested document."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_type: str
    source_name: str
    source_uri: Optional[str] = None
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DocumentChunk(BaseModel):
    """Common internal representation of a document chunk."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    document_id: str
    content: str
    chunk_index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
