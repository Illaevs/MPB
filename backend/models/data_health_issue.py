import uuid

from sqlalchemy import Column, DateTime, JSON, String, Text
from sqlalchemy.sql import func

from app.database.base import Base


class DataHealthIssue(Base):
    __tablename__ = "data_health_issues"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    fingerprint = Column(String(64), nullable=False, unique=True, index=True)

    deal_id = Column(String(36), index=True)
    scope_type = Column(String(50), nullable=False, index=True)
    scope_id = Column(String(36), index=True)

    issue_type = Column(String(100), nullable=False, index=True)
    module = Column(String(50), nullable=False, index=True)
    severity = Column(String(20), default="warning", index=True)
    status = Column(String(20), default="open", index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    payload_json = Column(JSON, default=dict)

    ignored_reason = Column(Text)
    ignored_until = Column(DateTime(timezone=True))
    ignored_by_user_id = Column(String(36))
    ignored_at = Column(DateTime(timezone=True))

    first_detected_at = Column(DateTime(timezone=True), server_default=func.now())
    last_detected_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
