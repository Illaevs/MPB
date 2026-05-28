"""
Pydantic schemas for upload jobs.
"""
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel


class UploadJobResponse(BaseModel):
    id: str
    status: str
    module: Optional[str] = None
    entity_id: Optional[str] = None
    file_kind: Optional[str] = None
    file_name: Optional[str] = None
    size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    meta: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
