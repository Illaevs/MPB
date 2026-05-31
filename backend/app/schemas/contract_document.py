"""
Pydantic schemas for ContractDocument model.
"""
from typing import List, Optional, Union
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_serializer


class ContractDocumentBase(BaseModel):
    contract_id: Optional[Union[str, UUID]] = None
    doc_type: str
    number_in_contract: int
    status: Optional[str] = "draft"
    amount: Optional[float] = None
    pdf_file_name: Optional[str] = None
    pdf_storage_path: Optional[str] = None
    edit_file_name: Optional[str] = None
    edit_storage_path: Optional[str] = None
    pdf_uploaded_by: Optional[str] = None
    pdf_uploaded_at: Optional[datetime] = None
    edit_uploaded_by: Optional[str] = None
    edit_uploaded_at: Optional[datetime] = None


class ContractDocumentCreate(BaseModel):
    doc_type: str
    status: Optional[str] = "draft"
    amount: Optional[float] = None


class ContractDocumentUpdate(BaseModel):
    status: Optional[str] = None
    amount: Optional[float] = None


class ContractDocumentProductLinkResponse(BaseModel):
    deal_product_id: str
    product_name: Optional[str] = None
    custom_name: Optional[str] = None


class ContractDocumentResponse(ContractDocumentBase):
    id: Union[str, UUID]
    linked_products: List[ContractDocumentProductLinkResponse] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @field_serializer("id")
    def serialize_id(self, value):
        if isinstance(value, UUID):
            return str(value)
        return value
