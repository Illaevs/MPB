"""
Document registry models for consolidated outgoing documentation.
"""
import uuid

from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doc_type = Column(String(32), nullable=False)
    title = Column(String(255), nullable=False)
    number = Column(String(64))
    document_date = Column(Date)
    status = Column(String(32), default="draft")

    project_id = Column(String(36))
    counterparty_id = Column(String(36))
    our_company_id = Column(String(36))

    source_type = Column(String(64))
    source_id = Column(String(64))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class DocumentRelation(Base):
    __tablename__ = "document_relations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    related_document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    relation_type = Column(String(32), default="link")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document", foreign_keys=[document_id])
    related_document = relationship("Document", foreign_keys=[related_document_id])


class DocumentPackage(Base):
    __tablename__ = "document_packages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    package_date = Column(Date)
    status = Column(String(32), default="draft")
    project_id = Column(String(36))
    counterparty_id = Column(String(36))
    our_company_id = Column(String(36))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DocumentPackageItem(Base):
    __tablename__ = "document_package_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    package_id = Column(String(36), ForeignKey("document_packages.id"), nullable=False)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    package = relationship("DocumentPackage", backref="items")
    document = relationship("Document")


class DocumentDispatch(Base):
    __tablename__ = "document_dispatches"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("documents.id"))
    package_id = Column(String(36), ForeignKey("document_packages.id"))
    status = Column(String(32), default="sent")
    note = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("Document")
    package = relationship("DocumentPackage")


class DocumentDispatchChannel(Base):
    __tablename__ = "document_dispatch_channels"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    dispatch_id = Column(String(36), ForeignKey("document_dispatches.id"), nullable=False)
    channel = Column(String(32), nullable=False)
    channel_date = Column(Date, nullable=False)
    confirmation_file = Column(Text)
    track_number = Column(String(64))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    dispatch = relationship("DocumentDispatch", backref="channels")
