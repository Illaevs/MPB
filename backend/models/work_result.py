"""
WorkResult model - Результаты выполнения работ
"""
import uuid
from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum
from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, Enum as SqlEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class WorkResultStatus(str, PyEnum):
    PREPARATION = "preparation"  # Загрузка
    REVIEW = "review"           # На проверке у ГИПа
    REVISION = "revision"       # Возврат на доработку
    ACCEPTED = "accepted"       # Принято


class WorkResult(Base):
    __tablename__ = "work_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Связь с этапом
    stage_id = Column(UUID(as_uuid=True), ForeignKey("stages.id"), nullable=False)

    # Связь с подрядчиком
    subcontractor_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)

    # Версионность
    version = Column(Integer, default=1, nullable=False)

    # Статус
    status = Column(SqlEnum("preparation", "review", "revision", "accepted"), default="preparation")

    # Файлы
    s3_object_key = Column(String(500))  # Путь к архиву в S3

    # Комментарии
    comment_sub = Column(Text)  # От подрядчика
    comment_gip = Column(Text)  # Резолюция ГИПа

    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Связи
    stage = relationship("Stage")
    subcontractor = relationship("Company")

    def __repr__(self):
        return f"<WorkResult(stage={self.stage_id}, subcontractor={self.subcontractor_id}, version={self.version}, status={self.status})>"
