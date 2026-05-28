"""
Pydantic schemas for ProductCategory model
"""
from typing import Optional, Union
from pydantic import BaseModel, field_serializer, field_validator
from datetime import datetime
from uuid import UUID

class ProductCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[Union[str, UUID]] = None
    sort_order: Optional[int] = 0
    is_active: Optional[str] = "Y"

    @field_validator('parent_id', mode='before')
    @classmethod
    def validate_parent_id(cls, v):
        if isinstance(v, str):
            if v.strip() == '':  # Handle empty strings
                return None
            try:
                return UUID(v)
            except ValueError:
                return None
        return v

class ProductCategoryCreate(ProductCategoryBase):
    name: str  # Required field

class ProductCategoryUpdate(ProductCategoryBase):
    pass

class ProductCategoryResponse(ProductCategoryBase):
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
