"""
Document template models.
"""
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class DocumentTemplate(Base):
    __tablename__ = "document_templates"

    id = Column(String(36), primary_key=True, default=_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    module = Column(String(64), nullable=False, index=True)
    document_kind = Column(String(64), nullable=False, index=True)
    our_company_key = Column(String(64), nullable=True, index=True)
    binding_type = Column(String(64), default="global", index=True)
    binding_id = Column(String(36), nullable=True, index=True)
    status = Column(String(32), default="draft", index=True)
    is_active = Column(Boolean, default=False, index=True)
    current_version_id = Column(String(36), nullable=True)
    fields_json = Column(JSON, default=list)
    unknown_fields_json = Column(JSON, default=list)

    # template_v2 (new redesign): HTML layout with [data-locked] / [data-placeholder] /
    # [data-editable] sections. When set, the document renders as an inline
    # online editor instead of being driven by a DOCX file.
    layout_html = Column(Text, nullable=True)
    # Editable region config: [{key, label, default_html, allowed_marks}].
    # MVP: a single entry with key="body".
    editable_regions_json = Column(JSON, default=list)
    # Field schema for the right-side parameters panel:
    # [{key, label, type, source, validation, required}]. Drives the form
    # that fills placeholder chips in `layout_html`.
    placeholder_fields_json = Column(JSON, default=list)

    created_by = Column(String(36), nullable=True)
    updated_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    versions = relationship(
        "DocumentTemplateVersion",
        back_populates="template",
        cascade="all, delete-orphan",
    )


class DocumentTemplateVersion(Base):
    __tablename__ = "document_template_versions"

    id = Column(String(36), primary_key=True, default=_uuid)
    template_id = Column(String(36), ForeignKey("document_templates.id"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    file_name = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer, default=0)
    content_type = Column(String(255), nullable=True)
    fields_json = Column(JSON, default=list)
    unknown_fields_json = Column(JSON, default=list)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    template = relationship("DocumentTemplate", back_populates="versions")
