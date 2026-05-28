from typing import Optional, Union
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_serializer


class TreasuryAllocationBase(BaseModel):
    transaction_id: Union[str, UUID]
    income_expense_id: Union[str, UUID]
    amount: float
    category_code: Optional[str] = None


class TreasuryAllocationCreate(BaseModel):
    income_expense_id: Optional[Union[str, UUID]] = None  # если не указан — автосоздание ДДС
    amount: float
    category_code: Optional[str] = None


class TreasuryAllocationUpdate(BaseModel):
    income_expense_id: Optional[Union[str, UUID]] = None
    amount: Optional[float] = None
    category_code: Optional[str] = None


class TreasuryAllocationResponse(TreasuryAllocationBase):
    id: Union[str, UUID]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @field_serializer("id", "transaction_id", "income_expense_id")
    def serialize_ids(self, value):
        if isinstance(value, UUID):
            return str(value)
        return value
