"""
Treasury Auto Rule Model - Rules for automatic transaction categorization
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text
from sqlalchemy.dialects.sqlite import CHAR

from app.database.base import Base


class TreasuryAutoRule(Base):
    __tablename__ = "treasury_auto_rules"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    match_text = Column(String(500), nullable=False)
    match_type = Column(String(50), nullable=False, default="contains")  # contains, starts_with, ends_with, regex
    action_type = Column(String(50), nullable=False)  # category, ignore, create_dds
    category_code = Column(String(255), nullable=True)
    create_dds = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<TreasuryAutoRule(name='{self.name}', match='{self.match_text}')>"
