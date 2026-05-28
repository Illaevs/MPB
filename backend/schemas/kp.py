from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class KpTemplateBase(BaseModel):
    name: str
    docx_url: str
    pdf_url: Optional[str] = None
    is_active: bool = True


class KpTemplateCreate(KpTemplateBase):
    pass


class KpTemplateResponse(KpTemplateBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class KpTemplateBindingCreate(BaseModel):
    template_id: str
    our_company_id: str


class KpTemplateBindingResponse(KpTemplateBindingCreate):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True


class KpVersionResponse(BaseModel):
    id: str
    kp_id: str
    version: int
    docx_url: Optional[str]
    pdf_url: Optional[str]
    total_amount: float
    vat_amount: float
    total_text: Optional[str]
    vat_text: Optional[str]
    template_id: Optional[str]
    created_at: Optional[datetime]

    class Config:
        orm_mode = True


class KpDocumentCreate(BaseModel):
    lead_id: str
    our_company_id: Optional[str] = None
    template_id: Optional[str] = None
    vat_rate: Optional[float] = 20.0


class KpDocumentResponse(BaseModel):
    id: str
    lead_id: str
    number_seq: int
    number_display: str
    status: str
    current_version: int
    our_company_id: Optional[str]
    template_id: Optional[str]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    versions: List[KpVersionResponse] = []

    class Config:
        orm_mode = True
