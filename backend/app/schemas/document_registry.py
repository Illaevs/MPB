"""
Pydantic schemas for consolidated document registry.
"""
from datetime import date, datetime
from typing import Optional, List

from pydantic import BaseModel


class DocumentBase(BaseModel):
    doc_type: str
    title: str
    number: Optional[str] = None
    document_date: Optional[date] = None
    status: Optional[str] = "draft"
    project_id: Optional[str] = None
    counterparty_id: Optional[str] = None
    our_company_id: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    doc_type: Optional[str] = None
    title: Optional[str] = None
    number: Optional[str] = None
    document_date: Optional[date] = None
    status: Optional[str] = None
    project_id: Optional[str] = None
    counterparty_id: Optional[str] = None
    our_company_id: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None


class DocumentResponse(DocumentBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentRelationCreate(BaseModel):
    related_document_id: str
    relation_type: Optional[str] = "link"


class DocumentRelationResponse(BaseModel):
    id: str
    document_id: str
    related_document_id: str
    relation_type: str
    created_at: Optional[datetime] = None
    related_document: Optional[DocumentResponse] = None
    document: Optional[DocumentResponse] = None

    class Config:
        from_attributes = True


class DocumentPackageBase(BaseModel):
    title: str
    package_date: Optional[date] = None
    status: Optional[str] = "draft"
    project_id: Optional[str] = None
    counterparty_id: Optional[str] = None
    our_company_id: Optional[str] = None


class DocumentPackageCreate(DocumentPackageBase):
    pass


class DocumentPackageUpdate(BaseModel):
    title: Optional[str] = None
    package_date: Optional[date] = None
    status: Optional[str] = None
    project_id: Optional[str] = None
    counterparty_id: Optional[str] = None
    our_company_id: Optional[str] = None


class DocumentPackageResponse(DocumentPackageBase):
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentPackageItemCreate(BaseModel):
    document_id: str


class DocumentPackageItemResponse(BaseModel):
    id: str
    package_id: str
    document_id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentDispatchCreate(BaseModel):
    document_id: Optional[str] = None
    package_id: Optional[str] = None
    status: Optional[str] = "sent"
    note: Optional[str] = None


class DocumentDispatchResponse(BaseModel):
    id: str
    document_id: Optional[str] = None
    package_id: Optional[str] = None
    status: str
    note: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentDispatchChannelCreate(BaseModel):
    channel: str
    channel_date: date
    confirmation_file: Optional[str] = None
    track_number: Optional[str] = None


class DocumentDispatchChannelUpdate(BaseModel):
    channel_date: Optional[date] = None
    confirmation_file: Optional[str] = None
    track_number: Optional[str] = None


class DocumentDispatchChannelResponse(BaseModel):
    id: str
    dispatch_id: str
    channel: str
    channel_date: date
    confirmation_file: Optional[str] = None
    track_number: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
