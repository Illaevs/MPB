"""
DealProduct model.
"""
import uuid
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from sqlalchemy import Boolean, Column, String, Float, ForeignKey, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class DealProduct(Base):
    __tablename__ = "deal_products"
    _MONEY_QUANT = Decimal("0.01")

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    deal_id = Column(String(36), ForeignKey("deals.id"), nullable=False)
    product_id = Column(String(36), ForeignKey("products.id"), nullable=False)

    custom_name = Column(String(255))
    custom_price = Column(Float)

    quantity = Column(Float, nullable=False, default=1.0)
    unit = Column(String(50))

    unit_price = Column(Float, nullable=False)
    discount_percent = Column(Float, default=0.0)
    discount_amount = Column(Float, default=0.0)
    tax_rate = Column(Float, default=0.0)
    tax_included = Column(Boolean, default=False)
    currency = Column(String(3), default="RUB")

    total_price = Column(Float)
    discount_total = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    final_price = Column(Float)

    stage_id = Column(String(36), ForeignKey("stages.id"))
    status = Column(String(50), default="planned")

    notes = Column(Text)
    custom_properties = Column(JSON, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    deal = relationship("Deal", backref="deal_products")
    product = relationship("Product", back_populates="deal_products")

    @classmethod
    def _round_money(cls, value):
        if value is None:
            return None
        return float(Decimal(str(value)).quantize(cls._MONEY_QUANT, rounding=ROUND_HALF_UP))

    @staticmethod
    def _coerce_bool(value):
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(value)

    @classmethod
    def _calculate_money_fields(
        cls,
        *,
        quantity,
        unit_price,
        discount_percent,
        discount_amount,
        tax_rate,
        tax_included=False,
    ):
        quantity = float(quantity or 0.0)
        unit_price = cls._round_money(unit_price or 0.0)
        discount_percent = float(discount_percent or 0.0)
        discount_amount = cls._round_money(discount_amount or 0.0)
        tax_rate = float(tax_rate or 0.0)
        tax_included = cls._coerce_bool(tax_included)

        entered_total = cls._round_money(quantity * unit_price)
        discount_from_percent = cls._round_money(entered_total * (discount_percent / 100.0))
        total_discount = cls._round_money(discount_from_percent + discount_amount)
        amount_after_discount = cls._round_money(entered_total - total_discount)

        if tax_included and tax_rate > 0:
            final_price = amount_after_discount
            tax_amount = cls._round_money(final_price * (tax_rate / (100.0 + tax_rate)))
            total_price = cls._round_money(final_price - tax_amount)
        else:
            total_price = amount_after_discount
            tax_amount = cls._round_money(total_price * (tax_rate / 100.0))
            final_price = cls._round_money(total_price + tax_amount)

        return {
            "unit_price": unit_price,
            "discount_amount": discount_amount,
            "total_price": total_price,
            "discount_total": total_discount,
            "tax_amount": tax_amount,
            "final_price": final_price,
        }

    @classmethod
    async def get_all(cls, db, skip: int = 0, limit: int = 100):
        from sqlalchemy import select
        try:
            query = select(cls).offset(skip).limit(limit)
            result = await db.execute(query)
            return result.scalars().all()
        except Exception as e:
            print(f"Database error in get_all: {e}")
            return []

    @classmethod
    async def get_by_id(cls, db, deal_product_id):
        from sqlalchemy import select, or_
        from sqlalchemy.orm import selectinload
        try:
            deal_product_uuid = deal_product_id if isinstance(deal_product_id, uuid.UUID) else uuid.UUID(str(deal_product_id))
        except (ValueError, TypeError):
            raise ValueError("deal_product_id must be a string or UUID")

        deal_id_str = str(deal_product_uuid)
        deal_id_hex = deal_product_uuid.hex
        query = select(cls).options(selectinload(cls.product)).where(or_(cls.id == deal_product_uuid, cls.id == deal_id_str, cls.id == deal_id_hex))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_deal(cls, db, deal_id: str):
        from sqlalchemy import select, or_
        from sqlalchemy.orm import selectinload
        try:
            deal_uuid = deal_id if isinstance(deal_id, uuid.UUID) else uuid.UUID(str(deal_id))
        except (ValueError, TypeError):
            return []
        deal_id_str = str(deal_uuid)
        deal_id_hex = deal_uuid.hex
        query = select(cls).options(selectinload(cls.product)).where(
            or_(cls.deal_id == deal_uuid, cls.deal_id == deal_id_str, cls.deal_id == deal_id_hex)
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

        bind = db.get_bind()
        is_sqlite = bool(bind and bind.dialect.name == "sqlite")
        if is_sqlite:
            for key in ("deal_id", "product_id", "stage_id", "id"):
                if key in kwargs and kwargs[key] is not None:
                    try:
                        u = kwargs[key] if isinstance(kwargs[key], uuid.UUID) else uuid.UUID(str(kwargs[key]))
                        kwargs[key] = u.hex
                    except (ValueError, TypeError):
                        pass

        if 'custom_price' in kwargs and kwargs['custom_price'] is not None:
            kwargs['custom_price'] = cls._round_money(kwargs['custom_price'])
            kwargs['unit_price'] = kwargs['custom_price']

        kwargs.update(
            cls._calculate_money_fields(
                quantity=kwargs.get('quantity', 1.0),
                unit_price=kwargs.get('unit_price', 0.0),
                discount_percent=kwargs.get('discount_percent', 0.0),
                discount_amount=kwargs.get('discount_amount', 0.0),
                tax_rate=kwargs.get('tax_rate', 0.0),
                tax_included=kwargs.get('tax_included', False),
            )
        )

        deal_product = cls(**kwargs)
        db.add(deal_product)
        await db.commit()
        await db.refresh(deal_product)
        return await cls.get_by_id(db, deal_product.id)

    @classmethod
    async def update(cls, db, deal_product_id, **kwargs):
        from sqlalchemy import update, or_

        try:
            deal_product_uuid = deal_product_id if isinstance(deal_product_id, uuid.UUID) else uuid.UUID(str(deal_product_id))
        except (ValueError, TypeError):
            raise ValueError("deal_product_id must be a string or UUID")

        if 'custom_price' in kwargs and kwargs['custom_price'] is not None:
            kwargs['custom_price'] = cls._round_money(kwargs['custom_price'])
            kwargs['unit_price'] = kwargs['custom_price']

        if any(key in kwargs for key in ['quantity', 'unit_price', 'custom_price', 'discount_percent', 'discount_amount', 'tax_rate', 'tax_included']):
            current = await cls.get_by_id(db, deal_product_uuid)
            if current:
                resolved_unit_price = kwargs.get('unit_price')
                if resolved_unit_price is None:
                    resolved_unit_price = current.unit_price

                kwargs.update(
                    cls._calculate_money_fields(
                        quantity=kwargs.get('quantity', current.quantity),
                        unit_price=resolved_unit_price,
                        discount_percent=kwargs.get('discount_percent', current.discount_percent),
                        discount_amount=kwargs.get('discount_amount', current.discount_amount),
                        tax_rate=kwargs.get('tax_rate', current.tax_rate),
                        tax_included=kwargs.get('tax_included', current.tax_included),
                    )
                )

        deal_id_str = str(deal_product_uuid)
        deal_id_hex = deal_product_uuid.hex
        query = (
            update(cls)
            .where(or_(cls.id == deal_product_uuid, cls.id == deal_id_str, cls.id == deal_id_hex))
            .values(**kwargs)
            .execution_options(synchronize_session='fetch')
        )
        await db.execute(query)
        await db.commit()
        return await cls.get_by_id(db, deal_product_uuid)

    @classmethod
    async def delete(cls, db, deal_product_id: str) -> bool:
        from sqlalchemy import delete, or_
        try:
            deal_product_uuid = deal_product_id if isinstance(deal_product_id, uuid.UUID) else uuid.UUID(str(deal_product_id))
        except (ValueError, TypeError):
            return False
        deal_id_str = str(deal_product_uuid)
        deal_id_hex = deal_product_uuid.hex
        query = delete(cls).where(or_(cls.id == deal_product_uuid, cls.id == deal_id_str, cls.id == deal_id_hex))
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    def __repr__(self):
        return f"<DealProduct(deal={self.deal_id}, product={self.product_id}, quantity={self.quantity})>"
