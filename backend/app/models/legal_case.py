"""
Legal work models: cases, events, and task links.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Date, Time, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class LegalCase(Base):
    __tablename__ = "legal_cases"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_number = Column(String(100))
    judge = Column(String(255))
    jurisdiction = Column(String(255))
    judge_assistant = Column(String(255))
    judge_assistant_phone = Column(String(50))
    plaintiff_id = Column(String(36), ForeignKey("companies.id"), nullable=True)
    defendant_id = Column(String(36), ForeignKey("companies.id"), nullable=True)
    description = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    plaintiff = relationship("Company", foreign_keys=[plaintiff_id])
    defendant = relationship("Company", foreign_keys=[defendant_id])

    @classmethod
    async def get_all(cls, db):
        from sqlalchemy import select
        result = await db.execute(select(cls))
        return result.scalars().all()

    @classmethod
    async def get_by_id(cls, db, case_id: str):
        from sqlalchemy import select
        result = await db.execute(select(cls).where(cls.id == str(case_id)))
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, db, **kwargs):
        now = datetime.now()
        kwargs["created_at"] = now
        kwargs["updated_at"] = now
        obj = cls(**kwargs)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    @classmethod
    async def update(cls, db, case_id: str, **kwargs):
        from sqlalchemy import update
        query = (
            update(cls)
            .where(cls.id == str(case_id))
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()
        return await cls.get_by_id(db, case_id)

    @classmethod
    async def delete(cls, db, case_id: str) -> bool:
        from sqlalchemy import delete
        result = await db.execute(delete(cls).where(cls.id == str(case_id)))
        await db.commit()
        return result.rowcount > 0


class LegalCaseEvent(Base):
    __tablename__ = "legal_case_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    legal_case_id = Column(String(36), ForeignKey("legal_cases.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(String(100), nullable=False)
    event_date = Column(Date, nullable=False)
    event_time = Column(Time, nullable=True)
    courtroom = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    legal_case = relationship("LegalCase", backref="events")

    @classmethod
    async def get_by_id(cls, db, event_id: str):
        from sqlalchemy import select
        result = await db.execute(select(cls).where(cls.id == str(event_id)))
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, db, **kwargs):
        obj = cls(**kwargs)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    @classmethod
    async def update(cls, db, event_id: str, **kwargs):
        from sqlalchemy import update
        query = (
            update(cls)
            .where(cls.id == str(event_id))
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()
        return await cls.get_by_id(db, event_id)

    @classmethod
    async def delete(cls, db, event_id: str) -> bool:
        from sqlalchemy import delete
        result = await db.execute(delete(cls).where(cls.id == str(event_id)))
        await db.commit()
        return result.rowcount > 0


class LegalCaseEventFile(Base):
    __tablename__ = "legal_case_event_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String(36), ForeignKey("legal_case_events.id", ondelete="CASCADE"), nullable=False)
    file_name = Column(String(255), nullable=False)
    yandex_path = Column(Text, nullable=False)
    storage_path = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    event = relationship("LegalCaseEvent", backref="files")

    @classmethod
    async def get_by_id(cls, db, file_id: str):
        from sqlalchemy import select
        result = await db.execute(select(cls).where(cls.id == str(file_id)))
        return result.scalar_one_or_none()

    @classmethod
    async def create(cls, db, **kwargs):
        obj = cls(**kwargs)
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj


class LegalCaseTask(Base):
    __tablename__ = "legal_case_tasks"
    __table_args__ = (
        UniqueConstraint("legal_case_id", "task_id", name="uq_legal_case_task"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    legal_case_id = Column(String(36), ForeignKey("legal_cases.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(String(36), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    legal_case = relationship("LegalCase", backref="task_links")
    task = relationship("Task")
