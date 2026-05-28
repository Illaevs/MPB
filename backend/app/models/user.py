"""
User model - system users.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Float, Integer, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), nullable=False, unique=True)
    full_name = Column(String(255), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    wallpaper_url = Column(String(500), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(String(36), ForeignKey("roles.id"), nullable=True)
    # Орг-структура: узел, к которому привязан пользователь (nullable).
    org_unit_id = Column(String(36), ForeignKey("org_units.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret_enc = Column(String(1024), nullable=True)
    two_factor_backup_codes_hash = Column(Text, nullable=True)
    two_factor_enabled_at = Column(DateTime(timezone=True), nullable=True)
    
    # Рейтинг исполнителя
    rating = Column(Float, default=0.0)
    rating_count = Column(Integer, default=0)

    # Персональные настройки интерфейса (синхронизируются между устройствами)
    ui_preferences = Column(JSON, default=dict, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    role = relationship("Role")
    # Расширенная карточка сотрудника (см. UserProfile).
    # 1-к-1, cascade — чтобы удаление пользователя чистило профиль.
    profile = relationship(
        "UserProfile",
        uselist=False,
        back_populates="user",
        foreign_keys="UserProfile.user_id",
        cascade="all, delete-orphan",
    )

    @classmethod
    async def get_all(cls, db):
        from sqlalchemy import select
        result = await db.execute(select(cls).order_by(cls.full_name))
        return result.scalars().all()

    @classmethod
    async def get_by_id(cls, db, user_id: str):
        from sqlalchemy import select, or_
        try:
            user_uuid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
        except (ValueError, TypeError):
            user_uuid = None
        user_id_str = str(user_uuid) if user_uuid else str(user_id)
        user_id_hex = user_uuid.hex if user_uuid else None
        conditions = [cls.id == user_id_str]
        if user_id_hex:
            conditions.append(cls.id == user_id_hex)
        result = await db.execute(select(cls).where(or_(*conditions)))
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_email(cls, db, email: str):
        from sqlalchemy import select
        result = await db.execute(select(cls).where(cls.email == email))
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, db, **kwargs):
        now = datetime.now()
        kwargs["created_at"] = now
        kwargs["updated_at"] = now
        user = cls(**kwargs)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @classmethod
    async def update(cls, db, user_id: str, **kwargs):
        from sqlalchemy import update, or_
        try:
            user_uuid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
        except (ValueError, TypeError):
            user_uuid = None
        user_id_str = str(user_uuid) if user_uuid else str(user_id)
        user_id_hex = user_uuid.hex if user_uuid else None
        conditions = [cls.id == user_id_str]
        if user_id_hex:
            conditions.append(cls.id == user_id_hex)
        query = (
            update(cls)
            .where(or_(*conditions))
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()
        return await cls.get_by_id(db, user_id)

    @classmethod
    async def delete(cls, db, user_id: str) -> bool:
        from sqlalchemy import delete, or_
        try:
            user_uuid = user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
        except (ValueError, TypeError):
            user_uuid = None
        user_id_str = str(user_uuid) if user_uuid else str(user_id)
        user_id_hex = user_uuid.hex if user_uuid else None
        conditions = [cls.id == user_id_str]
        if user_id_hex:
            conditions.append(cls.id == user_id_hex)
        result = await db.execute(delete(cls).where(or_(*conditions)))
        await db.commit()
        return result.rowcount > 0
