"""
Pydantic schemas for Company model
"""
from typing import Optional, Union, List
from pydantic import BaseModel, field_serializer
from datetime import datetime
from uuid import UUID


class BankAccount(BaseModel):
    bank_name: Optional[str] = None
    account_rs: Optional[str] = None
    account_ks: Optional[str] = None
    bik: Optional[str] = None


class ContactPerson(BaseModel):
    name: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None


class CompanyBase(BaseModel):
    inn: str
    type: Optional[str] = "customer"
    name: str
    short_name: Optional[str] = None
    full_name: Optional[str] = None
    kpp: Optional[str] = None
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    phones: Optional[List[str]] = []
    emails: Optional[List[str]] = []
    contacts: Optional[List[ContactPerson]] = []
    bank_accounts: Optional[List[BankAccount]] = []
    address: Optional[str] = None
    rating_speed: Optional[float] = 0.0
    rating_quality: Optional[float] = 0.0
    work_directions: Optional[List[Union[str, int]]] = []
    rating: Optional[float] = 0.0
    note: Optional[str] = None
    is_default: Optional[bool] = False

class CompanyCreate(CompanyBase):
    inn: str  # Required field
    name: str  # Required field

class CompanyUpdate(CompanyBase):
    pass

class CompanyResponse(CompanyBase):
    id: Union[str, UUID]
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @field_serializer('id')
    def serialize_id(self, value):
        """Convert UUID to string for JSON serialization"""
        if isinstance(value, UUID):
            return str(value)
        return value
