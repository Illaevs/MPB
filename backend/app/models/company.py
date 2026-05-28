"""
Company model - Контрагенты (Заказчики, Подрядчики)
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Enum, Float, Text, JSON, Boolean
from sqlalchemy.sql import func

from app.database.base import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inn = Column(String(12), unique=True, nullable=False, index=True)  # ИНН для маппинга банковских выписок

    # Тип контрагента
    type = Column(Enum("customer", "subcontractor", "internal", "contractor", "service", "other"), nullable=False, default="customer")

    # Основная информация
    name = Column(String(255), nullable=False)
    short_name = Column(String(255))  # Сокращенное наименование
    full_name = Column(String(500))  # Полное наименование
    kpp = Column(String(20))
    contact_person = Column(String(255))
    phone = Column(String(50))
    email = Column(String(255))
    phones = Column(JSON, default=list)
    emails = Column(JSON, default=list)
    contacts = Column(JSON, default=list)  # [{name, position, phone, email}]
    bank_accounts = Column(JSON, default=list)

    # Адрес
    address = Column(Text)

    # Рейтинги для подрядчиков
    rating_speed = Column(Float, default=0.0)      # Индекс скорости выполнения
    rating_quality = Column(Float, default=0.0)    # Индекс качества

    # Направления работ (id разделов каталога), пользовательский рейтинг и примечание
    work_directions = Column(JSON, default=list)   # [category_id, ...]
    rating = Column(Float, default=0.0)            # 0..5, шаг 0.5
    note = Column(Text)                            # Примечание

    # Дефолтная "наша компания" — выставляется ровно одной internal-компанией.
    # Используется как fallback для our_company_id в leads/deals/kp/documents,
    # чтобы UI мог не показывать выбор, пока компания одна.
    is_default = Column(Boolean, default=False, nullable=False)

    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @classmethod
    async def get_all(cls, db, skip: int = 0, limit: int = 100, search: str = None, company_type: str = None, sort_by: str = "name", sort_dir: str = "asc"):
        """Получить список компаний с поиском и фильтрами"""
        from sqlalchemy import select, or_, asc, desc, func
        try:
            query = select(cls)
            if company_type:
                types = [t.strip() for t in company_type.split(",") if t.strip()]
                if types:
                    query = query.where(cls.type.in_(types))

            result = await db.execute(query)
            companies = result.scalars().all()

            if search:
                tokens = [t.strip().casefold() for t in search.split() if t.strip()]

                def matches(company):
                    fields = [
                        company.name or "",
                        company.short_name or "",
                        company.full_name or "",
                        company.inn or "",
                        company.kpp or "",
                        company.contact_person or "",
                    ]
                    folded = [value.casefold() for value in fields]
                    for token in tokens:
                        if not any(token in value for value in folded):
                            return False
                    return True

                companies = [company for company in companies if matches(company)]

            sort_column = sort_by if hasattr(cls, sort_by) else "name"

            def sort_key(company):
                value = getattr(company, sort_column, "")
                if isinstance(value, str):
                    return value.casefold()
                return value or ""

            companies = sorted(companies, key=sort_key, reverse=(sort_dir == "desc"))
            return companies[skip:skip + limit]
        except Exception as e:
            print(f"Database error in get_all: {e}")
            return []

    @classmethod
    async def get_by_id(cls, db, company_id: str):
        """Получить компанию по ID"""
        from sqlalchemy import select
        query = select(cls).where(cls.id == str(company_id))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_count(cls, db, search: str = None, company_type: str = None) -> int:
        """Получить общее количество компаний с фильтрами"""
        from sqlalchemy import select, func, or_
        try:
            query = select(cls)
            if company_type:
                types = [t.strip() for t in company_type.split(",") if t.strip()]
                if types:
                    query = query.where(cls.type.in_(types))

            result = await db.execute(query)
            companies = result.scalars().all()

            if search:
                tokens = [t.strip().casefold() for t in search.split() if t.strip()]

                def matches(company):
                    fields = [
                        company.name or "",
                        company.short_name or "",
                        company.full_name or "",
                        company.inn or "",
                        company.kpp or "",
                        company.contact_person or "",
                    ]
                    folded = [value.casefold() for value in fields]
                    for token in tokens:
                        if not any(token in value for value in folded):
                            return False
                    return True

                companies = [company for company in companies if matches(company)]

            return len(companies)
        except Exception as e:
            print(f"Database error in get_count: {e}")
            return 0

    @classmethod
    async def get_by_inn(cls, db, inn: str):
        """Fetch company by INN."""
        from sqlalchemy import select
        if not inn:
            return None
        query = select(cls).where(cls.inn == inn)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_default_our_company_id(cls, db) -> Optional[str]:
        """Return the id of the company flagged as the system-wide
        "наша компания" default, or None if none is set.

        Roughly: the value that should land in lead/deal/document
        `our_company_id` when the UI doesn't ask the user to pick.
        Used by router create/update endpoints so the form can omit
        the selector entirely.
        """
        from sqlalchemy import select
        query = select(cls.id).where(cls.is_default == True, cls.type == "internal").limit(1)
        result = await db.execute(query)
        value = result.scalar_one_or_none()
        return str(value) if value else None

    @classmethod
    async def get_default_our_company(cls, db):
        """Same as get_default_our_company_id but returns the full row."""
        from sqlalchemy import select
        query = select(cls).where(cls.is_default == True, cls.type == "internal").limit(1)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def set_default(cls, db, company_id: str) -> "Company":
        """Mark this company as the default our_company; clear the flag
        on everyone else atomically. Caller must ensure the company exists
        and is type='internal'."""
        from sqlalchemy import update as _update
        # Clear all first, then set the chosen one. Single transaction.
        await db.execute(_update(cls).values(is_default=False))
        await db.execute(
            _update(cls).where(cls.id == str(company_id)).values(is_default=True)
        )
        await db.commit()
        return await cls.get_by_id(db, company_id)

    @classmethod
    async def create(cls, db, **kwargs):
        """Создать новую компанию"""
        from datetime import datetime
        # Set created_at and updated_at explicitly
        now = datetime.now()
        kwargs['created_at'] = now
        kwargs['updated_at'] = now
        company = cls(**kwargs)
        db.add(company)
        await db.commit()
        await db.refresh(company)
        return company

    @classmethod
    async def update(cls, db, company_id: str, **kwargs):
        """Обновить компанию"""
        from sqlalchemy import update
        query = (
            update(cls)
            .where(cls.id == str(company_id))
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()

        # Получить обновленный объект
        return await cls.get_by_id(db, company_id)

    @classmethod
    async def delete(cls, db, company_id: str) -> bool:
        """Удалить компанию"""
        from sqlalchemy import delete
        from sqlalchemy import or_
        if not company_id:
            return False
        variants = [str(company_id)]
        try:
            parsed = company_id if isinstance(company_id, uuid.UUID) else uuid.UUID(str(company_id))
            variants.extend([str(parsed), parsed.hex])
        except (ValueError, TypeError):
            pass
        query = delete(cls).where(or_(*[cls.id == value for value in variants]))
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}', inn='{self.inn}')>"
