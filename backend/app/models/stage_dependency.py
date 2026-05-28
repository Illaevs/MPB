"""
StageDependency model - Связи между этапами (Gantt dependencies)
"""
import uuid
from datetime import datetime
from typing import Optional
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class DependencyType(str, PyEnum):
    FS = "FS"  # Finish-to-Start (окончание-начало)
    SS = "SS"  # Start-to-Start (начало-начало)
    FF = "FF"  # Finish-to-Finish (окончание-окончание)
    SF = "SF"  # Start-to-Finish (начало-окончание)


DEPENDENCY_TYPE_ALIASES = {
    "finish_to_start": "FS",
    "start_to_start": "SS",
    "finish_to_finish": "FF",
    "start_to_finish": "SF",
}
VALID_DEPENDENCY_TYPES = {"FS", "SS", "FF", "SF"}


def normalize_dependency_type(value: Optional[str]) -> str:
    normalized = str(value or "FS").strip()
    if not normalized:
        return "FS"
    alias = DEPENDENCY_TYPE_ALIASES.get(normalized.lower())
    if alias:
        return alias
    upper = normalized.upper()
    return upper if upper in VALID_DEPENDENCY_TYPES else "FS"


class StageDependency(Base):
    __tablename__ = "stage_dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Предшественник (от которого зависит)
    predecessor_id = Column(UUID(as_uuid=True), ForeignKey("stages.id"), nullable=False)

    # Последователь (который зависит)
    successor_id = Column(UUID(as_uuid=True), ForeignKey("stages.id"), nullable=False)

    # Тип связи
    dependency_type = Column(String(32), default="FS")

    # Временной лаг (задержка или опережение) в днях
    lag = Column(Integer, default=0)

    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Связи через backref в Stage

    def __repr__(self):
        return f"<StageDependency(predecessor={self.predecessor_id}, successor={self.successor_id}, type={self.dependency_type})>"
