import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class ContractDocumentProductLink(Base):
    __tablename__ = "contract_document_product_links"
    __table_args__ = (
        UniqueConstraint("contract_document_id", "deal_product_id", name="uq_contract_document_product"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contract_document_id = Column(String(36), ForeignKey("contract_documents.id"), nullable=False, index=True)
    deal_product_id = Column(String(36), ForeignKey("deal_products.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    document = relationship("ContractDocument", backref="product_links")
    deal_product = relationship("DealProduct")
