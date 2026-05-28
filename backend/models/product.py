"""
Product model.
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Float, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    category_id = Column(UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=True)

    name = Column(String(255), nullable=False)
    base_price = Column(Float, default=0.0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    category = relationship("ProductCategory", back_populates="products")
    deal_products = relationship("DealProduct", back_populates="product", cascade="all, delete-orphan")
    lead_products = relationship("LeadProduct", back_populates="product", cascade="all, delete-orphan")
    subcontractor_products = relationship(
        "SubcontractorProduct",
        back_populates="product",
        cascade="all, delete-orphan"
    )

    @classmethod
    async def get_all(cls, db, skip: int = 0, limit: int = 100):
        from sqlalchemy import select
        try:
            query = select(cls).offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            print(f"Database error in get_all: {e}")
            return []

    @classmethod
    async def get_by_id(cls, db, product_id):
        from sqlalchemy import select, or_, cast, String
        try:
            product_uuid = product_id if isinstance(product_id, uuid.UUID) else uuid.UUID(str(product_id))
        except (ValueError, TypeError):
            product_uuid = None
        product_id_str = str(product_uuid) if product_uuid else str(product_id)
        product_id_hex = product_uuid.hex if product_uuid else None
        conditions = [
            cast(cls.id, String) == product_id_str,
            cast(cls.id, String) == product_id_hex,
        ]
        if product_uuid:
            conditions.append(cls.id == product_uuid)
        query = select(cls).where(or_(*conditions))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_category(cls, db, category_id: str):
        from sqlalchemy import select, or_, cast, String
        try:
            category_uuid = category_id if isinstance(category_id, uuid.UUID) else uuid.UUID(str(category_id))
        except (ValueError, TypeError):
            category_uuid = None
        category_id_str = str(category_uuid) if category_uuid else str(category_id)
        category_id_hex = category_uuid.hex if category_uuid else None
        conditions = [
            cast(cls.category_id, String) == category_id_str,
            cast(cls.category_id, String) == category_id_hex,
        ]
        if category_uuid:
            conditions.append(cls.category_id == category_uuid)
        query = select(cls).where(or_(*conditions))
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def search(cls, db, search_term: str, skip: int = 0, limit: int = 100):
        from sqlalchemy import select
        query = select(cls).where(
            cls.name.ilike(f"%{search_term}%")
        ).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def create(cls, db, **kwargs):
        now = datetime.now()
        kwargs['created_at'] = now
        kwargs['updated_at'] = now
        product = cls(**kwargs)
        db.add(product)
        await db.commit()
        await db.refresh(product)
        return product

    @classmethod
    async def update(cls, db, product_id: str, **kwargs):
        from sqlalchemy import update, or_, cast, String
        try:
            product_uuid = product_id if isinstance(product_id, uuid.UUID) else uuid.UUID(str(product_id))
        except (ValueError, TypeError):
            return None
        product_id_str = str(product_uuid)
        product_id_hex = product_uuid.hex
        query = (
            update(cls)
            .where(or_(
                cast(cls.id, String) == product_id_str,
                cast(cls.id, String) == product_id_hex,
                cls.id == product_uuid,
            ))
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()
        return await cls.get_by_id(db, product_id)

    @classmethod
    async def delete(cls, db, product_id: str) -> bool:
        from sqlalchemy import delete, or_, cast, String
        try:
            product_uuid = product_id if isinstance(product_id, uuid.UUID) else uuid.UUID(str(product_id))
        except (ValueError, TypeError):
            return False
        product_id_str = str(product_uuid)
        product_id_hex = product_uuid.hex
        query = delete(cls).where(or_(
            cast(cls.id, String) == product_id_str,
            cast(cls.id, String) == product_id_hex,
            cls.id == product_uuid,
        ))
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}')>"
