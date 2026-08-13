from typing import Dict, Any
from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    status: str
    version: str
    database: str
    vector_store: str
    details: Dict[str, Any]
