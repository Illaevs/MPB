"""
SubcontractorProduct model - products linked to subcontractor cards
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class SubcontractorProduct(Base):
    __tablename__ = "subcontractor_products"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    subcontractor_card_id = Column(String(36), ForeignKey("subcontractor_cards.id"), nullable=False)
    contract_id = Column(String(36), ForeignKey("contracts.id"))
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

    stage_id = Column(String(36), ForeignKey("subcontractor_stages.id"))
    status = Column(String(50), default="planned")
    notes = Column(Text)

    custom_properties = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    subcontractor_card = relationship("SubcontractorCard", backref="subcontractor_products")
    contract = relationship("Contract")
    product = relationship("Product", back_populates="subcontractor_products")
    stage = relationship("SubcontractorStage", backref="subcontractor_products")

    @classmethod
    async def get_all(cls, db, skip: int = 0, limit: int = 100):
        from sqlalchemy import select
        try:
            query = select(cls).offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            print(f"Database error in get_all (subcontractor products): {e}")
            return []

    @classmethod
    async def get_by_id(cls, db, item_id):
        from sqlalchemy import select, or_
        try:
            item_uuid = item_id if isinstance(item_id, uuid.UUID) else uuid.UUID(str(item_id))
        except (ValueError, TypeError):
            raise ValueError("subcontractor_product_id must be a string or UUID")

        item_id_str = str(item_uuid)
        item_id_hex = item_uuid.hex
        query = select(cls).where(or_(cls.id == item_uuid, cls.id == item_id_str, cls.id == item_id_hex))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_subcontractor_card(cls, db, card_id: str):
        from sqlalchemy import select, or_
        from sqlalchemy.orm import selectinload
        try:
            card_uuid = card_id if isinstance(card_id, uuid.UUID) else uuid.UUID(str(card_id))
        except (ValueError, TypeError):
            return []
        card_id_str = str(card_uuid)
        card_id_hex = card_uuid.hex
        query = select(cls).options(selectinload(cls.product)).where(
            or_(
                cls.subcontractor_card_id == card_uuid,
                cls.subcontractor_card_id == card_id_str,
                cls.subcontractor_card_id == card_id_hex
            )
        )
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_by_product(cls, db, product_id: str):
        from sqlalchemy import select, or_
        try:
            product_uuid = product_id if isinstance(product_id, uuid.UUID) else uuid.UUID(str(product_id))
        except (ValueError, TypeError):
            return []
        product_id_str = str(product_uuid)
        product_id_hex = product_uuid.hex
        query = select(cls).where(
            or_(cls.product_id == product_uuid, cls.product_id == product_id_str, cls.product_id == product_id_hex)
        )
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def create(cls, db, **kwargs):
        now = datetime.now()
        kwargs['created_at'] = now
        kwargs['updated_at'] = now
        if 'subcontractor_card_id' in kwargs and isinstance(kwargs['subcontractor_card_id'], uuid.UUID):
            kwargs['subcontractor_card_id'] = str(kwargs['subcontractor_card_id'])

        bind = db.get_bind()
        is_sqlite = bool(bind and bind.dialect.name == "sqlite")
        if is_sqlite:
            for key in ("product_id", "stage_id", "contract_id", "id"):
                if key in kwargs and kwargs[key] is not None:
                    try:
                        u = kwargs[key] if isinstance(kwargs[key], uuid.UUID) else uuid.UUID(str(kwargs[key]))
                        kwargs[key] = u.hex
                    except (ValueError, TypeError):
                        pass

        quantity = kwargs.get('quantity', 1.0)
        unit_price = kwargs.get('unit_price', 0.0)
        discount_percent = kwargs.get('discount_percent', 0.0)
        discount_amount = kwargs.get('discount_amount', 0.0)
        tax_rate = kwargs.get('tax_rate', 0.0)

        total_price = quantity * unit_price
        discount_from_percent = total_price * (discount_percent / 100)
        total_discount = discount_from_percent + discount_amount
        subtotal_after_discount = total_price - total_discount
        tax_amount = subtotal_after_discount * (tax_rate / 100)
        final_price = subtotal_after_discount + tax_amount

        kwargs['total_price'] = total_price
        kwargs['discount_total'] = total_discount
        kwargs['tax_amount'] = tax_amount
        kwargs['final_price'] = final_price

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
            raise ValueError("subcontractor_product_id must be a string or UUID")

        for key in ("stage_id", "contract_id", "subcontractor_card_id", "product_id"):
            if key in kwargs and isinstance(kwargs[key], uuid.UUID):
                kwargs[key] = str(kwargs[key])

        if 'custom_price' in kwargs and kwargs['custom_price'] is not None:
            kwargs['unit_price'] = kwargs['custom_price']

        if any(key in kwargs for key in ['quantity', 'unit_price', 'custom_price', 'discount_percent', 'discount_amount', 'tax_rate']):
            current = await cls.get_by_id(db, item_uuid)
            if current:
                quantity = kwargs.get('quantity', current.quantity)
                unit_price = kwargs.get('unit_price')
                if unit_price is None:
                    unit_price = current.unit_price
                discount_percent = kwargs.get('discount_percent', current.discount_percent)
                discount_amount = kwargs.get('discount_amount', current.discount_amount)
                tax_rate = kwargs.get('tax_rate', current.tax_rate)

                total_price = quantity * unit_price
                discount_from_percent = total_price * (discount_percent / 100)
                total_discount = discount_from_percent + discount_amount
                subtotal_after_discount = total_price - total_discount
                tax_amount = subtotal_after_discount * (tax_rate / 100)
                final_price = subtotal_after_discount + tax_amount

                kwargs['total_price'] = total_price
                kwargs['discount_total'] = total_discount
                kwargs['tax_amount'] = tax_amount
                kwargs['final_price'] = final_price

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
        return await cls.get_by_id(db, item_id)

    @classmethod
    async def delete(cls, db, item_id) -> bool:
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
