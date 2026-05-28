"""
UploadJob model - async upload queue for Yandex Disk.
"""
import uuid

from sqlalchemy import Column, String, DateTime, Integer, Text, JSON
from sqlalchemy.sql import func

from app.database.base import Base


class UploadJob(Base):
    __tablename__ = "upload_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(String(32), default="queued")
    module = Column(String(64))
    entity_id = Column(String(64))
    file_kind = Column(String(32))
    file_name = Column(String(255))
    temp_path = Column(Text)
    target_path = Column(Text)
    size_bytes = Column(Integer)
    error_message = Column(Text)
    created_by = Column(String(36))
    meta = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
