from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class IngestionJobResponse(BaseModel):
    id: str
    document_id: str
    status: str
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
