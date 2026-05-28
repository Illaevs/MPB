"""
Finance API Router - Financial Analysis and Planning
"""
import uuid
import re
import csv
import io
from datetime import date, datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, delete

from app.database.session import get_db
from app.models import FinancialPlan, Deal, Company, TreasuryTransaction, IncomeExpenseEntry, TreasuryAllocation, TreasuryAutoRule
from app.schemas.treasury_transaction import TreasuryTransactionResponse, TreasuryTransactionUpdate, TreasuryTransactionCreate, LinkedPaymentInfo
from app.schemas.treasury_allocation import (
    TreasuryAllocationCreate,
    TreasuryAllocationUpdate,
    TreasuryAllocationResponse,
)
from app.schemas.financial_plan import FinancialPlanCreate, FinancialPlanUpdate, FinancialPlanResponse
from app.schemas.treasury_auto_rule import TreasuryAutoRuleCreate, TreasuryAutoRuleUpdate, TreasuryAutoRuleResponse
from app.services.finance_service import FinanceService

router = APIRouter()

def _parse_uuid(value: str, field_name: str) -> uuid.UUID:
    try:
        raw = str(value)
        if re.fullmatch(r"[0-9a-fA-F]{32}", raw):
            raw = f"{raw[0:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}"
        return value if isinstance(value, uuid.UUID) else uuid.UUID(raw)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}")

def _parse_date(value: str) -> date:
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unsupported date format: {value}")

def _parse_amount(value: str) -> float:
    raw = value.strip().replace(" ", "").replace("\u00a0", "")
    raw = raw.replace(",", ".")
    return float(raw) if raw else 0.0

