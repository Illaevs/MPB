"""
TaskAuction model - Аукционы на задачи
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class TaskAuction(Base):
    __tablename__ = "task_auctions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Основная информация
    title = Column(String(255), nullable=False)
    description = Column(Text)
    budget = Column(Float, nullable=False)
    
    # Привязки
    deal_id = Column(String(36), ForeignKey("deals.id"), nullable=True)
    category_code = Column(String(255), nullable=True)
    
    # Настройки
    allow_custom_price = Column(Boolean, default=False)  # Можно ставить свою цену
    is_block = Column(Boolean, default=False)
    block_id = Column(String(36), ForeignKey("task_auctions.id", ondelete="CASCADE"), nullable=True)
    
    # Статус: new, awarded, cancelled
    status = Column(String(20), default="new")
    
    # Победитель
    winner_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    winner_bid_id = Column(String(36), nullable=True)  # FK to TaskAuctionBid
    
    # Созданная задача
    created_task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)
    
    # Создатель
    created_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    
    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    deal = relationship("Deal", backref="task_auctions")
    winner = relationship("User", foreign_keys=[winner_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    created_task = relationship("Task", foreign_keys=[created_task_id])
    bids = relationship("TaskAuctionBid", back_populates="auction", cascade="all, delete-orphan")
    parent = relationship("TaskAuction", remote_side=[id], back_populates="children")
    children = relationship("TaskAuction", back_populates="parent", cascade="all, delete-orphan")
    
    @classmethod
    async def get_all(
        cls,
        db,
        skip: int = 0,
        limit: int = 100,
        status: str = None,
        deal_id: str = None,
        parent_only: bool = False,
        include_children: bool = False,
    ):
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        query = select(cls)
        if status:
            if status in {"completed", "closed"}:
                query = query.where(cls.status.in_(["awarded", "cancelled"]))
            else:
                query = query.where(cls.status == status)
        if deal_id:
            query = query.where(cls.deal_id == deal_id)
        if parent_only:
            query = query.where(cls.block_id.is_(None))
        if include_children:
            query = query.options(selectinload(cls.children))
        query = query.order_by(cls.created_at.desc()).offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()
    
    @classmethod
    async def get_by_id(cls, db, auction_id: str):
        from sqlalchemy import select
        query = select(cls).where(cls.id == auction_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @classmethod
    async def create(cls, db, **kwargs):
        auction = cls(**kwargs)
        db.add(auction)
        await db.commit()
        await db.refresh(auction)
        return auction
    
    @classmethod
    async def update(cls, db, auction_id: str, **kwargs):
        from sqlalchemy import update
        query = update(cls).where(cls.id == auction_id).values(**kwargs)
        await db.execute(query)
        await db.commit()
        return await cls.get_by_id(db, auction_id)
    
    def __repr__(self):
        return f"<TaskAuction(id={self.id}, title='{self.title}', status='{self.status}')>"
