"""
SubcontractorStageDependency model - dependencies between subcontractor stages
"""
import uuid
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.database.base import Base
from app.models.stage_dependency import normalize_dependency_type


class SubcontractorDependencyType(str, PyEnum):
    FS = "FS"
    SS = "SS"
    FF = "FF"
    SF = "SF"


class SubcontractorStageDependency(Base):
    __tablename__ = "subcontractor_stage_dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    predecessor_id = Column(UUID(as_uuid=True), ForeignKey("subcontractor_stages.id"), nullable=False)
    successor_id = Column(UUID(as_uuid=True), ForeignKey("subcontractor_stages.id"), nullable=False)

    dependency_type = Column(String(32), default="FS")
    lag = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return (
            f"<SubcontractorStageDependency(predecessor={self.predecessor_id}, "
            f"successor={self.successor_id}, type={self.dependency_type})>"
        )
