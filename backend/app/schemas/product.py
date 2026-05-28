"""
Pydantic schemas for Product model
"""
from typing import Optional, Union, List
from pydantic import BaseModel, field_serializer, field_validator
from datetime import datetime
from uuid import UUID

class ProductBase(BaseModel):
    name: str  # Наименование работы
    base_price: float = 0.0  # Стоимость работы
    category_id: Optional[Union[str, UUID]] = None  # Категория

    @field_validator('category_id', mode='before')
    @classmethod
    def validate_category_id(cls, v):
        if isinstance(v, str):
            if v.strip() == '':  # Handle empty strings
                return None
            try:
                return UUID(v)
            except ValueError:
                return None
        return v

class ProductCreate(ProductBase):
    name: str  # Required field

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    base_price: Optional[float] = None
    category_id: Optional[Union[str, UUID]] = None

    @field_validator('category_id', mode='before')
    @classmethod
    def validate_category_id(cls, v):
        if isinstance(v, str):
            if v.strip() == '':
                return None
            try:
                return UUID(v)
            except ValueError:
                return None
        return v

class ProductResponse(ProductBase):
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
