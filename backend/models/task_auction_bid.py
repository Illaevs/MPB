"""
TaskAuctionBid model - Заявки на аукцион
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class TaskAuctionBid(Base):
    __tablename__ = "task_auction_bids"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Связь с аукционом
    auction_id = Column(String(36), ForeignKey("task_auctions.id", ondelete="CASCADE"), nullable=False)
    
    # Кто подал заявку
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    # Предложенная цена (если allow_custom_price=True, иначе = budget аукциона)
    bid_price = Column(Float, nullable=False)

    # Для блоков: заявка на весь блок + подзадачи
    covers_children = Column(Boolean, default=False)
    
    # Комментарий к заявке (опционально)
    comment = Column(String(500), nullable=True)
    
    # Метаданные
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Связи
    auction = relationship("TaskAuction", back_populates="bids")
    user = relationship("User")
    
    @classmethod
    async def get_by_auction(cls, db, auction_id: str):
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        query = select(cls).where(cls.auction_id == auction_id).options(
            selectinload(cls.user)
        ).order_by(cls.bid_price.asc())
        result = await db.execute(query)
        return result.scalars().all()
    
    @classmethod
    async def get_by_user_and_auction(cls, db, user_id: str, auction_id: str):
        from sqlalchemy import select
        query = select(cls).where(cls.user_id == user_id, cls.auction_id == auction_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @classmethod
    async def get_by_id(cls, db, bid_id: str):
        from sqlalchemy import select
        query = select(cls).where(cls.id == bid_id)
        result = await db.execute(query)
        return result.scalar_one_or_none()
    
    @classmethod
    async def create(cls, db, **kwargs):
        bid = cls(**kwargs)
        db.add(bid)
        await db.commit()
        await db.refresh(bid)
        return bid
    
    @classmethod
    async def update(cls, db, bid_id: str, **kwargs):
        from sqlalchemy import update
        query = update(cls).where(cls.id == bid_id).values(**kwargs)
        await db.execute(query)
        await db.commit()
        return await cls.get_by_id(db, bid_id)
    
    @classmethod
    async def delete(cls, db, bid_id: str):
        from sqlalchemy import delete
        query = delete(cls).where(cls.id == bid_id)
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0
    
    def __repr__(self):
        return f"<TaskAuctionBid(id={self.id}, auction_id={self.auction_id}, bid_price={self.bid_price})>"
