"""
Models for commercial proposals (КП).
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class KpTemplate(Base):
    __tablename__ = "kp_templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    docx_url = Column(Text, nullable=False)
    pdf_url = Column(Text)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    bindings = relationship("KpTemplateBinding", back_populates="template", cascade="all, delete-orphan")


class KpTemplateBinding(Base):
    __tablename__ = "kp_template_bindings"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id = Column(String(36), ForeignKey("kp_templates.id"), nullable=False)
    our_company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    template = relationship("KpTemplate", back_populates="bindings")


class KpDocument(Base):
    __tablename__ = "kp_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=False)
    number_seq = Column(Integer, nullable=False)
    number_display = Column(String(50), nullable=False)
    status = Column(String(50), default="draft")
    current_version = Column(Integer, default=1)
    our_company_id = Column(String(36), ForeignKey("companies.id"))
    template_id = Column(String(36), ForeignKey("kp_templates.id"))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    lead = relationship("Lead", foreign_keys=[lead_id])
    our_company = relationship("Company", foreign_keys=[our_company_id])
    template = relationship("KpTemplate", foreign_keys=[template_id])
    versions = relationship("KpVersion", back_populates="kp", cascade="all, delete-orphan", order_by="KpVersion.version.desc()")


class KpVersion(Base):
    __tablename__ = "kp_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    kp_id = Column(String(36), ForeignKey("kp_documents.id"), nullable=False)
    version = Column(Integer, nullable=False)
    docx_url = Column(Text)
    pdf_url = Column(Text)
    total_amount = Column(Float, default=0.0)
    vat_amount = Column(Float, default=0.0)
    total_text = Column(Text)
    vat_text = Column(Text)
    template_id = Column(String(36), ForeignKey("kp_templates.id"))

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    kp = relationship("KpDocument", back_populates="versions")
    template = relationship("KpTemplate")
