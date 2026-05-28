"""
Finance Service - Сервис для финансовых расчетов
"""
import re
import uuid
from datetime import date, datetime
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models import (
    FinancialPlan, TreasuryTransaction, TransactionAllocation,
    CBRate, Deal, Stage, Company, TreasuryAutoRule, TreasuryAllocation, IncomeExpenseEntry
)


class FinanceService:
    """
    Сервис для финансовых расчетов: PV, NPV, неустойки
    """

    @staticmethod
    def round_decimal(value: float, places: int = 2) -> Decimal:
        """Округляет значение до указанного количества знаков после запятой"""
        return Decimal(str(value)).quantize(Decimal(f"1.{'0' * places}"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _normalize_uuid(value: Any) -> uuid.UUID:
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))

    @classmethod
    async def get_cb_rate_for_date(cls, target_date: date, db: AsyncSession) -> Optional[float]:
        """
        Получить ставку ЦБ для указанной даты
        Используется ближайшая предыдущая дата ставки
        """
        query = select(CBRate).where(
            CBRate.rate_date <= target_date
        ).order_by(CBRate.rate_date.desc()).limit(1)

        result = await db.execute(query)
        cb_rate = result.scalar_one_or_none()

        return cb_rate.rate_value / 100 if cb_rate else 0.0  # Преобразуем проценты в доли

    @classmethod
    async def calculate_pv(cls, deal_id: uuid.UUID, db: AsyncSession) -> Dict[str, Any]:
        """
        Расчет Present Value для проекта

        PV = Amount / (1 + Rate/365)^DaysDelay

        Args:
            deal_id: ID проекта
            db: Сессия БД

        Returns:
            Словарь с результатами расчета
        """
        # Получаем плановые операции
        deal_uuid = cls._normalize_uuid(deal_id)
        plans_query = select(FinancialPlan).where(
            FinancialPlan.deal_id == deal_uuid
        ).options(selectinload(FinancialPlan.allocations))

        plans_result = await db.execute(plans_query)
        plans = plans_result.scalars().all()

        total_plan_income = 0.0
        total_plan_expense = 0.0
        total_fact_income = 0.0
        total_fact_expense = 0.0
        total_pv_income = 0.0
        total_pv_expense = 0.0

        for plan in plans:
            plan_amount = plan.amount_plan

            if plan.direction == "income":
                total_plan_income += plan_amount
            else:  # expense
                total_plan_expense += plan_amount

            # Получаем распределенные транзакции для этого плана
            allocated_amount = 0.0
            pv_amount = 0.0

            for allocation in plan.allocations:
                transaction = allocation.transaction
                allocated_amount += allocation.amount

                # Расчет PV для транзакции
                if plan.date_plan_end and transaction.transaction_date > plan.date_plan_end:
                    # Просрочка в днях
                    days_delay = (transaction.transaction_date - plan.date_plan_end).days

                    # Получаем ставку ЦБ
                    cb_rate = await cls.get_cb_rate_for_date(plan.date_plan_end, db)

                    # Расчет PV: PV = Amount / (1 + Rate/365)^DaysDelay
                    discount_factor = (1 + cb_rate / 365) ** days_delay
                    pv = allocation.amount / discount_factor if discount_factor != 0 else allocation.amount
                else:
                    pv = allocation.amount

                pv_amount += pv

            # Суммируем фактические и PV значения
            if plan.direction == "income":
                total_fact_income += allocated_amount
                total_pv_income += pv_amount
            else:  # expense
                total_fact_expense += allocated_amount
                total_pv_expense += pv_amount

        # Расчет потерь/выигрыша
        inflation_loss_income = total_plan_income - total_pv_income
        inflation_loss_expense = total_pv_expense - total_plan_expense  # Для расходов наоборот

        return {
            "deal_id": str(deal_uuid),
            "summary": {
                "total_plan_income": cls.round_decimal(total_plan_income),
                "total_plan_expense": cls.round_decimal(total_plan_expense),
                "total_fact_income": cls.round_decimal(total_fact_income),
                "total_fact_expense": cls.round_decimal(total_fact_expense),
                "total_pv_income": cls.round_decimal(total_pv_income),
                "total_pv_expense": cls.round_decimal(total_pv_expense),
                "inflation_loss_income": cls.round_decimal(inflation_loss_income),
                "inflation_loss_expense": cls.round_decimal(inflation_loss_expense),
                "net_inflation_loss": cls.round_decimal(inflation_loss_income - inflation_loss_expense)
            },
            "details": [
                {
                    "plan_id": str(plan.id),
                    "direction": plan.direction,
                    "description": plan.description,
                    "plan_amount": cls.round_decimal(plan.amount_plan),
                    "fact_amount": cls.round_decimal(sum(a.amount for a in plan.allocations)),
                    "pv_amount": cls.round_decimal(
                        sum(
                            allocation.amount / ((1 + await cls.get_cb_rate_for_date(plan.date_plan_end, db) / 365) **
                                               max(0, (allocation.transaction.transaction_date - plan.date_plan_end).days))
                            if plan.date_plan_end and allocation.transaction.transaction_date > plan.date_plan_end
                            else allocation.amount
                            for allocation in plan.allocations
                        )
                    )
                } for plan in plans
            ]
        }

    @classmethod
    async def calculate_penalties(
        cls,
        deal_id: uuid.UUID,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Расчет неустоек по проекту

        Args:
            deal_id: ID проекта
            db: Сессия БД

        Returns:
            Словарь с рассчитанными неустойками
        """
        # Получаем проект с конфигурацией неустоек
        deal_uuid = cls._normalize_uuid(deal_id)
        deal_query = select(Deal).where(Deal.id == deal_uuid)
        deal_result = await db.execute(deal_query)
        deal = deal_result.scalar_one_or_none()

        if not deal or not deal.penalty_config:
            return {"error": "Penalty configuration not found"}

        penalty_config = deal.penalty_config

        # Получаем просроченные этапы
        stages_query = select(Stage).where(
            and_(
                Stage.deal_id == deal_uuid,
                Stage.date_end.isnot(None),
                Stage.status.in_(["delayed", "completed"])  # Только завершенные или просроченные
            )
        )

        stages_result = await db.execute(stages_query)
        stages = stages_result.scalars().all()

        risk_penalties = []
        profit_penalties = []

        for stage in stages:
            if not stage.date_end:
                continue

            # Определяем тип просрочки (риск или прибыль)
            # Для упрощения считаем все просрочки как риски (штрафы заказчику)
            # В реальной системе нужно анализировать связи с платежами

            penalty_base = stage.planned_cost or stage.actual_cost or 0

            if penalty_config.get("risk", {}).get("type") == "fixed":
                # Фиксированная ставка
                rate = penalty_config["risk"].get("value", 0)
                penalty = penalty_base * rate

            elif penalty_config.get("risk", {}).get("type") == "rate_cb":
                # Ставка ЦБ
                grace_period = penalty_config["risk"].get("grace_period", 0)

                # Имитация просрочки (в реальной системе нужно рассчитывать по факту)
                delay_days = 10  # Для демонстрации

                if delay_days > grace_period:
                    effective_delay = delay_days - grace_period

                    # Получаем ставку ЦБ для даты окончания этапа
                    cb_rate = await cls.get_cb_rate_for_date(stage.date_end, db)
                    factor = penalty_config["risk"].get("factor", 1.0)

                    # Расчет по дням просрочки
                    daily_penalty = penalty_base * cb_rate * factor / 365
                    penalty = daily_penalty * effective_delay
                else:
                    penalty = 0
            else:
                penalty = 0

            risk_penalties.append({
                "stage_id": str(stage.id),
                "stage_name": stage.name,
                "delay_days": 10,  # Для демонстрации
                "penalty_amount": cls.round_decimal(penalty),
                "calculation_type": penalty_config.get("risk", {}).get("type", "fixed")
            })

        return {
            "deal_id": str(deal_uuid),
            "risk_penalties": risk_penalties,
            "profit_penalties": profit_penalties,  # Пока пустой
            "total_risk_penalty": cls.round_decimal(sum(p["penalty_amount"] for p in risk_penalties)),
            "total_profit_penalty": cls.round_decimal(0),  # Пока 0
            "net_penalty": cls.round_decimal(sum(p["penalty_amount"] for p in risk_penalties))
        }

    @classmethod
    def _rule_matches(cls, rule: TreasuryAutoRule, tx: TreasuryTransaction) -> bool:
        purpose = (tx.purpose or "").lower()
        match_text = (rule.match_text or "").lower()

        if rule.match_type == "contains":
            return match_text in purpose
        if rule.match_type == "starts_with":
            return purpose.startswith(match_text)
        if rule.match_type == "ends_with":
            return purpose.endswith(match_text)
        if rule.match_type == "regex":
            try:
                return bool(re.search(rule.match_text, tx.purpose or "", re.IGNORECASE))
            except re.error:
                return False
        return False

    @classmethod
    async def _link_companies_to_entry(
        cls,
        entry: IncomeExpenseEntry,
        tx: TreasuryTransaction,
        db: AsyncSession,
    ) -> None:
        # Do not block rule application if INN lookup fails.
        try:
            if tx.payer_inn:
                payer_company = await Company.get_by_inn(db, tx.payer_inn)
                if payer_company:
                    entry.payer_id = str(payer_company.id)
            if tx.payee_inn:
                payee_company = await Company.get_by_inn(db, tx.payee_inn)
                if payee_company:
                    entry.payee_id = str(payee_company.id)
        except Exception:
            pass

    @classmethod
    async def apply_rule_to_transaction(
        cls,
        rule: TreasuryAutoRule,
        tx: TreasuryTransaction,
        db: AsyncSession,
    ) -> bool:
        """Apply a specific auto-rule to a transaction."""
        if not cls._rule_matches(rule, tx):
            return False

        if rule.action_type == "ignore":
            tx.ignore_flag = "Да"
            tx.auto_rule_id = str(rule.id)
            return True

        if rule.action_type == "category":
            if rule.category_code:
                tx.category_code = rule.category_code
            tx.auto_rule_id = str(rule.id)
            return True

        if rule.action_type == "create_dds":
            direction = "expense" if tx.amount < 0 else "income"
            entry = IncomeExpenseEntry(
                id=str(uuid.uuid4()),
                direction=direction,
                amount=abs(tx.amount),
                plan_date=tx.transaction_date or date.today(),
                actual_date=tx.transaction_date,
                payer_id=None,
                payee_id=None,
                category_code=rule.category_code or tx.category_code,
            )
            await cls._link_companies_to_entry(entry, tx, db)
            db.add(entry)
            await db.flush()

            allocation = TreasuryAllocation(
                transaction_id=tx.id,
                income_expense_id=entry.id,
                amount=abs(tx.amount),
                category_code=rule.category_code or tx.category_code,
            )
            db.add(allocation)

            if rule.category_code:
                tx.category_code = rule.category_code
            tx.income_expense_id = entry.id
            tx.auto_rule_id = str(rule.id)
            return True

        return False

    @classmethod
    async def apply_auto_rules(cls, tx: TreasuryTransaction, db: AsyncSession) -> Optional[str]:
        """Apply the first matching auto-rule to a transaction. Returns rule_id if applied."""
        rules_result = await db.execute(
            select(TreasuryAutoRule)
            .where(TreasuryAutoRule.is_active == True)
            .order_by(TreasuryAutoRule.priority)
        )
        rules = rules_result.scalars().all()

        for rule in rules:
            if await cls.apply_rule_to_transaction(rule, tx, db):
                return str(rule.id)

        return None

    @classmethod
    async def import_bank_statement(
        cls,
        transactions_data: List[Dict[str, Any]],
        db: AsyncSession,
        create_missing_companies: bool = False,
        default_calc_type: str = "vtb"
    ) -> Dict[str, Any]:
        """
        Импорт выписки банка (CSV/XML)

        Args:
            transactions_data: Список транзакций из файла
            db: Сессия БД

        Returns:
            Результат импорта
        """
        imported_count = 0
        skipped_count = 0
        rules_applied_count = 0
        errors = []
        # Список импортированных транзакций для batch-эмиссии в Event Bus.
        # Заполняется в success-ветке; используется после commit.
        imported_items: list = []

        for tx_data in transactions_data:
            try:
                # Проверяем, существует ли уже такая транзакция
                existing_query = select(TreasuryTransaction).where(
                    and_(
                        TreasuryTransaction.doc_num == tx_data["doc_num"],
                        TreasuryTransaction.transaction_date == tx_data["transaction_date"],
                        TreasuryTransaction.amount == tx_data["amount"]
                    )
                )
                existing_result = await db.execute(existing_query)
                existing_tx = existing_result.scalar_one_or_none()

                if existing_tx:
                    skipped_count += 1
                    continue

                if create_missing_companies:
                    payer_inn = tx_data.get("payer_inn")
                    payer_name = tx_data.get("payer_name") or "No Name"
                    if payer_inn:
                        existing_payer = await Company.get_by_inn(db, payer_inn)
                        if not existing_payer:
                            await Company.create(
                                db,
                                inn=payer_inn,
                                name=payer_name,
                                type="customer"
                            )

                    payee_inn = tx_data.get("payee_inn")
                    payee_name = tx_data.get("payee_name") or "No Name"
                    if payee_inn:
                        existing_payee = await Company.get_by_inn(db, payee_inn)
                        if not existing_payee:
                            await Company.create(
                                db,
                                inn=payee_inn,
                                name=payee_name,
                                type="customer"
                            )

                async with db.begin_nested():
                    transaction = TreasuryTransaction(
                        doc_num=tx_data["doc_num"],
                        transaction_date=tx_data["transaction_date"],
                        amount=tx_data["amount"],
                        calc_type=tx_data.get("calc_type") or default_calc_type,
                        payer_inn=tx_data.get("payer_inn"),
                        payee_inn=tx_data.get("payee_inn"),
                        payer_name=tx_data.get("payer_name"),
                        payee_name=tx_data.get("payee_name"),
                        purpose=tx_data.get("purpose", ""),
                        ignore_flag="Нет",
                        remainder=abs(tx_data["amount"])
                    )

                    db.add(transaction)
                    await db.flush()

                    rule_applied = await cls.apply_auto_rules(transaction, db)
                    if rule_applied:
                        rules_applied_count += 1

                    imported_count += 1
                    imported_items.append({
                        "id": str(transaction.id),
                        "doc_num": transaction.doc_num,
                        "amount": float(transaction.amount or 0),
                        "transaction_date": transaction.transaction_date.isoformat() if transaction.transaction_date else None,
                        "category_code": transaction.category_code,
                    })

            except Exception as e:
                errors.append(f"Error importing transaction {tx_data.get('doc_num', 'unknown')}: {str(e)}")

        await db.commit()

        # Event Bus v2: ОДНО batch-событие на всю пачку — внешний
        # consumer (BI, 1С) получит её атомарно, а не N webhook'ов.
        # Считаем total_amount по импортированным (skipped не входят).
        if imported_items:
            from app.services.event_outbox import emit_batch_event_safe
            await emit_batch_event_safe(
                db,
                event_type="treasury_transaction.batch_imported",
                entity_type="treasury_transaction",
                items=imported_items,
                summary={
                    "imported_count": imported_count,
                    "skipped_count": skipped_count,
                    "rules_applied_count": rules_applied_count,
                    "total_amount": sum(i["amount"] for i in imported_items),
                    "errors_count": len(errors),
                },
            )

        return {
            "imported_count": imported_count,
            "skipped_count": skipped_count,
            "rules_applied_count": rules_applied_count,
            "errors": errors,
            "total_processed": len(transactions_data)
        }

