"""
LeadProduct model.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class LeadProduct(Base):
    __tablename__ = "lead_products"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    lead_id = Column(String(36), ForeignKey("leads.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)

    custom_name = Column(String(255))
    custom_price = Column(Float)

    quantity = Column(Float, nullable=False, default=1.0)
    unit = Column(String(50))

    unit_price = Column(Float, nullable=False)
    discount_percent = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    tax_rate = Column(Float, default=0.0)
    currency = Column(String(3), default="RUB")

    total_price = Column(Float)
    discount_total = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    final_price = Column(Float)

    notes = Column(Text)
    custom_properties = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    lead = relationship("Lead", backref="lead_products")
    product = relationship("Product", back_populates="lead_products")

    @classmethod
    async def get_by_id(cls, db, item_id):
        from sqlalchemy import select, or_
        try:
            item_uuid = item_id if isinstance(item_id, uuid.UUID) else uuid.UUID(str(item_id))
        except (ValueError, TypeError):
            raise ValueError("lead_product_id must be a string or UUID")

        item_id_str = str(item_uuid)
        item_id_hex = item_uuid.hex
        query = select(cls).where(or_(cls.id == item_uuid, cls.id == item_id_str, cls.id == item_id_hex))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_lead(cls, db, lead_id: str):
        from sqlalchemy import select, or_
        from sqlalchemy.orm import selectinload
        try:
            lead_uuid = lead_id if isinstance(lead_id, uuid.UUID) else uuid.UUID(str(lead_id))
        except (ValueError, TypeError):
            return []
        lead_id_str = str(lead_uuid)
        lead_id_hex = lead_uuid.hex
        query = select(cls).options(selectinload(cls.product)).where(
            or_(cls.lead_id == lead_uuid, cls.lead_id == lead_id_str, cls.lead_id == lead_id_hex)
        )
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def create(cls, db, **kwargs):
        now = datetime.now()
        kwargs["created_at"] = now
        kwargs["updated_at"] = now

        bind = db.get_bind()
        is_sqlite = bool(bind and bind.dialect.name == "sqlite")
        if is_sqlite:
            for key in ("lead_id", "product_id", "id"):
                if key in kwargs and kwargs[key] is not None:
                    try:
                        u = kwargs[key] if isinstance(kwargs[key], uuid.UUID) else uuid.UUID(str(kwargs[key]))
                        kwargs[key] = u.hex
                    except (ValueError, TypeError):
                        pass

        quantity = kwargs.get("quantity", 1.0)
        unit_price = kwargs.get("unit_price", 0.0)
        discount_percent = kwargs.get("discount_percent", 0.0)
        discount_amount = kwargs.get("discount_amount", 0.0)
        tax_rate = kwargs.get("tax_rate", 0.0)

        total_price = quantity * unit_price
        discount_from_percent = total_price * (discount_percent / 100)
        total_discount = discount_from_percent + discount_amount
        subtotal_after_discount = total_price - total_discount
        tax_amount = subtotal_after_discount * (tax_rate / 100)
        final_price = subtotal_after_discount + tax_amount

        kwargs["total_price"] = total_price
        kwargs["discount_total"] = total_discount
        kwargs["tax_amount"] = tax_amount
        kwargs["final_price"] = final_price

        item = cls(**kwargs)
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item

    @classmethod
    async def update(cls, db, item_id, **kwargs):
        from sqlalchemy import update, or_

        try:
            item_uuid = item_id if isinstance(item_id, uuid.UUID) else uuid.UUID(str(item_id))
        except (ValueError, TypeError):
            raise ValueError("lead_product_id must be a string or UUID")

        if "custom_price" in kwargs and kwargs["custom_price"] is not None:
            kwargs["unit_price"] = kwargs["custom_price"]

        if any(key in kwargs for key in ["quantity", "unit_price", "custom_price", "discount_percent", "discount_amount", "tax_rate"]):
            current = await cls.get_by_id(db, item_uuid)
            if current:
                quantity = kwargs.get("quantity", current.quantity)
                unit_price = kwargs.get("unit_price")
                if unit_price is None:
                    unit_price = current.unit_price
                discount_percent = kwargs.get("discount_percent", current.discount_percent)
                discount_amount = kwargs.get("discount_amount", current.discount_amount)
                tax_rate = kwargs.get("tax_rate", current.tax_rate)

                total_price = quantity * unit_price
                discount_from_percent = total_price * (discount_percent / 100)
                total_discount = discount_from_percent + discount_amount
                subtotal_after_discount = total_price - total_discount
                tax_amount = subtotal_after_discount * (tax_rate / 100)
                final_price = subtotal_after_discount + tax_amount

                kwargs["total_price"] = total_price
                kwargs["discount_total"] = total_discount
                kwargs["tax_amount"] = tax_amount
                kwargs["final_price"] = final_price

        item_id_str = str(item_uuid)
        item_id_hex = item_uuid.hex
        query = (
            update(cls)
            .where(or_(cls.id == item_uuid, cls.id == item_id_str, cls.id == item_id_hex))
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()
        return await cls.get_by_id(db, item_uuid)

    @classmethod
    async def delete(cls, db, item_id: str) -> bool:
        from sqlalchemy import delete, or_
        try:
            item_uuid = item_id if isinstance(item_id, uuid.UUID) else uuid.UUID(str(item_id))
        except (ValueError, TypeError):
            return False
        item_id_str = str(item_uuid)
        item_id_hex = item_uuid.hex
        query = delete(cls).where(or_(cls.id == item_uuid, cls.id == item_id_str, cls.id == item_id_hex))
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    def __repr__(self):
        return f"<LeadProduct(lead={self.lead_id}, product={self.product_id}, quantity={self.quantity})>"