def _normalize_inn(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    return digits or None

def _month_start(value: date) -> date:
    return date(value.year, value.month, 1)

def _month_end(value: date) -> date:
    next_month = value.month + 1
    year = value.year
    if next_month > 12:
        next_month = 1
        year += 1
    return date(year, next_month, 1) - timedelta(days=1)

def _quarter_start(value: date) -> date:
    quarter = (value.month - 1) // 3
    month = quarter * 3 + 1
    return date(value.year, month, 1)

def _quarter_end(value: date) -> date:
    start = _quarter_start(value)
    end_month = start.month + 2
    return _month_end(date(start.year, end_month, 1))

def _iter_months(start: date, end: date) -> List[date]:
    months = []
    cursor = date(start.year, start.month, 1)
    end_cursor = date(end.year, end.month, 1)
    while cursor <= end_cursor:
        months.append(cursor)
        year = cursor.year + (1 if cursor.month == 12 else 0)
        month = 1 if cursor.month == 12 else cursor.month + 1
        cursor = date(year, month, 1)
    return months


def _is_ignore_flag(value: Optional[str]) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    raw = str(value).strip()
    if not raw:
        return False

    candidates = [raw]
    # Try to fix common mojibake (UTF-8 decoded as cp1251/latin1)
    for enc in ("latin1", "cp1251"):
        try:
            fixed = raw.encode(enc).decode("utf-8")
            if fixed and fixed not in candidates:
                candidates.append(fixed)
        except Exception:
            continue

    true_set = {"да", "yes", "true", "1", "y", "on", "истина", "??"}
    false_set = {"нет", "no", "false", "0", "n", "off", "???"}

    for cand in candidates:
        lowered = cand.strip().lower()
        if lowered in true_set:
            return True
        if lowered in false_set:
            return False
    return False

def _normalize_calc_type(value: str, default_calc_type: str) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return default_calc_type
    if raw in {"vtb", "втб", "втб банк"}:
        return "vtb"
    if "матер" in raw or raw == "material":
        return "material"
    if "иной" in raw or raw == "other":
        return "other"
    return default_calc_type

def _detect_delimiter(sample: str) -> str:
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,|\t,")
        return dialect.delimiter
    except csv.Error:
        return ";"

def _decode_file(content: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1251"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("utf-8", errors="replace")


def _build_tx_response(
    tx: TreasuryTransaction,
    allocations: List[TreasuryAllocation],
    linked_payments: Optional[List[TreasuryTransaction]] = None,
) -> TreasuryTransactionResponse:
    allocated_amount = sum(a.amount for a in allocations)
    linked_list = linked_payments or []
    linked_sum = sum(abs(lp.amount) for lp in linked_list)
    total_allocated = allocated_amount + linked_sum
    total_amount = abs(tx.amount)
    remainder = max(total_amount - total_allocated, 0.0)
    auto_rule_id = getattr(tx, 'auto_rule_id', None)
    linked_tx_id = getattr(tx, 'linked_transaction_id', None)
    return TreasuryTransactionResponse.model_validate(tx).model_copy(
        update={
            "allocations": [TreasuryAllocationResponse.model_validate(a) for a in allocations],
            "allocated_amount": total_allocated,
            "remainder": remainder,
            "auto_rule_id": auto_rule_id,
            "auto_filled": bool(auto_rule_id),
            "linked_transaction_id": str(linked_tx_id) if linked_tx_id else None,
            "linked_payments": [
                LinkedPaymentInfo(
                    id=lp.id,
                    doc_num=lp.doc_num,
                    transaction_date=lp.transaction_date,
                    amount=lp.amount,
                )
                for lp in linked_list
            ],
        }
    )


@router.get("/cashflow")
async def get_cashflow(
    deal_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(IncomeExpenseEntry)
    if deal_id:
        query = query.where(IncomeExpenseEntry.deal_id == deal_id)
    result = await db.execute(query)
    entries = result.scalars().all()

    entry_ids = [e.id for e in entries]
    tx_map: Dict[str, List[Tuple[TreasuryAllocation, TreasuryTransaction]]] = {}
    if entry_ids:
        alloc_result = await db.execute(
            select(TreasuryAllocation, TreasuryTransaction)
            .join(TreasuryTransaction, TreasuryAllocation.transaction_id == TreasuryTransaction.id)
            .where(TreasuryAllocation.income_expense_id.in_(entry_ids))
        )
        for allocation, tx in alloc_result.all():
            tx_map.setdefault(allocation.income_expense_id, []).append((allocation, tx))

    def add_amount(bucket: Dict[date, Dict[str, float]], key_date: date, direction: str, amount: float):
        if key_date not in bucket:
            bucket[key_date] = {"income": 0.0, "expense": 0.0}
        bucket[key_date][direction] += amount

    plan_bucket: Dict[date, Dict[str, float]] = {}
    actual_bucket: Dict[date, Dict[str, float]] = {}
    forecast_bucket: Dict[date, Dict[str, float]] = {}

    for entry in entries:
        direction = entry.direction
        plan_date = entry.plan_date
        add_amount(plan_bucket, plan_date, direction, entry.amount)

        paid = 0.0
        for allocation, tx in tx_map.get(entry.id, []):
            amt = allocation.amount
            paid += amt
            if tx.transaction_date:
                add_amount(actual_bucket, tx.transaction_date, direction, amt)

        remaining = entry.amount - paid
        if remaining > 0:
            add_amount(forecast_bucket, plan_date, direction, remaining)

    all_dates = sorted(set(plan_bucket.keys()) | set(actual_bucket.keys()) | set(forecast_bucket.keys()))

    cumulative_plan = 0.0
    cumulative_actual = 0.0
    cumulative_forecast = 0.0
    rows = []
    totals = {
        "plan_income": 0.0,
        "plan_expense": 0.0,
        "actual_income": 0.0,
        "actual_expense": 0.0,
        "forecast_income": 0.0,
        "forecast_expense": 0.0
    }

    for day in all_dates:
        plan_income = plan_bucket.get(day, {}).get("income", 0.0)
        plan_expense = plan_bucket.get(day, {}).get("expense", 0.0)
        actual_income = actual_bucket.get(day, {}).get("income", 0.0)
        actual_expense = actual_bucket.get(day, {}).get("expense", 0.0)
        forecast_income = forecast_bucket.get(day, {}).get("income", 0.0)
        forecast_expense = forecast_bucket.get(day, {}).get("expense", 0.0)

        totals["plan_income"] += plan_income
        totals["plan_expense"] += plan_expense
        totals["actual_income"] += actual_income
        totals["actual_expense"] += actual_expense
        totals["forecast_income"] += forecast_income
        totals["forecast_expense"] += forecast_expense

        net_plan = plan_income - plan_expense
        net_actual = actual_income - actual_expense
        net_forecast = forecast_income - forecast_expense

        cumulative_plan += net_plan
        cumulative_actual += net_actual
        cumulative_forecast += net_forecast

        rows.append({
            "date": day,
            "plan_income": plan_income,
            "plan_expense": plan_expense,
            "actual_income": actual_income,
            "actual_expense": actual_expense,
            "forecast_income": forecast_income,
            "forecast_expense": forecast_expense,
            "net_plan": net_plan,
            "net_actual": net_actual,
            "net_forecast": net_forecast,
            "cumulative_plan": cumulative_plan,
            "cumulative_actual": cumulative_actual,
            "cumulative_forecast": cumulative_forecast
        })

    return {
        "deal_id": deal_id,
        "rows": rows,
        "totals": totals
    }


@router.get("/overview")
async def get_finance_overview(
    period: str = "year",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    today = date.today()
    start: Optional[date] = None
    end: Optional[date] = None
    if start_date:
        start = _parse_date(start_date)
    if end_date:
        end = _parse_date(end_date)

    if not start or not end:
        if period == "month":
            start = date(today.year, today.month, 1)
            end = _month_end(today)
        elif period == "quarter":
            start = _quarter_start(today)
            end = _quarter_end(today)
        elif period == "year":
            start = date(today.year, 1, 1)
            end = date(today.year, 12, 31)
        elif period == "all":
            start = None
            end = None
        else:
            start = date(today.year, 1, 1)
            end = date(today.year, 12, 31)

    entries_query = select(IncomeExpenseEntry)
    if start and end:
        entries_query = entries_query.where(
            and_(IncomeExpenseEntry.plan_date >= start, IncomeExpenseEntry.plan_date <= end)
        )
    entry_result = await db.execute(entries_query)
    entries = entry_result.scalars().all()

    entry_ids = [e.id for e in entries]
    allocations_all: List[TreasuryAllocation] = []
    allocations_in_period: List[Tuple[TreasuryAllocation, TreasuryTransaction]] = []
    if entry_ids:
        alloc_all_result = await db.execute(
            select(TreasuryAllocation).where(TreasuryAllocation.income_expense_id.in_(entry_ids))
        )
        allocations_all = alloc_all_result.scalars().all()

        alloc_period_query = (
            select(TreasuryAllocation, TreasuryTransaction)
            .join(TreasuryTransaction, TreasuryAllocation.transaction_id == TreasuryTransaction.id)
            .where(TreasuryAllocation.income_expense_id.in_(entry_ids))
        )
        if start and end:
            alloc_period_query = alloc_period_query.where(
                and_(TreasuryTransaction.transaction_date >= start, TreasuryTransaction.transaction_date <= end)
            )
        alloc_period_result = await db.execute(alloc_period_query)
        allocations_in_period = alloc_period_result.all()

    paid_total_by_entry: Dict[str, float] = {}
    for alloc in allocations_all:
        paid_total_by_entry.setdefault(alloc.income_expense_id, 0.0)
        paid_total_by_entry[alloc.income_expense_id] += float(alloc.amount or 0)

    plan_income = plan_expense = 0.0
    forecast_income = forecast_expense = 0.0
    for entry in entries:
        amount = float(entry.amount or 0)
        if entry.direction == "income":
            plan_income += amount
        else:
            plan_expense += amount
        paid_total = paid_total_by_entry.get(entry.id, 0.0)
        remaining = max(amount - paid_total, 0.0)
        if remaining > 0:
            if entry.direction == "income":
                forecast_income += remaining
            else:
                forecast_expense += remaining

    actual_income = actual_expense = 0.0
    for alloc, tx in allocations_in_period:
        amount = float(alloc.amount or 0)
        direction = "income" if (tx.amount or 0) >= 0 else "expense"
        if direction == "income":
            actual_income += amount
        else:
            actual_expense += amount

    kpis = {
        "plan_income": plan_income,
        "plan_expense": plan_expense,
        "actual_income": actual_income,
        "actual_expense": actual_expense,
        "forecast_income": forecast_income,
        "forecast_expense": forecast_expense,
        "net_plan": plan_income - plan_expense,
        "net_actual": actual_income - actual_expense,
        "net_forecast": forecast_income - forecast_expense,
    }

    if start and end:
        series_start = start
        series_end = end
    else:
        date_candidates = []
        for entry in entries:
            if entry.plan_date:
                date_candidates.append(entry.plan_date)
        for alloc, tx in allocations_in_period:
            if tx.transaction_date:
                date_candidates.append(tx.transaction_date)
        if not date_candidates:
            series_start = date(today.year, today.month, 1)
            series_end = series_start
        else:
            series_start = min(date_candidates)
            series_end = max(date_candidates)

    months = _iter_months(series_start, series_end)
    month_index = {m: idx for idx, m in enumerate(months)}
    plan_income_series = [0.0 for _ in months]
    plan_expense_series = [0.0 for _ in months]
    actual_income_series = [0.0 for _ in months]
    actual_expense_series = [0.0 for _ in months]
    forecast_income_series = [0.0 for _ in months]
    forecast_expense_series = [0.0 for _ in months]

    for entry in entries:
        bucket = _month_start(entry.plan_date)
        if bucket not in month_index:
            continue
        idx = month_index[bucket]
        amount = float(entry.amount or 0)
        paid_total = paid_total_by_entry.get(entry.id, 0.0)
        remaining = max(amount - paid_total, 0.0)
        if entry.direction == "income":
            plan_income_series[idx] += amount
            if remaining > 0:
                forecast_income_series[idx] += remaining
        else:
            plan_expense_series[idx] += amount
            if remaining > 0:
                forecast_expense_series[idx] += remaining

    for alloc, tx in allocations_in_period:
        bucket = _month_start(tx.transaction_date)
        if bucket not in month_index:
            continue
        idx = month_index[bucket]
        amount = float(alloc.amount or 0)
        direction = "income" if (tx.amount or 0) >= 0 else "expense"
        if direction == "income":
            actual_income_series[idx] += amount
        else:
            actual_expense_series[idx] += amount

    cumulative_plan = []
    cumulative_actual = []
    cumulative_forecast = []
    running_plan = running_actual = running_forecast = 0.0
    for idx in range(len(months)):
        net_plan = plan_income_series[idx] - plan_expense_series[idx]
        net_actual = actual_income_series[idx] - actual_expense_series[idx]
        net_forecast = forecast_income_series[idx] - forecast_expense_series[idx]
        running_plan += net_plan
        running_actual += net_actual
        running_forecast += net_forecast
        cumulative_plan.append(running_plan)
        cumulative_actual.append(running_actual)
        cumulative_forecast.append(running_forecast)

    cashflow = {
        "labels": [m.isoformat() for m in months],
        "plan_income": plan_income_series,
        "plan_expense": plan_expense_series,
        "actual_income": actual_income_series,
        "actual_expense": actual_expense_series,
        "forecast_income": forecast_income_series,
        "forecast_expense": forecast_expense_series,
        "cumulative_plan": cumulative_plan,
        "cumulative_actual": cumulative_actual,
        "cumulative_forecast": cumulative_forecast,
    }

    budget_plan_expense: Dict[str, float] = {}
    budget_plan_income: Dict[str, float] = {}
    entry_category_map = {entry.id: entry.category_code for entry in entries}
    for entry in entries:
        category = entry.category_code or "Без категории"
        amount = float(entry.amount or 0)
        if entry.direction == "expense":
            budget_plan_expense[category] = budget_plan_expense.get(category, 0.0) + amount
        else:
            budget_plan_income[category] = budget_plan_income.get(category, 0.0) + amount

    budget_actual_expense: Dict[str, float] = {}
    budget_actual_income: Dict[str, float] = {}
    for alloc, tx in allocations_in_period:
        category = alloc.category_code or entry_category_map.get(alloc.income_expense_id)
        category = category or "Без категории"
        amount = float(alloc.amount or 0)
        direction = "income" if (tx.amount or 0) >= 0 else "expense"
        if direction == "expense":
            budget_actual_expense[category] = budget_actual_expense.get(category, 0.0) + amount
        else:
            budget_actual_income[category] = budget_actual_income.get(category, 0.0) + amount

    def _build_budget_items(plan_map: Dict[str, float], actual_map: Dict[str, float]) -> List[Dict[str, Any]]:
        categories = set(plan_map.keys()) | set(actual_map.keys())
        items = []
        for cat in categories:
            plan_value = plan_map.get(cat, 0.0)
            actual_value = actual_map.get(cat, 0.0)
            items.append({
                "category": cat,
                "plan": plan_value,
                "actual": actual_value,
                "remainder": max(plan_value - actual_value, 0.0),
            })
        items.sort(key=lambda x: x["plan"], reverse=True)
        return items[:10]

    budget_by_category = {
        "expense": _build_budget_items(budget_plan_expense, budget_actual_expense),
        "income": _build_budget_items(budget_plan_income, budget_actual_income),
    }

    tx_query = select(TreasuryTransaction)
    if start and end:
        tx_query = tx_query.where(
            and_(TreasuryTransaction.transaction_date >= start, TreasuryTransaction.transaction_date <= end)
        )
    tx_result = await db.execute(tx_query)
    transactions = tx_result.scalars().all()
    tx_ids = [tx.id for tx in transactions]

    alloc_by_tx: Dict[str, float] = {}
    if tx_ids:
        alloc_result = await db.execute(
            select(TreasuryAllocation).where(TreasuryAllocation.transaction_id.in_(tx_ids))
        )
        for alloc in alloc_result.scalars().all():
            alloc_by_tx.setdefault(str(alloc.transaction_id), 0.0)
            alloc_by_tx[str(alloc.transaction_id)] += float(alloc.amount or 0)

    treasury_stats = {
        "allocated": {"count": 0, "amount": 0.0},
        "unallocated": {"count": 0, "amount": 0.0},
        "ignored": {"count": 0, "amount": 0.0},
        "aging": [
            {"label": "0-7", "count": 0, "amount": 0.0},
            {"label": "8-30", "count": 0, "amount": 0.0},
            {"label": "31-60", "count": 0, "amount": 0.0},
            {"label": "61+", "count": 0, "amount": 0.0},
        ],
    }

    for tx in transactions:
        amount = abs(float(tx.amount or 0))
        if _is_ignore_flag(tx.ignore_flag):
            treasury_stats["ignored"]["count"] += 1
            treasury_stats["ignored"]["amount"] += amount
            continue
        allocated_amount = alloc_by_tx.get(str(tx.id), 0.0)
        remainder = max(amount - allocated_amount, 0.0)
        if remainder <= 1e-6:
            treasury_stats["allocated"]["count"] += 1
            treasury_stats["allocated"]["amount"] += amount
        else:
            treasury_stats["unallocated"]["count"] += 1
            treasury_stats["unallocated"]["amount"] += remainder
            age_days = (today - tx.transaction_date).days if tx.transaction_date else 0
            if age_days <= 7:
                bucket = 0
            elif age_days <= 30:
                bucket = 1
            elif age_days <= 60:
                bucket = 2
            else:
                bucket = 3
            treasury_stats["aging"][bucket]["count"] += 1
            treasury_stats["aging"][bucket]["amount"] += remainder

    rules_auto = sum(1 for tx in transactions if tx.auto_rule_id)
    rules_total = len(transactions)
    rules_coverage = {
        "total": rules_total,
        "auto": rules_auto,
        "percent": (rules_auto / rules_total * 100.0) if rules_total else 0.0,
    }

    cash_gap = {
        "labels": [m.isoformat() for m in months],
        "balance": cumulative_plan,
        "min_balance": min(cumulative_plan) if cumulative_plan else 0.0,
        "min_date": months[cumulative_plan.index(min(cumulative_plan))].isoformat() if cumulative_plan else None,
    }

    return {
        "period": {
            "start": series_start.isoformat() if series_start else None,
            "end": series_end.isoformat() if series_end else None,
            "label": period,
        },
        "kpis": kpis,
        "cashflow": cashflow,
        "treasury_status": treasury_stats,
        "budget_by_category": budget_by_category,
        "rules_coverage": rules_coverage,
        "cash_gap": cash_gap,
    }

def _parse_transactions_from_csv(
    content: str,
    default_calc_type: str
) -> Tuple[List[Dict[str, Any]], List[str]]:
    errors: List[str] = []
    transactions: List[Dict[str, Any]] = []
    sample = content[:4096]
    delimiter = _detect_delimiter(sample)

    reader = csv.reader(io.StringIO(content), delimiter=delimiter)
    rows = list(reader)
    if not rows:
        return transactions, errors

    header = [h.strip().lower() for h in rows[0]]
    has_header = any(header)

    def _find_index(candidates: List[str]) -> Optional[int]:
        for cand in candidates:
            if cand in header:
                return header.index(cand)
        return None

    if has_header:
        idx_doc = _find_index(["doc_num", "номер", "номер документа", "номер пп", "номер платежа", "№ документа", "№ п/п", "документ №"])
        idx_date = _find_index(["date", "дата", "дата документа", "дата операции", "дата проводки"])
        idx_amount = _find_index(["amount", "сумма", "сумма операции", "сумма платежа", "сумма рублей", "сумма в валюте счета"])
        idx_payer_inn = _find_index(["payer_inn", "инн плательщика", "инн отправителя", "инн плат.", "инн корреспондента"])
        idx_payee_inn = _find_index(["payee_inn", "инн получателя", "инн бенефициара", "инн контрагента"])
        idx_payer_name = _find_index(["payer", "плательщик", "отправитель", "наименование плательщика", "корреспондент", "контрагент"])
        idx_payee_name = _find_index(["payee", "получатель", "бенефициар", "наименование получателя", "наименование бенефициара"])
        idx_purpose = _find_index(["purpose", "назначение", "назначение платежа", "описание операции", "основание платежа"])
        idx_calc = _find_index(["calc_type", "расчет", "тип расчета", "вид операции"])
        data_rows = rows[1:]
    else:
        idx_doc = 0
        idx_date = 1
        idx_amount = 2
        idx_payer_inn = 3
        idx_payee_inn = 4
        idx_payer_name = 5
        idx_payee_name = 6
        idx_purpose = 7
        idx_calc = 8
        data_rows = rows

    for row_index, row in enumerate(data_rows, start=1):
        if not any(cell.strip() for cell in row):
            continue
        try:
            doc_num = row[idx_doc].strip() if idx_doc is not None and idx_doc < len(row) else ""
            date_raw = row[idx_date] if idx_date is not None and idx_date < len(row) else ""
            amount_raw = row[idx_amount] if idx_amount is not None and idx_amount < len(row) else ""
            payer_inn_raw = row[idx_payer_inn] if idx_payer_inn is not None and idx_payer_inn < len(row) else ""
            payee_inn_raw = row[idx_payee_inn] if idx_payee_inn is not None and idx_payee_inn < len(row) else ""
            payer_name = row[idx_payer_name].strip() if idx_payer_name is not None and idx_payer_name < len(row) else ""
            payee_name = row[idx_payee_name].strip() if idx_payee_name is not None and idx_payee_name < len(row) else ""
            purpose = row[idx_purpose].strip() if idx_purpose is not None and idx_purpose < len(row) else ""
            calc_raw = row[idx_calc].strip() if idx_calc is not None and idx_calc < len(row) else ""
            calc_type = _normalize_calc_type(calc_raw, default_calc_type)

            tx_date = _parse_date(str(date_raw))
            amount = _parse_amount(str(amount_raw))

            transactions.append({
                "doc_num": doc_num,
                "transaction_date": tx_date,
                "amount": amount,
                "payer_inn": _normalize_inn(payer_inn_raw),
                "payee_inn": _normalize_inn(payee_inn_raw),
                "payer_name": payer_name,
                "payee_name": payee_name,
                "purpose": purpose,
                "calc_type": calc_type or default_calc_type
            })
        except Exception as e:
            errors.append(f"Row {row_index}: {e}")

    return transactions, errors

# Financial Plans CRUD
@router.get("/plans/", response_model=List[FinancialPlanResponse])
async def get_financial_plans(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """РџРѕР»СѓС‡РёС‚СЊ СЃРїРёСЃРѕРє РІСЃРµС… С„РёРЅР°РЅСЃРѕРІС‹С… РїР»Р°РЅРѕРІ"""
    try:
        plans = await FinancialPlan.get_all(db, skip=skip, limit=limit)
        return plans
    except Exception as e:
        print(f"Error getting financial plans: {e}")
        return []

@router.get("/plans/deal/{deal_id}", response_model=List[FinancialPlanResponse])
async def get_financial_plans_by_deal(
    deal_id: str,
    db: AsyncSession = Depends(get_db)
):
    """РџРѕР»СѓС‡РёС‚СЊ РІСЃРµ С„РёРЅР°РЅСЃРѕРІС‹Рµ РїР»Р°РЅС‹ РїСЂРѕРµРєС‚Р°"""
    try:
        plans = await FinancialPlan.get_by_deal_id(db, deal_id)
        return plans
    except Exception as e:
        print(f"Error getting financial plans for deal {deal_id}: {e}")
        return []

@router.post("/plans/", response_model=FinancialPlanResponse)
async def create_financial_plan(
    plan: FinancialPlanCreate,
    db: AsyncSession = Depends(get_db)
):
    """РЎРѕР·РґР°С‚СЊ РЅРѕРІС‹Р№ С„РёРЅР°РЅСЃРѕРІС‹Р№ РїР»Р°РЅ"""
    try:
        db_plan = await FinancialPlan.create(db, **plan.dict())
        return db_plan
    except Exception as e:
        print(f"Error creating financial plan: {e}")
        raise HTTPException(status_code=400, detail="РћС€РёР±РєР° СЃРѕР·РґР°РЅРёСЏ С„РёРЅР°РЅСЃРѕРІРѕРіРѕ РїР»Р°РЅР°")

@router.get("/plans/{plan_id}", response_model=FinancialPlanResponse)
async def get_financial_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db)
):
    """РџРѕР»СѓС‡РёС‚СЊ С„РёРЅР°РЅСЃРѕРІС‹Р№ РїР»Р°РЅ РїРѕ ID"""
    plan = await FinancialPlan.get_by_id(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Р¤РёРЅР°РЅСЃРѕРІС‹Р№ РїР»Р°РЅ РЅРµ РЅР°Р№РґРµРЅ")
    return plan

@router.put("/plans/{plan_id}", response_model=FinancialPlanResponse)
async def update_financial_plan(
    plan_id: str,
    plan_update: FinancialPlanUpdate,
    db: AsyncSession = Depends(get_db)
):
    """РћР±РЅРѕРІРёС‚СЊ С„РёРЅР°РЅСЃРѕРІС‹Р№ РїР»Р°РЅ"""
    try:
        plan = await FinancialPlan.update(db, plan_id, **plan_update.dict(exclude_unset=True))
        if not plan:
            raise HTTPException(status_code=404, detail="Р¤РёРЅР°РЅСЃРѕРІС‹Р№ РїР»Р°РЅ РЅРµ РЅР°Р№РґРµРЅ")
        return plan
    except Exception as e:
        print(f"Error updating financial plan {plan_id}: {e}")
        raise HTTPException(status_code=400, detail="РћС€РёР±РєР° РѕР±РЅРѕРІР»РµРЅРёСЏ С„РёРЅР°РЅСЃРѕРІРѕРіРѕ РїР»Р°РЅР°")

@router.delete("/plans/{plan_id}")
async def delete_financial_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db)
):
    """РЈРґР°Р»РёС‚СЊ С„РёРЅР°РЅСЃРѕРІС‹Р№ РїР»Р°РЅ"""
    success = await FinancialPlan.delete(db, plan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Р¤РёРЅР°РЅСЃРѕРІС‹Р№ РїР»Р°РЅ РЅРµ РЅР°Р№РґРµРЅ")
    return {"message": "Р¤РёРЅР°РЅСЃРѕРІС‹Р№ РїР»Р°РЅ СѓРґР°Р»РµРЅ"}

# Financial Analysis
@router.get("/pv/{deal_id}")
async def calculate_pv(
    deal_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Р Р°СЃС‡РµС‚ Present Value РґР»СЏ РїСЂРѕРµРєС‚Р°"""
    try:
        deal_uuid = _parse_uuid(deal_id, "deal_id")
        result = await FinanceService.calculate_pv(deal_uuid, db)
        return result
    except Exception as e:
        print(f"Error calculating PV for deal {deal_id}: {e}")
        raise HTTPException(status_code=400, detail="РћС€РёР±РєР° СЂР°СЃС‡РµС‚Р° PV")

@router.get("/penalties/{deal_id}")
async def calculate_penalties(
    deal_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Р Р°СЃС‡РµС‚ РЅРµСѓСЃС‚РѕРµРє РґР»СЏ РїСЂРѕРµРєС‚Р°"""
    try:
        deal_uuid = _parse_uuid(deal_id, "deal_id")
        result = await FinanceService.calculate_penalties(deal_uuid, db)
        return result
    except Exception as e:
        print(f"Error calculating penalties for deal {deal_id}: {e}")
        raise HTTPException(status_code=400, detail="РћС€РёР±РєР° СЂР°СЃС‡РµС‚Р° РЅРµСѓСЃС‚РѕРµРє")

# Bank Statement Import
@router.post("/import-bank-statement/preview")
async def preview_bank_statement(
    file: UploadFile = File(...),
    default_calc_type: str = "vtb",
    db: AsyncSession = Depends(get_db)
):
    try:
        content = await file.read()
        file_content = _decode_file(content)
        transactions_data, parse_errors = _parse_transactions_from_csv(
            file_content,
            default_calc_type
        )

        inns = set()
        for tx in transactions_data:
            if tx.get("payer_inn"):
                inns.add(tx["payer_inn"])
            if tx.get("payee_inn"):
                inns.add(tx["payee_inn"])

        existing_inns = set()
        if inns:
            query = select(Company.inn).where(Company.inn.in_(inns))
            result = await db.execute(query)
            existing_inns = {row[0] for row in result.fetchall()}

        preview_rows = []
        duplicate_count = 0
        missing_companies = {}

        for idx, tx in enumerate(transactions_data, start=1):
            dup_query = select(TreasuryTransaction).where(
                and_(
                    TreasuryTransaction.doc_num == tx["doc_num"],
                    TreasuryTransaction.transaction_date == tx["transaction_date"],
                    TreasuryTransaction.amount == tx["amount"]
                )
            )
            dup_result = await db.execute(dup_query)
            is_duplicate = dup_result.scalar_one_or_none() is not None
            if is_duplicate:
                duplicate_count += 1

            payer_inn = tx.get("payer_inn")
            payee_inn = tx.get("payee_inn")
            missing_payer = payer_inn and payer_inn not in existing_inns
            missing_payee = payee_inn and payee_inn not in existing_inns

            if missing_payer:
                missing_companies[payer_inn] = tx.get("payer_name") or "No Name"
            if missing_payee:
                missing_companies[payee_inn] = tx.get("payee_name") or "No Name"

            preview_rows.append({
                "index": idx,
                "doc_num": tx["doc_num"],
                "transaction_date": tx["transaction_date"].isoformat(),
                "amount": tx["amount"],
                "payer_inn": payer_inn,
                "payee_inn": payee_inn,
                "payer_name": tx.get("payer_name"),
                "payee_name": tx.get("payee_name"),
                "purpose": tx.get("purpose"),
                "calc_type": tx.get("calc_type"),
                "is_duplicate": is_duplicate,
                "missing_payer": bool(missing_payer),
                "missing_payee": bool(missing_payee)
            })

        return {
            "total_rows": len(preview_rows),
            "duplicate_count": duplicate_count,
            "missing_companies": [
                {"inn": inn, "name": name} for inn, name in missing_companies.items()
            ],
            "parse_errors": parse_errors,
            "rows": preview_rows
        }
    except Exception as e:
        print(f"Error previewing bank statement: {e}")
        raise HTTPException(status_code=400, detail="Ошибка предпросмотра выписки")

@router.post("/import-bank-statement/confirm")
async def import_bank_statement_confirm(
    file: UploadFile = File(...),
    create_missing_companies: bool = False,
    default_calc_type: str = "vtb",
    db: AsyncSession = Depends(get_db)
):
    try:
        content = await file.read()
        file_content = _decode_file(content)
        transactions_data, parse_errors = _parse_transactions_from_csv(
            file_content,
            default_calc_type
        )
        result = await FinanceService.import_bank_statement(
            transactions_data,
            db,
            create_missing_companies=create_missing_companies,
            default_calc_type=default_calc_type
        )
        result["parse_errors"] = parse_errors
        return result
    except Exception as e:
        print(f"Error importing bank statement: {e}")
        raise HTTPException(status_code=400, detail="Ошибка импорта выписки")

# Treasury Transactions
@router.get("/treasury/transactions")
async def list_treasury_transactions(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    payer: Optional[str] = None,
    payee: Optional[str] = None,
    payer_name: Optional[str] = None,
    payee_name: Optional[str] = None,
    tx_type: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    calc_type: Optional[str] = None,
    income_expense_id: Optional[str] = None,
    unlinked_only: bool = False,
    db: AsyncSession = Depends(get_db)
):
    skip = max(0, skip)
    limit = max(1, min(limit, 500))

    # Use payer_name/payee_name if provided
    payer = payer or payer_name
    payee = payee or payee_name
    
    query = select(TreasuryTransaction)
    dialect_name = ""
    try:
        dialect_name = db.get_bind().dialect.name
    except Exception:
        dialect_name = ""
    search = search.strip() if search else None
    payer = payer.strip() if payer else None
    payee = payee.strip() if payee else None
    use_python_search = bool(
        dialect_name == "sqlite"
        and any(value and any(ord(ch) > 127 for ch in value) for value in (search, payer, payee))
    )

    if tx_type == "expense":
        query = query.where(TreasuryTransaction.amount < 0)
    elif tx_type == "income":
        query = query.where(TreasuryTransaction.amount >= 0)

    if calc_type:
        query = query.where(TreasuryTransaction.calc_type == calc_type)

    if category:
        query = query.outerjoin(TreasuryAllocation, TreasuryAllocation.transaction_id == TreasuryTransaction.id).where(
            or_(
                TreasuryAllocation.category_code == category,
                and_(TreasuryAllocation.id.is_(None), TreasuryTransaction.category_code == category),
            )
        )

    if income_expense_id:
        query = query.join(TreasuryAllocation, TreasuryAllocation.transaction_id == TreasuryTransaction.id).where(
            TreasuryAllocation.income_expense_id == income_expense_id
        )
    elif unlinked_only:
        query = query.outerjoin(TreasuryAllocation, TreasuryAllocation.transaction_id == TreasuryTransaction.id).where(
            TreasuryAllocation.id.is_(None)
        )

    if search and not use_python_search:
        pattern = f"%{search}%"
        query = query.where(
            or_(
                TreasuryTransaction.doc_num.ilike(pattern),
                TreasuryTransaction.purpose.ilike(pattern),
                TreasuryTransaction.payer_name.ilike(pattern),
                TreasuryTransaction.payee_name.ilike(pattern),
            )
        )

    if payer and not use_python_search:
        pattern = f"%{payer}%"
        query = query.where(
            or_(
                TreasuryTransaction.payer_name.ilike(pattern),
                TreasuryTransaction.payer_inn.ilike(pattern)
            )
        )

    if payee and not use_python_search:
        pattern = f"%{payee}%"
        query = query.where(
            or_(
                TreasuryTransaction.payee_name.ilike(pattern),
                TreasuryTransaction.payee_inn.ilike(pattern)
            )
        )

    result = await db.execute(query.order_by(TreasuryTransaction.transaction_date.desc()))
    items = result.scalars().all()

    if use_python_search:
        search_cf = search.casefold() if search else None
        payer_cf = payer.casefold() if payer else None
        payee_cf = payee.casefold() if payee else None

        def _contains(haystack: str, needle: str) -> bool:
            return needle in haystack

        filtered = []
        for item in items:
            doc_num = (item.doc_num or "").casefold()
            purpose = (item.purpose or "").casefold()
            payer_name_val = (item.payer_name or "").casefold()
            payee_name_val = (item.payee_name or "").casefold()
            payer_inn_val = (item.payer_inn or "").casefold()
            payee_inn_val = (item.payee_inn or "").casefold()

            if search_cf:
                if not _contains(doc_num, search_cf) and not _contains(purpose, search_cf) and not _contains(payer_name_val, search_cf) and not _contains(payee_name_val, search_cf):
                    continue
            if payer_cf:
                if not _contains(payer_name_val, payer_cf) and not _contains(payer_inn_val, payer_cf):
                    continue
            if payee_cf:
                if not _contains(payee_name_val, payee_cf) and not _contains(payee_inn_val, payee_cf):
                    continue

            filtered.append(item)
        items = filtered

    tx_ids = [str(item.id) for item in items]
    tx_uuids = [uuid.UUID(i) for i in tx_ids] if tx_ids else []

    alloc_map: Dict[str, List[TreasuryAllocation]] = {}
    if tx_uuids:
        alloc_result = await db.execute(
            select(TreasuryAllocation)
            .where(TreasuryAllocation.transaction_id.in_(tx_uuids))
        )
        for allocation in alloc_result.scalars().all():
            alloc_map.setdefault(str(allocation.transaction_id), []).append(allocation)

    # Загружаем привязанные платежи (возвраты): те, у которых linked_transaction_id IN (наши id)
    linked_map: Dict[str, List[TreasuryTransaction]] = {}
    if tx_uuids:
        linked_result = await db.execute(
            select(TreasuryTransaction)
            .where(TreasuryTransaction.linked_transaction_id.in_(tx_uuids))
        )
        for lp in linked_result.scalars().all():
            linked_map.setdefault(str(lp.linked_transaction_id), []).append(lp)

    def _get_allocated(item: TreasuryTransaction) -> float:
        allocations = alloc_map.get(str(item.id), [])
        linked_list = linked_map.get(str(item.id), [])
        return sum(a.amount for a in allocations) + sum(abs(lp.amount) for lp in linked_list)

    def is_ok(item: TreasuryTransaction) -> bool:
        if _is_ignore_flag(item.ignore_flag):
            return True
        allocations = alloc_map.get(str(item.id), [])
        if allocations:
            return all(a.category_code for a in allocations)
        return bool(item.category_code)

    def is_fully_allocated(item: TreasuryTransaction) -> bool:
        if _is_ignore_flag(item.ignore_flag):
            return False
        total_amount = abs(item.amount)
        return _get_allocated(item) >= total_amount * 0.99

    def is_ignored(item: TreasuryTransaction) -> bool:
        return _is_ignore_flag(item.ignore_flag)

    # New status filter values: allocated, not_allocated, ignored
    if status == "allocated":
        items = [item for item in items if is_fully_allocated(item)]
    elif status == "not_allocated":
        items = [item for item in items if not is_fully_allocated(item) and not is_ignored(item)]
    elif status == "ignored":
        items = [item for item in items if is_ignored(item)]
    elif status == "ok":
        items = [item for item in items if is_ok(item)]
    elif status == "alert":
        items = [item for item in items if not is_ok(item)]

    total = len(items)
    ok_count = len([item for item in items if is_fully_allocated(item)])
    ignored_count = len([item for item in items if is_ignored(item)])
    alert_count = total - ok_count - ignored_count

    paged = items[skip:skip + limit]
    response_items: List[TreasuryTransactionResponse] = []
    for item in paged:
        allocations = alloc_map.get(str(item.id), [])
        linked_list = linked_map.get(str(item.id), [])
        response_items.append(_build_tx_response(item, allocations, linked_list))

    return {
        "items": response_items,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": skip + len(response_items) < total,
        "stats": {
            "total": total,
            "ok": ok_count,
            "alert": alert_count,
            "ignored": ignored_count
        }
    }


@router.post("/treasury/transactions", response_model=TreasuryTransactionResponse)
async def create_treasury_transaction(
    payload: TreasuryTransactionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new treasury transaction manually."""
    # Check for duplicate
    dup_query = select(TreasuryTransaction).where(
        and_(
            TreasuryTransaction.doc_num == payload.doc_num,
            TreasuryTransaction.transaction_date == payload.transaction_date,
            TreasuryTransaction.amount == payload.amount
        )
    )
    dup_result = await db.execute(dup_query)
    if dup_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Транзакция с такими данными уже существует")

    tx = TreasuryTransaction(
        id=uuid.uuid4(),
        doc_num=payload.doc_num,
        transaction_date=payload.transaction_date,
        amount=payload.amount,
        calc_type=payload.calc_type or "vtb",
        payer_inn=payload.payer_inn,
        payee_inn=payload.payee_inn,
        payer_name=payload.payer_name,
        payee_name=payload.payee_name,
        purpose=payload.purpose,
        category_code=payload.category_code,
        ignore_flag=payload.ignore_flag or "Нет",
    )
    db.add(tx)
    await db.flush()
    
    # Apply auto-rules if no category already set
    if not tx.category_code and tx.ignore_flag != "Да":
        await apply_rules_to_transaction(tx, db)
    
    await db.commit()
    await db.refresh(tx)

    return _build_tx_response(tx, [])


@router.patch("/treasury/transactions/{tx_id}", response_model=TreasuryTransactionResponse)
async def update_treasury_transaction(
    tx_id: str,
    payload: TreasuryTransactionUpdate,
    db: AsyncSession = Depends(get_db)
):
    tx_uuid = _parse_uuid(tx_id, "tx_id")
    result = await db.execute(select(TreasuryTransaction).where(TreasuryTransaction.id == tx_uuid))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")

    update_data = payload.dict(exclude_unset=True)
    if "ignore_flag" in update_data and isinstance(update_data["ignore_flag"], bool):
        update_data["ignore_flag"] = "Да" if update_data["ignore_flag"] else "Нет"

    allocation_entry_id = None
    if "income_expense_id" in update_data:
        allocation_entry_id = update_data.pop("income_expense_id") or None

    for key, value in update_data.items():
        setattr(tx, key, value)

    # Compatibility: map income_expense_id to allocations (full amount)
    if allocation_entry_id is not None:
        if allocation_entry_id:
            check = await db.execute(
                select(IncomeExpenseEntry).where(IncomeExpenseEntry.id == allocation_entry_id)
            )
            if not check.scalar_one_or_none():
                raise HTTPException(status_code=404, detail="Entry not found")
        await db.execute(delete(TreasuryAllocation).where(TreasuryAllocation.transaction_id == tx.id))
        if allocation_entry_id:
            allocation = TreasuryAllocation(
                transaction_id=tx.id,
                income_expense_id=allocation_entry_id,
                amount=abs(tx.amount),
                category_code=tx.category_code,
            )
            db.add(allocation)

    await db.commit()
    await db.refresh(tx)

    alloc_result = await db.execute(
        select(TreasuryAllocation).where(TreasuryAllocation.transaction_id == tx.id)
    )
    allocations = alloc_result.scalars().all()
    return _build_tx_response(tx, allocations)


@router.delete("/treasury/transactions/{tx_id}")
async def delete_treasury_transaction(
    tx_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a treasury transaction and its allocations."""
    tx_uuid = _parse_uuid(tx_id, "tx_id")
    result = await db.execute(select(TreasuryTransaction).where(TreasuryTransaction.id == tx_uuid))
    tx = result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")

    # Delete allocations first
    await db.execute(delete(TreasuryAllocation).where(TreasuryAllocation.transaction_id == tx_uuid))
    
    # Delete transaction
    await db.delete(tx)
    await db.commit()
    return {"message": "Транзакция удалена"}


@router.post("/treasury/transactions/bulk-action")
async def bulk_action_treasury_transactions(
    payload: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk action on multiple transactions.
    Actions: category, calc_type, ignore, create_dds
    """
    transaction_ids = payload.get("transaction_ids", [])
    action = payload.get("action")
    
    if not transaction_ids or not action:
        raise HTTPException(status_code=400, detail="transaction_ids and action required")
    
    # Get transactions
    tx_uuids = [_parse_uuid(tid, "id") for tid in transaction_ids]
    result = await db.execute(
        select(TreasuryTransaction).where(TreasuryTransaction.id.in_(tx_uuids))
    )
    transactions = result.scalars().all()
    
    if not transactions:
        raise HTTPException(status_code=404, detail="Transactions not found")
    
    updated_count = 0
    
    if action == "category":
        category_code = payload.get("category_code")
        if not category_code:
            raise HTTPException(status_code=400, detail="category_code required")
        for tx in transactions:
            tx.category_code = category_code
            updated_count += 1
    
    elif action == "calc_type":
        calc_type = payload.get("calc_type")
        if not calc_type:
            raise HTTPException(status_code=400, detail="calc_type required")
        for tx in transactions:
            tx.calc_type = calc_type
            updated_count += 1
    
    elif action == "ignore":
        for tx in transactions:
            tx.ignore_flag = "Да"
            updated_count += 1
    
    elif action == "create_dds":
        from datetime import date as date_module
        category_code = payload.get("category_code")
        try:
            from app.models.company import Company
        except Exception:
            Company = None
        
        for tx in transactions:
            # Check if already has allocation
            existing = await db.execute(
                select(TreasuryAllocation).where(TreasuryAllocation.transaction_id == tx.id)
            )
            if existing.scalar_one_or_none():
                continue  # Skip if already allocated

            linked_result = await db.execute(
                select(TreasuryTransaction).where(TreasuryTransaction.linked_transaction_id == tx.id)
            )
            linked_sum = sum(abs(lp.amount) for lp in linked_result.scalars().all())
            total_amount = abs(tx.amount)
            remaining_amount = total_amount - linked_sum
            if remaining_amount <= 0:
                continue

            direction = "expense" if tx.amount < 0 else "income"
            entry = IncomeExpenseEntry(
                id=str(uuid.uuid4()),
                direction=direction,
                amount=remaining_amount,
                plan_date=tx.transaction_date or date_module.today(),
                actual_date=tx.transaction_date,
                payer_id=None,
                payee_id=None,
                category_code=category_code or tx.category_code,
            )

            # Try to link payer/payee by INN if possible
            if Company:
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
                    # Do not block if INN lookup fails
                    pass
            db.add(entry)
            await db.flush()
            
            allocation = TreasuryAllocation(
                transaction_id=tx.id,
                income_expense_id=entry.id,
                amount=remaining_amount,
                category_code=category_code or tx.category_code,
            )
            db.add(allocation)
            tx.income_expense_id = entry.id
            if category_code:
                tx.category_code = category_code
            updated_count += 1
    
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")
    
    await db.commit()
    return {"message": f"Обновлено {updated_count} транзакций", "updated_count": updated_count}


@router.post("/treasury/transactions/{tx_id}/link")
async def link_payment(
    tx_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db)
):
    """Привязать платёж linked_transaction_id к платежу tx_id (возврат/зачёт)."""
    tx_uuid = _parse_uuid(tx_id, "tx_id")
    linked_id_raw = payload.get("linked_transaction_id")
    if not linked_id_raw:
        raise HTTPException(status_code=400, detail="linked_transaction_id is required")
    linked_uuid = _parse_uuid(linked_id_raw, "linked_transaction_id")

    if str(tx_uuid) == str(linked_uuid):
        raise HTTPException(status_code=400, detail="Cannot link transaction to itself")

    tx_result = await db.execute(select(TreasuryTransaction).where(TreasuryTransaction.id == tx_uuid))
    tx = tx_result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    linked_result = await db.execute(select(TreasuryTransaction).where(TreasuryTransaction.id == linked_uuid))
    linked = linked_result.scalar_one_or_none()
    if not linked:
        raise HTTPException(status_code=404, detail="Linked transaction not found")

    if linked.linked_transaction_id:
        raise HTTPException(status_code=400, detail="This payment is already linked to another transaction")

    linked.linked_transaction_id = tx_uuid
    linked.ignore_flag = "Да"
    await db.commit()
    return {"message": "Payment linked successfully"}


@router.delete("/treasury/transactions/{tx_id}/link/{linked_id}")
async def unlink_payment(
    tx_id: str,
    linked_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Отвязать платёж linked_id от платежа tx_id."""
    tx_uuid = _parse_uuid(tx_id, "tx_id")
    linked_uuid = _parse_uuid(linked_id, "linked_id")

    linked_result = await db.execute(select(TreasuryTransaction).where(TreasuryTransaction.id == linked_uuid))
    linked = linked_result.scalar_one_or_none()
    if not linked:
        raise HTTPException(status_code=404, detail="Linked transaction not found")

    if str(linked.linked_transaction_id) != str(tx_uuid):
        raise HTTPException(status_code=400, detail="This payment is not linked to the specified transaction")

    linked.linked_transaction_id = None
    linked.ignore_flag = "Нет"
    await db.commit()
    return {"message": "Payment unlinked successfully"}


@router.get("/treasury/transactions/{tx_id}/linked", response_model=List[LinkedPaymentInfo])
async def get_linked_payments(
    tx_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Получить платежи, привязанные к данной транзакции."""
    tx_uuid = _parse_uuid(tx_id, "tx_id")
    result = await db.execute(
        select(TreasuryTransaction).where(TreasuryTransaction.linked_transaction_id == tx_uuid)
    )
    linked = result.scalars().all()
    return [
        LinkedPaymentInfo(
            id=lp.id,
            doc_num=lp.doc_num,
            transaction_date=lp.transaction_date,
            amount=lp.amount,
        )
        for lp in linked
    ]


@router.get("/treasury/transactions/{tx_id}/allocations", response_model=List[TreasuryAllocationResponse])
async def list_treasury_allocations(
    tx_id: str,
    db: AsyncSession = Depends(get_db)
):
    tx_uuid = _parse_uuid(tx_id, "tx_id")
    alloc_result = await db.execute(
        select(TreasuryAllocation).where(TreasuryAllocation.transaction_id == tx_uuid)
    )
    return [TreasuryAllocationResponse.model_validate(a) for a in alloc_result.scalars().all()]


@router.post("/treasury/transactions/{tx_id}/allocations", response_model=TreasuryAllocationResponse)
async def create_treasury_allocation(
    tx_id: str,
    payload: TreasuryAllocationCreate,
    db: AsyncSession = Depends(get_db)
):
    tx_uuid = _parse_uuid(tx_id, "tx_id")
    tx_result = await db.execute(select(TreasuryTransaction).where(TreasuryTransaction.id == tx_uuid))
    tx = tx_result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if payload.amount is None or payload.amount <= 0:
        raise HTTPException(status_code=400, detail="Allocation amount must be greater than 0")

    direction = "expense" if tx.amount < 0 else "income"

    if not _is_ignore_flag(tx.ignore_flag) and not payload.category_code:
        raise HTTPException(status_code=400, detail="Category is required unless transaction is ignored")

    # Проверка остатка
    existing_result = await db.execute(
        select(TreasuryAllocation).where(TreasuryAllocation.transaction_id == tx.id)
    )
    existing = existing_result.scalars().all()
    allocated_amount = sum(a.amount for a in existing)
    # Учитываем привязанные платежи
    linked_result = await db.execute(
        select(TreasuryTransaction).where(TreasuryTransaction.linked_transaction_id == tx.id)
    )
    linked_sum = sum(abs(lp.amount) for lp in linked_result.scalars().all())
    total_amount = abs(tx.amount)
    remaining_amount = total_amount - allocated_amount - linked_sum
    if remaining_amount < 0:
        remaining_amount = 0

    # Определяем income_expense_id: из payload или автосоздаём ДДС
    income_expense_id = None
    allocation_amount = payload.amount
    if payload.income_expense_id:
        entry_result = await db.execute(
            select(IncomeExpenseEntry).where(IncomeExpenseEntry.id == str(payload.income_expense_id))
        )
        entry = entry_result.scalar_one_or_none()
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        if entry.direction != direction:
            raise HTTPException(status_code=400, detail="Entry direction does not match transaction")
        income_expense_id = str(payload.income_expense_id)
        if allocation_amount > (remaining_amount + 1e-6):
            raise HTTPException(status_code=400, detail="Allocation exceeds remaining amount")
    else:
        if remaining_amount <= 0:
            raise HTTPException(status_code=400, detail="No remaining amount to allocate")
        # Автосоздание записи ДДС
        if not payload.category_code:
            raise HTTPException(status_code=400, detail="Category is required to auto-create DDS entry")
        allocation_amount = remaining_amount
        new_entry = IncomeExpenseEntry(
            direction=direction,
            amount=allocation_amount,
            plan_date=tx.transaction_date,
            category_code=payload.category_code,
        )
        db.add(new_entry)
        await db.flush()
        income_expense_id = new_entry.id

    allocation = TreasuryAllocation(
        transaction_id=tx.id,
        income_expense_id=income_expense_id,
        amount=allocation_amount,
        category_code=payload.category_code,
    )
    db.add(allocation)
    await db.commit()
    await db.refresh(allocation)
    return TreasuryAllocationResponse.model_validate(allocation)


@router.patch("/treasury/allocations/{alloc_id}", response_model=TreasuryAllocationResponse)
async def update_treasury_allocation(
    alloc_id: str,
    payload: TreasuryAllocationUpdate,
    db: AsyncSession = Depends(get_db)
):
    alloc_uuid = _parse_uuid(alloc_id, "alloc_id")
    alloc_result = await db.execute(select(TreasuryAllocation).where(TreasuryAllocation.id == alloc_uuid))
    allocation = alloc_result.scalar_one_or_none()
    if not allocation:
        raise HTTPException(status_code=404, detail="Allocation not found")

    tx_result = await db.execute(select(TreasuryTransaction).where(TreasuryTransaction.id == allocation.transaction_id))
    tx = tx_result.scalar_one_or_none()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    update_data = payload.dict(exclude_unset=True)
    if "income_expense_id" in update_data and update_data["income_expense_id"]:
        entry_result = await db.execute(
            select(IncomeExpenseEntry).where(IncomeExpenseEntry.id == str(update_data["income_expense_id"]))
        )
        entry = entry_result.scalar_one_or_none()
        if not entry:
            raise HTTPException(status_code=404, detail="Entry not found")
        direction = "expense" if tx.amount < 0 else "income"
        if entry.direction != direction:
            raise HTTPException(status_code=400, detail="Entry direction does not match transaction")

    if "amount" in update_data:
        if update_data["amount"] is None or update_data["amount"] <= 0:
            raise HTTPException(status_code=400, detail="Allocation amount must be greater than 0")

    if not _is_ignore_flag(tx.ignore_flag) and "category_code" in update_data and not update_data["category_code"]:
        raise HTTPException(status_code=400, detail="Category is required unless transaction is ignored")

    # Check remainder with updated amount
    if "amount" in update_data:
        existing_result = await db.execute(
            select(TreasuryAllocation).where(TreasuryAllocation.transaction_id == allocation.transaction_id)
        )
        existing = existing_result.scalars().all()
        other_amount = sum(a.amount for a in existing if str(a.id) != str(allocation.id))
        total_amount = abs(tx.amount)
        if update_data["amount"] > (total_amount - other_amount + 1e-6):
            raise HTTPException(status_code=400, detail="Allocation exceeds remaining amount")

    for key, value in update_data.items():
        setattr(allocation, key, value)

    await db.commit()
    await db.refresh(allocation)
    return TreasuryAllocationResponse.model_validate(allocation)


@router.delete("/treasury/allocations/{alloc_id}")
async def delete_treasury_allocation(
    alloc_id: str,
    db: AsyncSession = Depends(get_db)
):
    alloc_uuid = _parse_uuid(alloc_id, "alloc_id")
    result = await db.execute(delete(TreasuryAllocation).where(TreasuryAllocation.id == alloc_uuid))
    await db.commit()
    if result.rowcount <= 0:
        raise HTTPException(status_code=404, detail="Allocation not found")
    return {"message": "Allocation deleted"}

# Financial Summary
@router.get("/summary/{deal_id}")
async def get_financial_summary(
    deal_id: str,
    db: AsyncSession = Depends(get_db)
):
    """РџРѕР»СѓС‡РёС‚СЊ С„РёРЅР°РЅСЃРѕРІСѓСЋ СЃРІРѕРґРєСѓ РїРѕ РїСЂРѕРµРєС‚Сѓ"""
    try:
        # Get PV data
        deal_uuid = _parse_uuid(deal_id, "deal_id")
        pv_data = await FinanceService.calculate_pv(deal_uuid, db)

        # Get penalty data
        penalty_data = await FinanceService.calculate_penalties(deal_uuid, db)

        # Get deal info
        deal_query = Deal.__table__.select().where(Deal.__table__.c.id == deal_uuid)
        deal_result = await db.execute(deal_query)
        deal = deal_result.first()

        return {
            "deal_id": str(deal_uuid),
            "deal_title": deal.title if deal else "Unknown",
            "pv_analysis": pv_data,
            "penalty_analysis": penalty_data,
            "summary": {
                "planned_income": pv_data["summary"]["total_plan_income"],
                "planned_expense": pv_data["summary"]["total_plan_expense"],
                "actual_income": pv_data["summary"]["total_fact_income"],
                "actual_expense": pv_data["summary"]["total_fact_expense"],
                "pv_income": pv_data["summary"]["total_pv_income"],
                "pv_expense": pv_data["summary"]["total_pv_expense"],
                "inflation_loss": pv_data["summary"]["net_inflation_loss"],
                "total_penalties": penalty_data["net_penalty"]
            }
        }

    except Exception as e:
        print(f"Error getting financial summary for deal {deal_id}: {e}")
        raise HTTPException(status_code=400, detail="Ошибка получения финансовой сводки")


# ===================== TREASURY AUTO RULES =====================

async def _apply_rule_to_transaction(
    rule: TreasuryAutoRule,
    tx: TreasuryTransaction,
    db: AsyncSession
) -> bool:
    """Apply a rule to a transaction. Returns True if applied."""
    return await FinanceService.apply_rule_to_transaction(rule, tx, db)


async def apply_rules_to_transaction(tx: TreasuryTransaction, db: AsyncSession) -> Optional[str]:
    """Apply first matching rule to a transaction. Returns rule_id if applied."""
    return await FinanceService.apply_auto_rules(tx, db)


@router.get("/treasury/rules", response_model=List[TreasuryAutoRuleResponse])
async def list_treasury_rules(db: AsyncSession = Depends(get_db)):
    """Get all auto-allocation rules."""
    result = await db.execute(
        select(TreasuryAutoRule).order_by(TreasuryAutoRule.priority)
    )
    return [TreasuryAutoRuleResponse.model_validate(r) for r in result.scalars().all()]


@router.post("/treasury/rules", response_model=TreasuryAutoRuleResponse)
async def create_treasury_rule(
    payload: TreasuryAutoRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new auto-allocation rule."""
    rule = TreasuryAutoRule(
        id=str(uuid.uuid4()),
        name=payload.name,
        match_text=payload.match_text,
        match_type=payload.match_type,
        action_type=payload.action_type,
        category_code=payload.category_code,
        create_dds=payload.create_dds,
        is_active=payload.is_active,
        priority=payload.priority,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return TreasuryAutoRuleResponse.model_validate(rule)


@router.put("/treasury/rules/{rule_id}", response_model=TreasuryAutoRuleResponse)
async def update_treasury_rule(
    rule_id: str,
    payload: TreasuryAutoRuleUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an auto-allocation rule."""
    result = await db.execute(
        select(TreasuryAutoRule).where(TreasuryAutoRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Правило не найдено")
    
    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)
    
    await db.commit()
    await db.refresh(rule)
    return TreasuryAutoRuleResponse.model_validate(rule)


@router.delete("/treasury/rules/{rule_id}")
async def delete_treasury_rule(
    rule_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete an auto-allocation rule."""
    result = await db.execute(
        select(TreasuryAutoRule).where(TreasuryAutoRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Правило не найдено")
    
    await db.delete(rule)
    await db.commit()
    return {"message": "Правило удалено"}


@router.post("/treasury/rules/{rule_id}/apply-all")
async def apply_rule_to_all(
    rule_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Apply a rule to all existing transactions that match."""
    result = await db.execute(
        select(TreasuryAutoRule).where(TreasuryAutoRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Правило не найдено")
    
    # Get all transactions without this rule applied
    tx_result = await db.execute(
        select(TreasuryTransaction).where(
            or_(
                TreasuryTransaction.auto_rule_id.is_(None),
                TreasuryTransaction.auto_rule_id != rule_id
            )
        )
    )
    transactions = tx_result.scalars().all()
    
    applied_count = 0
    for tx in transactions:
        if await _apply_rule_to_transaction(rule, tx, db):
            applied_count += 1
    
    await db.commit()
    return {"applied_count": applied_count, "total_checked": len(transactions)}
