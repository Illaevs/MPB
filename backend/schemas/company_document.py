"""
Schemas for CompanyDocument.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, field_serializer


class CompanyDocumentBase(BaseModel):
    company_id: str
    our_company_id: Optional[str] = None
    doc_type: str
    doc_value: Optional[str] = None
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    storage_path: Optional[str] = None
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    parent_id: Optional[str] = None
    status: Optional[str] = None
    comment: Optional[str] = None


class CompanyDocumentCreate(CompanyDocumentBase):
    company_id: str
    doc_type: str


class CompanyDocumentUpdate(BaseModel):
    our_company_id: Optional[str] = None
    doc_value: Optional[str] = None
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    storage_path: Optional[str] = None
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    parent_id: Optional[str] = None
    status: Optional[str] = None
    comment: Optional[str] = None


class CompanyDocumentResponse(BaseModel):
    id: str
    company_id: str
    our_company_id: Optional[str] = None
    our_company_name: Optional[str] = None
    doc_type: str
    doc_value: Optional[str] = None
    file_name: Optional[str] = None
    file_url: Optional[str] = None
    storage_path: Optional[str] = None
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    parent_id: Optional[str] = None
    status: str
    comment: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @field_serializer("id", "company_id", "our_company_id", "parent_id")
    def serialize_id(self, value):
        return str(value) if value is not None else None
