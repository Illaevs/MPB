"""
Tender model - tenders per deal product.
"""
import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.database.base import Base


class Tender(Base):
    __tablename__ = "tenders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    deal_product_id = Column(String(36), ForeignKey("deal_products.id"), nullable=False)
    deal_id = Column(String(36), ForeignKey("deals.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)
    direction_id = Column(String(36))  # product category id

    status = Column(String(20), default="new")  # new, review, archived
    winner_company_id = Column(String(36), ForeignKey("companies.id"))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Tender(id={self.id}, deal_product_id={self.deal_product_id}, status={self.status})>"
