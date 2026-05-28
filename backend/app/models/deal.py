"""
Deal model - Сделки/Объекты строительства
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Deal(Base):
    __tablename__ = "deals"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Основная информация
    title = Column(String(255), nullable=False)      # Рабочее наименование
    obj_name = Column(String(500))                   # Полное наименование объекта
    address = Column(Text)                           # Адрес объекта
    object_type = Column(String(100))                # Тип объекта (жилой, коммерческий, etc.)
    object_area = Column(Float)                      # Площадь объекта (м²)

    # Контрагенты
    customer_id = Column(String(36), ForeignKey("companies.id"))
    general_contractor_id = Column(String(36), ForeignKey("companies.id"))
    our_company_id = Column(String(36), ForeignKey("companies.id"))

    # Конфигурация неустоек (JSONB в PostgreSQL, JSON в SQLite)
    penalty_config = Column(JSON, default=dict)

    # Пути к файлам в S3
    s3_prefix_tz = Column(String(500))    # Те�
    s3_prefix_docs = Column(String(500))  # Проектная документация

    # Статус проекта
    status = Column(String(50), default="active")

    # Финансовые итоги
    total_contract_value = Column(Float, default=0.0)
    total_paid = Column(Float, default=0.0)

    # Настройки НДС
    vat_rate = Column(Float, default=20.0)  # Ставка НДС (%)
    vat_included = Column(Boolean, default=True)  # НДС включен в цену или нет

    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    customer = relationship("Company", foreign_keys=[customer_id])
    general_contractor = relationship("Company", foreign_keys=[general_contractor_id])

    @classmethod
    async def get_all(cls, db, skip: int = 0, limit: int = 100):
        """Получить все проекты"""
        from sqlalchemy import select
        try:
            query = select(cls).offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            print(f"Database error in get_all: {e}")
            # Возвращаем пустой список при ошибке
            return []

    @classmethod
    async def get_filtered(
        cls,
        db,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        min_contract_value: Optional[float] = None,
        max_contract_value: Optional[float] = None,
        search: Optional[str] = None,
        customer_id: Optional[str] = None,
        our_company_id: Optional[str] = None
    ):
        """Получить проекты с фильтрами"""
        from sqlalchemy import select, and_, or_
        try:
            query = select(cls)

            # Apply filters
            filters = []

            def id_filter_values(value):
                text = str(value or "").strip()
                if not text:
                    return []
                compact = text.replace("-", "").lower()
                values = {text, compact}
                if len(compact) == 32:
                    values.add(
                        f"{compact[0:8]}-{compact[8:12]}-{compact[12:16]}-"
                        f"{compact[16:20]}-{compact[20:32]}"
                    )
                return list(values)

            # Status filter
            if status:
                filters.append(cls.status == status)

            customer_values = id_filter_values(customer_id)
            if customer_values:
                filters.append(cls.customer_id.in_(customer_values))

            our_company_values = id_filter_values(our_company_id)
            if our_company_values:
                filters.append(cls.our_company_id.in_(our_company_values))

            # Contract value range filter
            if min_contract_value is not None:
                filters.append(cls.total_contract_value >= min_contract_value)
            if max_contract_value is not None:
                filters.append(cls.total_contract_value <= max_contract_value)

            # Search filter (title, obj_name, address)
            if search and search.strip():
                search_term = f"%{search.strip()}%"
                search_filters = [
                    cls.title.ilike(search_term),
                    cls.obj_name.ilike(search_term),
                    cls.address.ilike(search_term)
                ]
                filters.append(or_(*search_filters))

            # Apply all filters
            if filters:
                query = query.where(and_(*filters))

            # Apply pagination
            query = query.offset(skip).limit(limit)

            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            print(f"Database error in get_filtered: {e}")
            # Возвращаем пустой список при ошибке
            return []

    @classmethod
    async def get_by_id(cls, db, deal_id: str):
        from sqlalchemy import select, or_
        try:
            deal_uuid = deal_id if isinstance(deal_id, uuid.UUID) else uuid.UUID(str(deal_id))
        except (ValueError, TypeError):
            deal_uuid = None
        deal_id_str = str(deal_uuid) if deal_uuid else str(deal_id)
        deal_id_hex = deal_uuid.hex if deal_uuid else None
        conditions = [cls.id == deal_id_str]
        if deal_id_hex:
            conditions.append(cls.id == deal_id_hex)
        query = select(cls).where(or_(*conditions))
        result = await db.execute(query)
        return result.scalar_one_or_none()
    @classmethod
    async def create(cls, db, **kwargs):
        """Создать новый проект"""
        from datetime import datetime
        # Set created_at and updated_at explicitly
        now = datetime.now()
        kwargs['created_at'] = now
        kwargs['updated_at'] = now
        # Normalize UUID fields to strings for SQLite compatibility
        for key in ['customer_id', 'general_contractor_id', 'our_company_id']:
            value = kwargs.get(key)
            if isinstance(value, uuid.UUID):
                kwargs[key] = str(value)
        deal = cls(**kwargs)
        db.add(deal)
        await db.commit()
        await db.refresh(deal)
        return deal

    @classmethod
    async def update(cls, db, deal_id: str, **kwargs):
        from sqlalchemy import update, or_
        from datetime import datetime
        try:
            deal_uuid = deal_id if isinstance(deal_id, uuid.UUID) else uuid.UUID(str(deal_id))
        except (ValueError, TypeError):
            return None

        processed_kwargs = {}
        for key, value in kwargs.items():
            if key in ['created_at', 'updated_at'] and isinstance(value, str):
                try:
                    processed_kwargs[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    continue
            elif key in ['customer_id', 'general_contractor_id', 'our_company_id'] and isinstance(value, uuid.UUID):
                processed_kwargs[key] = str(value)
            else:
                processed_kwargs[key] = value

        processed_kwargs['updated_at'] = datetime.now()

        deal_id_str = str(deal_uuid)
        deal_id_hex = deal_uuid.hex
        query = (
            update(cls)
            .where(or_(cls.id == deal_uuid, cls.id == deal_id_str, cls.id == deal_id_hex))
            .values(**processed_kwargs)
            .execution_options(synchronize_session='fetch')
        )
        await db.execute(query)
        await db.commit()

        return await cls.get_by_id(db, deal_id)
    @classmethod
    async def delete(cls, db, deal_id: str) -> bool:
        from sqlalchemy import delete, or_
        try:
            deal_uuid = deal_id if isinstance(deal_id, uuid.UUID) else uuid.UUID(str(deal_id))
        except (ValueError, TypeError):
            return False
        deal_id_str = str(deal_uuid)
        deal_id_hex = deal_uuid.hex
        query = delete(cls).where(or_(cls.id == deal_uuid, cls.id == deal_id_str, cls.id == deal_id_hex))
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0
    @classmethod
    async def calculate_total_value(cls, db, deal_id: str):
        from sqlalchemy import select, func, or_
        try:
            deal_uuid = deal_id if isinstance(deal_id, uuid.UUID) else uuid.UUID(str(deal_id))
            deal_id_str = str(deal_uuid)
            deal_id_hex = deal_uuid.hex
        except Exception as e:
            deal_uuid = None
            deal_id_str = str(deal_id)
            deal_id_hex = None
            print(f"Error calculating total value for deal {deal_id}: {e}")
            return 0.0

        from app.models.deal_product import DealProduct
        query = select(func.sum(DealProduct.final_price)).where(
            or_(
                DealProduct.deal_id == deal_uuid,
                DealProduct.deal_id == deal_id_str,
                DealProduct.deal_id == deal_id_hex
            )
        )
        result = await db.execute(query)
        total = result.scalar() or 0.0

        await cls.update(db, deal_id, total_contract_value=total)
        return total
