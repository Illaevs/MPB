"""
Approval workflow models.
"""
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ApprovalTemplate(Base):
    __tablename__ = "approval_templates"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    code = Column(String(64), nullable=True, index=True)
    description = Column(Text, nullable=True)
    entity_type = Column(String(64), nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    tags = Column(JSON, default=list, nullable=True)
    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    steps = relationship(
        "ApprovalTemplateStep",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="ApprovalTemplateStep.step_order",
    )


class ApprovalTemplateStep(Base):
    __tablename__ = "approval_template_steps"

    id = Column(String(36), primary_key=True, default=_uuid)
    template_id = Column(String(36), ForeignKey("approval_templates.id"), nullable=False, index=True)
    parent_step_id = Column(String(36), ForeignKey("approval_template_steps.id"), nullable=True, index=True)
    step_order = Column(Integer, nullable=False, default=1)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assignee_type = Column(String(16), nullable=False, default="user")
    assignee_user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    assignee_role_id = Column(String(36), ForeignKey("roles.id"), nullable=True, index=True)
    is_required = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    template = relationship("ApprovalTemplate", back_populates="steps")
    parent = relationship("ApprovalTemplateStep", remote_side=[id], uselist=False)


class ApprovalInstance(Base):
    __tablename__ = "approval_instances"

    id = Column(String(36), primary_key=True, default=_uuid)
    template_id = Column(String(36), ForeignKey("approval_templates.id"), nullable=False, index=True)
    template_name = Column(String(255), nullable=False)
    template_version = Column(DateTime(timezone=True), nullable=True)
    entity_type = Column(String(64), nullable=False, index=True)
    entity_id = Column(String(64), nullable=False, index=True)
    entity_label = Column(String(255), nullable=True)
    status = Column(String(32), nullable=False, default="pending", index=True)
    current_step_id = Column(String(36), nullable=True, index=True)
    started_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    completed_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    completed_comment = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    template = relationship("ApprovalTemplate")
    steps = relationship(
        "ApprovalInstanceStep",
        back_populates="instance",
        cascade="all, delete-orphan",
        order_by="ApprovalInstanceStep.step_order",
    )
    actions = relationship(
        "ApprovalActionLog",
        back_populates="instance",
        cascade="all, delete-orphan",
        order_by="ApprovalActionLog.created_at",
    )


class ApprovalInstanceStep(Base):
    __tablename__ = "approval_instance_steps"

    id = Column(String(36), primary_key=True, default=_uuid)
    instance_id = Column(String(36), ForeignKey("approval_instances.id"), nullable=False, index=True)
    template_step_id = Column(String(36), nullable=True, index=True)
    parent_template_step_id = Column(String(36), nullable=True, index=True)
    step_order = Column(Integer, nullable=False, default=1)
    depth = Column(Integer, nullable=False, default=0)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assignee_type = Column(String(16), nullable=False, default="user")
    assignee_user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    assignee_role_id = Column(String(36), ForeignKey("roles.id"), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="waiting", index=True)
    is_required = Column(Boolean, default=True)
    acted_by = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    acted_at = Column(DateTime(timezone=True), nullable=True)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    instance = relationship("ApprovalInstance", back_populates="steps")


class ApprovalActionLog(Base):
    __tablename__ = "approval_action_logs"

    id = Column(String(36), primary_key=True, default=_uuid)
    instance_id = Column(String(36), ForeignKey("approval_instances.id"), nullable=False, index=True)
    instance_step_id = Column(String(36), ForeignKey("approval_instance_steps.id"), nullable=True, index=True)
    action = Column(String(32), nullable=False, index=True)
    actor_user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    comment = Column(Text, nullable=True)
    payload_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    instance = relationship("ApprovalInstance", back_populates="actions")
