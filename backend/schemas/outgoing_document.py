"""
Pydantic schemas for OutgoingDocument registry.
"""
from datetime import date, datetime
from typing import Any, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, field_serializer, field_validator


class OutgoingDocumentBase(BaseModel):
    document_kind: Optional[str] = "letter"
    editor_mode: Optional[str] = "classic"
    editor_schema_version: Optional[int] = 1
    editor_draft: Optional[Any] = None
    editor_validation: Optional[Any] = None
    editor_render_context: Optional[Any] = None
    recipient_company_id: Union[str, UUID]
    deal_id: Optional[Union[str, UUID]] = None
    contract_id: Optional[Union[str, UUID]] = None
    letter_date: date
    subject: str
    body: Optional[str] = ""
    attachments_list: Optional[str] = ""
    bank_account_index: Optional[int] = None
    bank_account_snapshot: Optional[Any] = None
    linked_stage_ids: Optional[Any] = None
    linked_payment_items: Optional[Any] = None
    act_contract_document_id: Optional[Union[str, UUID]] = None
    recipient_short_name: Optional[str] = None
    recipient_to_name: Optional[str] = None
    recipient_appeal: Optional[str] = None
    recipient_eio: Optional[str] = None
    recipient_genitive_name: Optional[str] = None
    recipient_salutation: Optional[str] = None
    status: Optional[str] = "draft"

    @field_validator("recipient_company_id", "deal_id", "contract_id", "act_contract_document_id", mode="before")
    @classmethod
    def validate_uuid_fields(cls, value):
        if isinstance(value, str) and value:
            try:
                return UUID(value)
            except ValueError:
                return None
        return value


class OutgoingDocumentCreate(OutgoingDocumentBase):
    pass


class OutgoingDocumentUpdate(BaseModel):
    document_kind: Optional[str] = None
    editor_mode: Optional[str] = None
    editor_schema_version: Optional[int] = None
    editor_draft: Optional[Any] = None
    editor_validation: Optional[Any] = None
    editor_render_context: Optional[Any] = None
    recipient_company_id: Optional[Union[str, UUID]] = None
    deal_id: Optional[Union[str, UUID]] = None
    contract_id: Optional[Union[str, UUID]] = None
    letter_date: Optional[date] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    attachments_list: Optional[str] = None
    bank_account_index: Optional[int] = None
    bank_account_snapshot: Optional[Any] = None
    linked_stage_ids: Optional[Any] = None
    linked_payment_items: Optional[Any] = None
    act_contract_document_id: Optional[Union[str, UUID]] = None
    recipient_short_name: Optional[str] = None
    recipient_to_name: Optional[str] = None
    recipient_appeal: Optional[str] = None
    recipient_eio: Optional[str] = None
    recipient_genitive_name: Optional[str] = None
    recipient_salutation: Optional[str] = None
    status: Optional[str] = None
    our_company_key: Optional[str] = None
    outgoing_number_suffix: Optional[str] = None

    @field_validator("recipient_company_id", "deal_id", "contract_id", "act_contract_document_id", mode="before")
    @classmethod
    def validate_uuid_fields(cls, value):
        if isinstance(value, str) and value:
            try:
                return UUID(value)
            except ValueError:
                return None
        return value


class OutgoingDocumentResolveRequest(BaseModel):
    document_id: Optional[Union[str, UUID]] = None
    document_kind: Optional[str] = "letter"
    editor_mode: Optional[str] = "classic"
    editor_schema_version: Optional[int] = 1
    editor_draft: Optional[Any] = None
    editor_validation: Optional[Any] = None
    editor_render_context: Optional[Any] = None
    recipient_company_id: Optional[Union[str, UUID]] = None
    deal_id: Optional[Union[str, UUID]] = None
    contract_id: Optional[Union[str, UUID]] = None
    letter_date: Optional[date] = None
    subject: Optional[str] = None
    body: Optional[str] = ""
    attachments_list: Optional[str] = ""
    bank_account_index: Optional[int] = None
    linked_stage_ids: Optional[Any] = None
    linked_payment_items: Optional[Any] = None
    recipient_short_name: Optional[str] = None
    recipient_to_name: Optional[str] = None
    recipient_appeal: Optional[str] = None
    recipient_eio: Optional[str] = None
    recipient_genitive_name: Optional[str] = None
    recipient_salutation: Optional[str] = None
    status: Optional[str] = "draft"
    our_company_key: Optional[str] = None

    @field_validator(
        "document_id",
        "recipient_company_id",
        "deal_id",
        "contract_id",
        mode="before",
    )
    @classmethod
    def validate_uuid_fields(cls, value):
        if isinstance(value, str) and value:
            try:
                return UUID(value)
            except ValueError:
                return None
        return value


class OutgoingDocumentResponse(OutgoingDocumentBase):
    id: Union[str, UUID]
    outgoing_number: str
    outgoing_number_seq: int
    outgoing_number_display: Optional[str] = None
    document_kind_label: Optional[str] = None
    our_company_key: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    recipient_company_name: Optional[str] = None
    deal_title: Optional[str] = None
    contract_number: Optional[str] = None
    selected_bank_account: Optional[Any] = None
    bank_accounts_count: Optional[int] = 0
    files_count: Optional[int] = 0
    versions_count: Optional[int] = 0

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @field_serializer("id")
    def serialize_id(self, value):
        if isinstance(value, UUID):
            return str(value)
        return value


class OutgoingDocumentVersionResponse(BaseModel):
    id: Union[str, UUID]
    document_id: Union[str, UUID]
    version_number: int
    status: Optional[str] = "draft"
    created_at: Optional[datetime] = None
    created_by: Optional[str] = None
    comment: Optional[str] = None
    pdf_path: Optional[str] = None
    pdf_public_url: Optional[str] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @field_serializer("id", "document_id")
    def serialize_ids(self, value):
        if isinstance(value, UUID):
            return str(value)
        return value


class OutgoingDocumentFileResponse(BaseModel):
    id: Union[str, UUID]
    document_id: Union[str, UUID]
    version_id: Optional[Union[str, UUID]] = None
    file_type: str
    file_path: Optional[str] = None
    file_name: Optional[str] = None
    public_url: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @field_serializer("id", "document_id", "version_id")
    def serialize_ids(self, value):
        if isinstance(value, UUID):
            return str(value)
        return value


class OutgoingDocumentDetailResponse(OutgoingDocumentResponse):
    versions: List[OutgoingDocumentVersionResponse] = []
    files: List[OutgoingDocumentFileResponse] = []
