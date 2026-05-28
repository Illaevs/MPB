"""
ProductCategory model - Категории товаров и услуг
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class ProductCategory(Base):
    __tablename__ = "product_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Иерархия (рекурсивная связь)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("product_categories.id"), nullable=True)

    # Основная информация
    name = Column(String(255), nullable=False)
    description = Column(Text)

    # Сортировка
    sort_order = Column(Integer, default=0)

    # Активность
    is_active = Column(String(1), default="Y")  # Y/N

    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    parent = relationship("ProductCategory", remote_side=[id], backref="children")
    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")

    @classmethod
    async def get_all(cls, db, skip: int = 0, limit: int = 100):
        """Получить все категории"""
        from sqlalchemy import select
        try:
            query = select(cls).offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            print(f"Database error in get_all: {e}")
            return []

    @classmethod
    async def get_by_id(cls, db, category_id: str):
        """г?г?г>‘?‘отгь‘‘? г?‘?г? гаг’‘’гчг?г?‘?гь‘? гуг? ID"""
        from sqlalchemy import select, or_, cast, String
        try:
            category_uuid = category_id if isinstance(category_id, uuid.UUID) else uuid.UUID(str(category_id))
        except (ValueError, TypeError):
            category_uuid = None
        category_id_str = str(category_uuid) if category_uuid else str(category_id)
        category_id_hex = category_uuid.hex if category_uuid else None
        conditions = [
            cast(cls.id, String) == category_id_str,
            cast(cls.id, String) == category_id_hex,
        ]
        if category_uuid:
            conditions.append(cls.id == category_uuid)
        query = select(cls).where(or_(*conditions))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, db, **kwargs):
        """Создать новую категорию"""
        from datetime import datetime
        # Set created_at and updated_at explicitly
        now = datetime.now()
        kwargs['created_at'] = now
        kwargs['updated_at'] = now
        category = cls(**kwargs)
        db.add(category)
        await db.commit()
        await db.refresh(category)
        return category

    @classmethod
    async def update(cls, db, category_id: str, **kwargs):
        """г?г+г?г?г?гь‘‘? гаг’‘’гчг?г?‘?гь‘?"""
        from sqlalchemy import update, or_, cast, String
        try:
            category_uuid = category_id if isinstance(category_id, uuid.UUID) else uuid.UUID(str(category_id))
        except (ValueError, TypeError):
            return None
        category_id_str = str(category_uuid)
        category_id_hex = category_uuid.hex
        query = (
            update(cls)
            .where(or_(
                cast(cls.id, String) == category_id_str,
                cast(cls.id, String) == category_id_hex,
                cls.id == category_uuid,
            ))
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()

        # г?г?г>‘?‘отгь‘‘? г?г+г?г?г?г>гчг?г?‘<гü г?г+‘?гчга‘’
        return await cls.get_by_id(db, category_id)

    @classmethod
    async def delete(cls, db, category_id: str) -> bool:
        """г?г?гьг>гь‘‘? гаг’‘’гчг?г?‘?гь‘?"""
        from sqlalchemy import delete, or_, cast, String
        try:
            category_uuid = category_id if isinstance(category_id, uuid.UUID) else uuid.UUID(str(category_id))
        except (ValueError, TypeError):
            return False
        category_id_str = str(category_uuid)
        category_id_hex = category_uuid.hex
        query = delete(cls).where(or_(
            cast(cls.id, String) == category_id_str,
            cast(cls.id, String) == category_id_hex,
            cls.id == category_uuid,
        ))
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    def __repr__(self):
        return f"<ProductCategory(id={self.id}, name='{self.name}')>"
