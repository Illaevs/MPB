"""
CompanyUserLink model - company links for leaders/employees/customers.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class CompanyUserLink(Base):
    __tablename__ = "company_user_links"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    company_id = Column(String(36), ForeignKey("companies.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    link_type = Column(String(20), nullable=False)  # leader / employee / customer

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    company = relationship("Company")
    user = relationship("User")

    @classmethod
    async def get_by_company(cls, db, company_id: str, link_type: str = None):
        from sqlalchemy import select
        query = select(cls).where(cls.company_id == str(company_id))
        if link_type:
            query = query.where(cls.link_type == link_type)
        result = await db.execute(query)
        return result.scalars().all()
