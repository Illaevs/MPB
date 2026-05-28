from __future__ import annotations

import uuid
from datetime import date
from typing import Dict, List, Optional

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Deal,
    Stage,
    WipMonthly,
    InflationIndex,
    Overhead,
    OverheadAllocation,
    IncomeExpenseEntry,
    TreasuryAllocation,
    TreasuryTransaction,
    PricingModel,
    PricingQuote,
)


class EconomyService:
    @staticmethod
    def vat_rate_for_date(target_date: date) -> float:
        cutoff = date(2026, 1, 1)
        return 20.0 if target_date < cutoff else 22.0

    @staticmethod
    def period_key(target_date: date) -> str:
        return f"{target_date.year:04d}-{target_date.month:02d}"

    @staticmethod
    def iter_months(start: date, end: date) -> List[date]:
        months: List[date] = []
        current = date(start.year, start.month, 1)
        last = date(end.year, end.month, 1)
        while current <= last:
            months.append(current)
            if current.month == 12:
                current = date(current.year + 1, 1, 1)
            else:
                current = date(current.year, current.month + 1, 1)
        return months

    @classmethod
    async def rebuild_wip_for_deal(cls, deal_id: uuid.UUID, db: AsyncSession) -> List[WipMonthly]:
        deal = await Deal.get_by_id(db, str(deal_id))
        if not deal:
            return []

        stages = await Stage.get_by_deal_id(db, str(deal_id))

        current_period = cls.period_key(date.today())
        await db.execute(
            delete(WipMonthly).where(
                WipMonthly.deal_id == deal_id,
                WipMonthly.period >= current_period,
            )
        )

        entries: List[WipMonthly] = []
        for stage in stages:
            if not stage.date_start:
                continue
            end_date = stage.date_end or stage.date_start
            months = cls.iter_months(stage.date_start, end_date)
            if not months:
                continue
            planned_cost = stage.planned_cost or 0.0
            base_amount = planned_cost / len(months) if planned_cost else 0.0
            for month_start in months:
                period = cls.period_key(month_start)
                vat_rate = cls.vat_rate_for_date(month_start)
                vat_amount = base_amount * vat_rate / 100.0
                total_amount = base_amount + vat_amount
                entry = WipMonthly(
                    deal_id=deal_id,
                    stage_id=stage.id,
                    period=period,
                    base_amount=base_amount,
                    vat_rate=vat_rate,
                    vat_amount=vat_amount,
                    total_amount=total_amount,
                    is_forecast=period >= current_period,
                    calc_version=1,
                )
                db.add(entry)
                entries.append(entry)

        await db.commit()
        return entries

    @classmethod
    async def get_wip_by_deal(cls, deal_id: uuid.UUID, db: AsyncSession) -> List[WipMonthly]:
        result = await db.execute(
            select(WipMonthly).where(WipMonthly.deal_id == deal_id).order_by(WipMonthly.period)
        )
        return result.scalars().all()

    @classmethod
    async def get_inflation_map(cls, db: AsyncSession) -> Dict[str, float]:
        result = await db.execute(select(InflationIndex))
        return {row.period: row.value for row in result.scalars().all()}

    @classmethod
    async def allocate_overheads(cls, period: str, db: AsyncSession) -> List[OverheadAllocation]:
        overheads_result = await db.execute(select(Overhead).where(Overhead.period == period))
        overheads = overheads_result.scalars().all()
        overhead_total = sum(o.amount for o in overheads)

        wip_result = await db.execute(select(WipMonthly).where(WipMonthly.period == period))
        wip_rows = wip_result.scalars().all()
        wip_by_deal: Dict[uuid.UUID, float] = {}
        for row in wip_rows:
            wip_by_deal[row.deal_id] = wip_by_deal.get(row.deal_id, 0.0) + (row.base_amount or 0.0)

        total_wip = sum(wip_by_deal.values())
        await db.execute(delete(OverheadAllocation).where(OverheadAllocation.period == period))

        allocations: List[OverheadAllocation] = []
        if total_wip > 0 and overhead_total != 0:
            for deal_id, deal_wip in wip_by_deal.items():
                amount = overhead_total * (deal_wip / total_wip)
                allocation = OverheadAllocation(
                    deal_id=deal_id,
                    period=period,
                    amount=amount,
                    calc_version=1,
                )
                db.add(allocation)
                allocations.append(allocation)

        await db.commit()
        return allocations

    @classmethod
    async def import_overheads_from_dds(
        cls,
        db: AsyncSession,
        excluded_prefixes: Optional[List[str]] = None,
    ) -> List[Overhead]:
        excluded_prefixes = excluded_prefixes or []

        def is_excluded(category_code: Optional[str]) -> bool:
            if not category_code:
                return True
            stripped = category_code.strip()
            return any(stripped.startswith(prefix) for prefix in excluded_prefixes)

        entry_result = await db.execute(
            select(IncomeExpenseEntry).where(IncomeExpenseEntry.direction == "expense")
        )
        entries = entry_result.scalars().all()

        totals: Dict[str, Dict[str, float]] = {}
        paid_map: Dict[str, float] = {}

        entry_ids = [e.id for e in entries]
        if entry_ids:
            entry_map = {entry.id: entry for entry in entries}
            alloc_result = await db.execute(
                select(TreasuryAllocation, TreasuryTransaction)
                .join(TreasuryTransaction, TreasuryAllocation.transaction_id == TreasuryTransaction.id)
                .where(TreasuryAllocation.income_expense_id.in_(entry_ids))
            )
            for allocation, tx in alloc_result.all():
                if not tx.transaction_date:
                    continue
                entry = entry_map.get(allocation.income_expense_id)
                if not entry or entry.direction != "expense":
                    continue
                if is_excluded(entry.category_code):
                    continue
                period = cls.period_key(tx.transaction_date)
                totals.setdefault(period, {})
                category = entry.category_code
                totals[period][category] = totals[period].get(category, 0.0) + allocation.amount
                paid_map[allocation.income_expense_id] = (
                    paid_map.get(allocation.income_expense_id, 0.0) + allocation.amount
                )

        for entry in entries:
            if is_excluded(entry.category_code):
                continue
            category = entry.category_code
            paid = paid_map.get(entry.id, 0.0)
            remaining = max(entry.amount - paid, 0.0)
            if remaining <= 0:
                continue
            period = cls.period_key(entry.plan_date)
            totals.setdefault(period, {})
            totals[period][category] = totals[period].get(category, 0.0) + remaining

        await db.execute(delete(Overhead).where(Overhead.source == "dds"))

        created: List[Overhead] = []
        for period, categories in totals.items():
            for category, amount in categories.items():
                item = Overhead(
                    period=period,
                    amount=amount,
                    category=category,
                    source="dds",
                )
                db.add(item)
                created.append(item)

        await db.commit()
        return created

    @classmethod
    async def calculate_pricing_quote(
        cls,
        deal_id: uuid.UUID,
        model_id: Optional[uuid.UUID],
        db: AsyncSession,
        margin: Optional[float] = None,
        risk: Optional[float] = None,
        calc_date: Optional[date] = None,
    ) -> PricingQuote:
        wip_rows = await cls.get_wip_by_deal(deal_id, db)
        base_cost = sum(row.base_amount for row in wip_rows)

        inflation_map = await cls.get_inflation_map(db)
        current_period = cls.period_key(date.today())

        indexed_cost = 0.0
        for row in wip_rows:
            index = inflation_map.get(row.period, 1.0)
            if row.period >= current_period:
                indexed_cost += row.base_amount * index
            else:
                indexed_cost += row.base_amount

        overheads_result = await db.execute(
            select(OverheadAllocation).where(OverheadAllocation.deal_id == deal_id)
        )
        overheads = sum(row.amount for row in overheads_result.scalars().all())

        model = None
        if model_id:
            model_result = await db.execute(select(PricingModel).where(PricingModel.id == model_id))
            model = model_result.scalar_one_or_none()

        final_margin = margin if margin is not None else (model.base_margin if model else 0.0)
        final_risk = risk if risk is not None else (model.risk_reserve if model else 0.0)
        calc_date = calc_date or date.today()

        final_price = (indexed_cost + overheads + final_risk) * (1 + final_margin)

        quote = PricingQuote(
            deal_id=deal_id,
            model_id=model_id,
            calc_date=calc_date,
            base_cost=base_cost,
            overheads=overheads,
            indexed_cost=indexed_cost,
            risk=final_risk,
            margin=final_margin,
            final_price=final_price,
        )
        db.add(quote)
        await db.commit()
        await db.refresh(quote)
        return quote
