"""
Contract model - registry of contracts
"""
import uuid
from datetime import datetime, date
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Column, String, Date, Float, ForeignKey, DateTime, Enum as SqlEnum, or_, cast, and_
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, aliased
from sqlalchemy.sql import func

from app.database.base import Base


class ContractStatus(str, PyEnum):
    APPROVAL = "approval"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ContractType(str, PyEnum):
    EXPENSES = "expenses"
    SERVICES = "services"
    LABOR = "labor"
    GENERAL_CONTRACTOR = "general_contractor"
    PARTIAL_CONTRACTOR = "partial_contractor"
    SUBCONTRACTOR = "subcontractor"
    SUPPLY_OUT = "supply_out"
    SUPPLY_IN = "supply_in"


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    contract_number = Column(String(100), nullable=False)
    contract_date = Column(Date, nullable=False)
    status = Column(SqlEnum("approval", "in_progress", "completed"), default="approval")
    amount = Column(Float, default=0.0)
    contract_type = Column(
        SqlEnum(
            "expenses",
            "services",
            "labor",
            "general_contractor",
            "partial_contractor",
            "subcontractor",
            "supply_out",
            "supply_in",
        ),
        nullable=False,
    )

    customer_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    executor_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id"), nullable=True)
    subcontractor_card_id = Column(UUID(as_uuid=True), ForeignKey("subcontractor_cards.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    customer = relationship("Company", foreign_keys=[customer_id])
    executor = relationship("Company", foreign_keys=[executor_id])
    deal = relationship("Deal", backref="contracts")
    subcontractor_card = relationship("SubcontractorCard", backref="contracts")

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
    async def search_all(cls, db, *, skip: int = 0, limit: int = 25,
                         search: str = None, contract_type: str = None,
                         status: str = None, customer_id: str = None,
                         executor_id: str = None, deal_id: str = None,
                         sort_by: str = "contract_date", sort_dir: str = "desc",
                         allowed_deal_ids=None):
        """Search contracts with filters and correlated subqueries for search.
        Returns (items, total_count).

        Uses EXISTS subqueries instead of JOINs to avoid UUID/String type
        mismatch issues between Contract FK (UUID) and Company/Deal PK (String).
        """
        from sqlalchemy import select, exists
        from sqlalchemy import func
        from app.models.company import Company
        from app.models.deal import Deal

        customer_id_text = cast(cls.customer_id, String)
        executor_id_text = cast(cls.executor_id, String)
        deal_id_text = cast(cls.deal_id, String)
        customer_id_norm = func.replace(customer_id_text, "-", "")
        executor_id_norm = func.replace(executor_id_text, "-", "")
        deal_id_norm = func.replace(deal_id_text, "-", "")

        conditions = []

        # permission filter
        if allowed_deal_ids is not None:
            allowed_strs = [str(did).replace("-", "") for did in allowed_deal_ids]
            if allowed_strs:
                conditions.append(and_(cls.deal_id.isnot(None), deal_id_norm.in_(allowed_strs)))
            else:
                return [], 0

        # individual filters (applied for both SQL and Python search)
        if contract_type:
            conditions.append(cls.contract_type == contract_type)
        if status:
            conditions.append(cls.status == status)
        if customer_id:
            conditions.append(customer_id_norm == str(customer_id).replace("-", ""))
        if executor_id:
            conditions.append(executor_id_norm == str(executor_id).replace("-", ""))
        if deal_id:
            conditions.append(deal_id_norm == str(deal_id).replace("-", ""))

        # SQLite does not handle Cyrillic case-insensitive search via lower/LIKE.
        # Fallback to Python casefold search when needed.
        dialect_name = ""
        try:
            dialect_name = db.get_bind().dialect.name
        except Exception:
            dialect_name = ""
        use_python_search = bool(
            search and search.strip() and dialect_name == "sqlite"
            and any(ord(ch) > 127 for ch in search)
        )

        if use_python_search:
            CustomerAlias = aliased(Company)
            ExecutorAlias = aliased(Company)
            DealAlias = aliased(Deal)

            query = (
                select(
                    cls,
                    CustomerAlias.name,
                    CustomerAlias.short_name,
                    ExecutorAlias.name,
                    ExecutorAlias.short_name,
                    DealAlias.title,
                    DealAlias.obj_name,
                    DealAlias.address,
                )
                .outerjoin(
                    CustomerAlias,
                    func.replace(CustomerAlias.id, "-", "") == customer_id_norm,
                )
                .outerjoin(
                    ExecutorAlias,
                    func.replace(ExecutorAlias.id, "-", "") == executor_id_norm,
                )
                .outerjoin(
                    DealAlias,
                    func.replace(DealAlias.id, "-", "") == deal_id_norm,
                )
            )
            if conditions:
                query = query.where(and_(*conditions))
            result = await db.execute(query)
            rows = result.all()

            search_cf = search.strip().casefold()
            matched = []
            for row in rows:
                contract = row[0]
                parts = [
                    contract.contract_number,
                    row[1],
                    row[2],
                    row[3],
                    row[4],
                    row[5],
                    row[6],
                ]
                haystack = " ".join([p for p in parts if p]).casefold()
                if search_cf in haystack:
                    matched.append(contract)

            total_count = len(matched)
            items = matched[skip: skip + limit]
            return items, total_count

        # search: use EXISTS subqueries for related tables
        if search and search.strip():
            pattern = f"%{search.strip()}%"

            # Subquery: customer name matches
            customer_match = exists(
                select(Company.id).where(
                    and_(
                        func.replace(Company.id, "-", "") == customer_id_norm,
                        or_(Company.name.ilike(pattern), Company.short_name.ilike(pattern))
                    )
                )
            )
            # Subquery: executor name matches
            executor_match = exists(
                select(Company.id).where(
                    and_(
                        func.replace(Company.id, "-", "") == executor_id_norm,
                        or_(Company.name.ilike(pattern), Company.short_name.ilike(pattern))
                    )
                )
            )
            # Subquery: deal title or object fields match
            deal_match = exists(
                select(Deal.id).where(
                    and_(
                        func.replace(Deal.id, "-", "") == deal_id_norm,
                        or_(
                            Deal.title.ilike(pattern),
                            Deal.obj_name.ilike(pattern),
                            Deal.address.ilike(pattern),
                        )
                    )
                )
            )

            conditions.append(or_(
                cls.contract_number.ilike(pattern),
                customer_match,
                executor_match,
                deal_match,
            ))

        base_q = select(cls)
        if conditions:
            base_q = base_q.where(and_(*conditions))

        # count
        count_q = select(func.count()).select_from(
            base_q.with_only_columns(cls.id).subquery()
        )
        total_result = await db.execute(count_q)
        total_count = total_result.scalar() or 0

        # items with sort
        sort_map = {
            "contract_date": cls.contract_date,
            "contract_number": cls.contract_number,
            "amount": cls.amount,
            "status": cls.status,
            "contract_type": cls.contract_type,
            "created_at": getattr(cls, "created_at", cls.contract_date),
        }
        sort_col = sort_map.get(sort_by or "contract_date", cls.contract_date)
        order_clause = sort_col.asc() if (sort_dir or "desc").lower() == "asc" else sort_col.desc()
        items_q = base_q.order_by(order_clause).offset(skip).limit(limit)
        result = await db.execute(items_q)
        items = result.scalars().all()

        return items, total_count

    @classmethod
    async def count_by_status(cls, db, *, allowed_deal_ids=None):
        """Count contracts grouped by status. Returns dict {status: count}."""
        from sqlalchemy import select
        conditions = []
        if allowed_deal_ids is not None:
            allowed_strs = [str(did) for did in allowed_deal_ids]
            if allowed_strs:
                deal_id_text = cast(cls.deal_id, String)
                conditions.append(and_(cls.deal_id.isnot(None), deal_id_text.in_(allowed_strs)))
            else:
                return {"approval": 0, "in_progress": 0, "completed": 0}
        query = select(cls.status, func.count(cls.id)).group_by(cls.status)
        if conditions:
            query = query.where(and_(*conditions))
        result = await db.execute(query)
        stats = {"approval": 0, "in_progress": 0, "completed": 0}
        for row in result.all():
            if row[0] in stats:
                stats[row[0]] = row[1]
        return stats

    @classmethod
    async def get_by_id(cls, db, contract_id: str):
        from sqlalchemy import select
        try:
            contract_uuid = contract_id if isinstance(contract_id, uuid.UUID) else uuid.UUID(str(contract_id))
            variants = [contract_uuid, str(contract_uuid), contract_uuid.hex]
        except (ValueError, TypeError):
            variants = [str(contract_id)]
        id_as_text = cast(cls.id, String)
        conditions = []
        for value in variants:
            if isinstance(value, uuid.UUID):
                conditions.append(cls.id == value)
                conditions.append(id_as_text == str(value))
            else:
                conditions.append(id_as_text == str(value))
        query = select(cls).where(or_(*conditions))
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_deal_id(cls, db, deal_id: str):
        from sqlalchemy import select
        try:
            deal_uuid = deal_id if isinstance(deal_id, uuid.UUID) else uuid.UUID(str(deal_id))
            variants = [deal_uuid, str(deal_uuid), deal_uuid.hex]
        except (ValueError, TypeError):
            variants = [str(deal_id)]
        deal_as_text = cast(cls.deal_id, String)
        conditions = []
        for value in variants:
            if isinstance(value, uuid.UUID):
                conditions.append(cls.deal_id == value)
                conditions.append(deal_as_text == str(value))
            else:
                conditions.append(deal_as_text == str(value))
        query = select(cls).where(or_(*conditions)).order_by(cls.contract_date.desc())
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def get_by_subcontractor_card_id(cls, db, card_id: str):
        from sqlalchemy import select
        try:
            card_uuid = card_id if isinstance(card_id, uuid.UUID) else uuid.UUID(str(card_id))
            variants = [card_uuid, str(card_uuid), card_uuid.hex]
        except (ValueError, TypeError):
            variants = [str(card_id)]
        card_as_text = cast(cls.subcontractor_card_id, String)
        conditions = []
        for value in variants:
            if isinstance(value, uuid.UUID):
                conditions.append(cls.subcontractor_card_id == value)
                conditions.append(card_as_text == str(value))
            else:
                conditions.append(card_as_text == str(value))
        query = select(cls).where(or_(*conditions)).order_by(cls.contract_date.desc())
        result = await db.execute(query)
        return result.scalars().all()

    @classmethod
    async def create(cls, db, **kwargs):
        now = datetime.now()
        kwargs["created_at"] = now
        kwargs["updated_at"] = now
        contract = cls(**kwargs)
        db.add(contract)
        await db.commit()
        await db.refresh(contract)
        return contract

    @classmethod
    async def update(cls, db, contract_id: str, **kwargs):
        from sqlalchemy import update
        try:
            contract_uuid = contract_id if isinstance(contract_id, uuid.UUID) else uuid.UUID(str(contract_id))
            variants = [contract_uuid, str(contract_uuid), contract_uuid.hex]
        except (ValueError, TypeError):
            variants = [str(contract_id)]
        id_as_text = cast(cls.id, String)
        conditions = []
        for value in variants:
            if isinstance(value, uuid.UUID):
                conditions.append(cls.id == value)
                conditions.append(id_as_text == str(value))
            else:
                conditions.append(id_as_text == str(value))
        query = (
            update(cls)
            .where(or_(*conditions))
            .values(**kwargs)
            .execution_options(synchronize_session="fetch")
        )
        await db.execute(query)
        await db.commit()
        return await cls.get_by_id(db, contract_id)

    @classmethod
    async def delete(cls, db, contract_id: str) -> bool:
        from sqlalchemy import delete
        try:
            contract_uuid = contract_id if isinstance(contract_id, uuid.UUID) else uuid.UUID(str(contract_id))
            variants = [contract_uuid, str(contract_uuid), contract_uuid.hex]
        except (ValueError, TypeError):
            variants = [str(contract_id)]
        id_as_text = cast(cls.id, String)
        conditions = []
        for value in variants:
            if isinstance(value, uuid.UUID):
                conditions.append(cls.id == value)
                conditions.append(id_as_text == str(value))
            else:
                conditions.append(id_as_text == str(value))
        query = delete(cls).where(or_(*conditions))
        result = await db.execute(query)
        await db.commit()
        return result.rowcount > 0

    def __repr__(self):
        return f"<Contract(id={self.id}, number='{self.contract_number}')>"
