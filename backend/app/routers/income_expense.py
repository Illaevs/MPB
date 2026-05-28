"""
Income/Expense registry API Router
"""
from typing import Optional, List, Dict
import uuid
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.exc import IntegrityError

from app.database.session import get_db
from app.core.auth_middleware import CurrentUser
from app.models import IncomeExpenseEntry, TreasuryTransaction, TreasuryAllocation, Company, Deal, Contract, Task
from app.schemas.income_expense import (
    IncomeExpenseEntryCreate,
    IncomeExpenseEntryUpdate,
    IncomeExpenseEntryResponse,
    PaymentHistoryItem,
)
from app.services.permissions import allowed_deal_ids, get_section_permissions, ensure_can_edit_record

router = APIRouter()


def _status_from_paid(amount: float, paid_amount: float) -> str:
    if amount <= 0:
        return "paid"
    if paid_amount <= 0:
        return "unpaid"
    if paid_amount + 1e-9 < amount:
        return "partial"
    return "paid"

def _validate_direction(value: Optional[str]):
    if value is None:
        return
    if value not in ("income", "expense"):
        raise HTTPException(status_code=400, detail="Invalid direction")


def _parse_uuid(value: Optional[str]) -> Optional[uuid.UUID]:
    if not value:
        return None
    try:
        return value if isinstance(value, uuid.UUID) else uuid.UUID(str(value))
    except (ValueError, TypeError):
        return None

async def _build_entry_response(db: AsyncSession, entry: IncomeExpenseEntry) -> IncomeExpenseEntryResponse:
    company_map: Dict[str, Company] = {}
    company_ids = {entry.payer_id, entry.payee_id} - {None}
    if company_ids:
        company_result = await db.execute(select(Company).where(Company.id.in_(company_ids)))
        company_map = {c.id: c for c in company_result.scalars().all()}

    history: List[PaymentHistoryItem] = []
    paid_amount = 0.0
    alloc_result = await db.execute(
        select(TreasuryAllocation, TreasuryTransaction)
        .join(TreasuryTransaction, TreasuryAllocation.transaction_id == TreasuryTransaction.id)
        .where(TreasuryAllocation.income_expense_id == entry.id)
        .order_by(TreasuryTransaction.transaction_date.asc())
    )
    for allocation, tx in alloc_result.all():
        history.append(PaymentHistoryItem(
            transaction_id=str(tx.id),
            transaction_date=tx.transaction_date,
            amount=allocation.amount,
            doc_num=tx.doc_num,
            allocation_id=str(allocation.id),
            category_code=allocation.category_code
        ))
        paid_amount += allocation.amount

    payment_status = _status_from_paid(entry.amount, paid_amount)
    deal_title = None
    contract_number = None
    warning = None
    if entry.deal_id:
        deal_result = await db.execute(select(Deal).where(Deal.id == entry.deal_id))
        deal = deal_result.scalar_one_or_none()
        if deal:
            deal_title = deal.title
    if entry.contract_id:
        contract = await Contract.get_by_id(db, entry.contract_id)
        if contract:
            contract_number = contract.contract_number
            if contract.contract_type != "services" and contract.amount and entry.amount > contract.amount:
                warning = "Плановая сумма больше суммы договора"

    return IncomeExpenseEntryResponse(
        id=str(entry.id),
        direction=entry.direction,
        amount=entry.amount,
        plan_date=entry.plan_date,
        actual_date=entry.actual_date,
        payer_id=entry.payer_id,
        payee_id=entry.payee_id,
        deal_id=entry.deal_id,
        contract_id=entry.contract_id,
        stage_id=entry.stage_id,
        category_code=entry.category_code,
        payer_name=company_map.get(entry.payer_id).name if entry.payer_id in company_map else None,
        payee_name=company_map.get(entry.payee_id).name if entry.payee_id in company_map else None,
        deal_title=deal_title,
        contract_number=contract_number,
        payment_status=payment_status,
        paid_amount=paid_amount,
        payments_history=history,
        warning=warning
    )


async def _build_filtered_responses(
    db: AsyncSession, request: Request, user,
    direction: Optional[str], status: Optional[str],
    payer_id: Optional[str], payee_id: Optional[str],
    deal_id: Optional[str], contract_id: Optional[str],
    search: Optional[str] = None,
    exclude_paid: bool = False,
) -> List[IncomeExpenseEntryResponse]:
    """Build filtered list of income/expense responses (shared by list and count endpoints)."""
    _validate_direction(direction)
    query = select(IncomeExpenseEntry)
    if direction:
        query = query.where(IncomeExpenseEntry.direction == direction)
    if payer_id:
        query = query.where(IncomeExpenseEntry.payer_id == payer_id)
    if payee_id:
        query = query.where(IncomeExpenseEntry.payee_id == payee_id)
    if deal_id:
        query = query.where(IncomeExpenseEntry.deal_id == deal_id)
    if contract_id:
        query = query.where(IncomeExpenseEntry.contract_id == contract_id)
    read_all, read_assigned = await get_section_permissions(db, user.role_id, "income_expense")
    if not read_all:
        if not read_assigned:
            return []
        allowed = await allowed_deal_ids(db, request, user)
        if allowed == []:
            return []
        query = query.where(IncomeExpenseEntry.deal_id.in_(allowed))

    result = await db.execute(query.order_by(IncomeExpenseEntry.plan_date.desc()))
    entries = result.scalars().all()

    company_ids = {e.payer_id for e in entries if e.payer_id} | {e.payee_id for e in entries if e.payee_id}
    deal_ids = {e.deal_id for e in entries if e.deal_id}
    contract_ids_set = {e.contract_id for e in entries if e.contract_id}
    company_map: Dict[str, Company] = {}
    if company_ids:
        company_result = await db.execute(select(Company).where(Company.id.in_(company_ids)))
        company_map = {c.id: c for c in company_result.scalars().all()}
    deal_map: Dict[str, Deal] = {}
    if deal_ids:
        deal_result = await db.execute(select(Deal).where(Deal.id.in_(deal_ids)))
        deal_map = {d.id: d for d in deal_result.scalars().all()}
    contract_map: Dict[str, Contract] = {}
    if contract_ids_set:
        contract_uuid_ids = {cid for cid in (_parse_uuid(value) for value in contract_ids_set) if cid}
        if contract_uuid_ids:
            contract_result = await db.execute(select(Contract).where(Contract.id.in_(contract_uuid_ids)))
            contract_map = {}
            for contract in contract_result.scalars().all():
                contract_map[str(contract.id)] = contract
                contract_map[contract.id.hex] = contract

    history_map: Dict[str, List[PaymentHistoryItem]] = {}
    paid_map: Dict[str, float] = {}
    entry_ids = [e.id for e in entries]
    if entry_ids:
        alloc_result = await db.execute(
            select(TreasuryAllocation, TreasuryTransaction)
            .join(TreasuryTransaction, TreasuryAllocation.transaction_id == TreasuryTransaction.id)
            .where(TreasuryAllocation.income_expense_id.in_(entry_ids))
            .order_by(TreasuryTransaction.transaction_date.asc())
        )
        for allocation, tx in alloc_result.all():
            entry_id = allocation.income_expense_id
            if not entry_id:
                continue
            history_map.setdefault(entry_id, []).append(PaymentHistoryItem(
                transaction_id=str(tx.id),
                transaction_date=tx.transaction_date,
                amount=allocation.amount,
                doc_num=tx.doc_num,
                allocation_id=str(allocation.id),
                category_code=allocation.category_code
            ))
            paid_map[entry_id] = paid_map.get(entry_id, 0.0) + allocation.amount

    responses: List[IncomeExpenseEntryResponse] = []
    for entry in entries:
        paid_amount = paid_map.get(entry.id, 0.0)
        payment_status = _status_from_paid(entry.amount, paid_amount)
        if exclude_paid and payment_status == "paid":
            continue
        if status and payment_status != status:
            continue
        warning = None
        contract = None
        if entry.contract_id:
            contract = contract_map.get(entry.contract_id)
            if not contract:
                parsed_id = _parse_uuid(entry.contract_id)
                if parsed_id:
                    contract = contract_map.get(str(parsed_id)) or contract_map.get(parsed_id.hex)
        if contract and contract.contract_type != "services" and contract.amount and entry.amount > contract.amount:
            warning = "Плановая сумма больше суммы договора"
        responses.append(IncomeExpenseEntryResponse(
            id=str(entry.id),
            direction=entry.direction,
            amount=entry.amount,
            plan_date=entry.plan_date,
            actual_date=entry.actual_date,
            payer_id=entry.payer_id,
            payee_id=entry.payee_id,
            deal_id=entry.deal_id,
            contract_id=entry.contract_id,
            stage_id=entry.stage_id,
            category_code=entry.category_code,
            payer_name=company_map.get(entry.payer_id).name if entry.payer_id in company_map else None,
            payee_name=company_map.get(entry.payee_id).name if entry.payee_id in company_map else None,
            deal_title=deal_map.get(entry.deal_id).title if entry.deal_id in deal_map else None,
            contract_number=contract.contract_number if contract else None,
            payment_status=payment_status,
            paid_amount=paid_amount,
            payments_history=history_map.get(entry.id, []),
            warning=warning
        ))

    # Text search across response fields
    if search:
        tokens = [t.strip().lower() for t in search.split() if t.strip()]
        def _matches(r):
            fields = [
                str(r.amount),
                r.payer_name or '',
                r.payee_name or '',
                r.deal_title or '',
                r.contract_number or '',
                r.category_code or '',
                r.direction or '',
                str(r.plan_date) if r.plan_date else '',
                str(r.actual_date) if r.actual_date else '',
            ]
            folded = [f.lower() for f in fields]
            return all(any(token in f for f in folded) for token in tokens)
        responses = [r for r in responses if _matches(r)]

    return responses


@router.get("/count")
async def count_income_expense_entries(
    request: Request,
    direction: Optional[str] = None,
    status: Optional[str] = None,
    exclude_paid: bool = False,
    payer_id: Optional[str] = None,
    payee_id: Optional[str] = None,
    deal_id: Optional[str] = None,
    contract_id: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    """Get total count of income/expense entries with same filters as list."""
    try:
        responses = await _build_filtered_responses(
            db, request, user, direction, status, payer_id, payee_id, deal_id, contract_id, search, exclude_paid
        )
        return {"count": len(responses)}
    except Exception as e:
        print(f"Error counting income-expense entries: {e}")
        return {"count": 0}


@router.get("/", response_model=List[IncomeExpenseEntryResponse])
async def list_income_expense_entries(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    direction: Optional[str] = None,
    status: Optional[str] = None,
    exclude_paid: bool = False,
    payer_id: Optional[str] = None,
    payee_id: Optional[str] = None,
    deal_id: Optional[str] = None,
    contract_id: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    responses = await _build_filtered_responses(
        db, request, user, direction, status, payer_id, payee_id, deal_id, contract_id, search, exclude_paid
    )
    return responses[skip:skip + limit]


@router.get("/{entry_id}", response_model=IncomeExpenseEntryResponse)
async def get_income_expense_entry(
    entry_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    result = await db.execute(select(IncomeExpenseEntry).where(IncomeExpenseEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    read_all, read_assigned = await get_section_permissions(db, user.role_id, "income_expense")
    if not read_all:
        if not read_assigned:
            raise HTTPException(status_code=404, detail="Entry not found")
        allowed = await allowed_deal_ids(db, request, user)
        if not allowed or not entry.deal_id or str(entry.deal_id) not in set(allowed):
            raise HTTPException(status_code=404, detail="Entry not found")

    return await _build_entry_response(db, entry)


@router.post("/", response_model=IncomeExpenseEntryResponse)
async def create_income_expense_entry(
    payload: IncomeExpenseEntryCreate,
    db: AsyncSession = Depends(get_db)
):
    _validate_direction(payload.direction)
    if payload.deal_id:
        deal = await db.execute(select(Deal).where(Deal.id == payload.deal_id))
        if not deal.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Deal not found")
    if payload.contract_id:
        contract_uuid = _parse_uuid(payload.contract_id)
        if not contract_uuid:
            raise HTTPException(status_code=400, detail="Invalid contract_id")
        contract_result = await db.execute(select(Contract).where(Contract.id == contract_uuid))
        contract = contract_result.scalar_one_or_none()
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        if not payload.deal_id and contract.deal_id:
            payload = payload.copy(update={"deal_id": contract.deal_id})
    entry = IncomeExpenseEntry(**payload.dict())
    db.add(entry)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Invalid company or related reference")
    await db.refresh(entry)

    return await _build_entry_response(db, entry)


@router.patch("/bulk/update")
async def bulk_update_income_expense_entries(
    request: Request,
    payload: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    entry_ids = [
        str(value).strip()
        for value in (payload.get("entry_ids") or [])
        if str(value or "").strip()
    ]
    if not entry_ids:
        raise HTTPException(status_code=400, detail="No entries selected")

    update_data = {}
    for key in ("deal_id", "contract_id", "category_code"):
        if key not in payload:
            continue
        value = payload.get(key)
        if isinstance(value, str):
            value = value.strip() or None
        update_data[key] = value

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    target_deal_id = update_data.get("deal_id")
    if "deal_id" in update_data and target_deal_id:
        deal = await db.execute(select(Deal).where(Deal.id == target_deal_id))
        if not deal.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Deal not found")

    target_contract = None
    if "contract_id" in update_data and update_data["contract_id"]:
        contract_uuid = _parse_uuid(update_data["contract_id"])
        if not contract_uuid:
            raise HTTPException(status_code=400, detail="Invalid contract_id")
        contract_result = await db.execute(select(Contract).where(Contract.id == contract_uuid))
        target_contract = contract_result.scalar_one_or_none()
        if not target_contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        if target_contract.deal_id and not update_data.get("deal_id"):
            update_data["deal_id"] = str(target_contract.deal_id)

    read_all, read_assigned = await get_section_permissions(db, user.role_id, "income_expense")
    allowed = None
    if not read_all:
        if not read_assigned:
            raise HTTPException(status_code=403, detail="No access to income/expense entries")
        allowed = await allowed_deal_ids(db, request, user)
        if allowed == []:
            raise HTTPException(status_code=403, detail="No access to selected entries")
        allowed_set = {str(value) for value in allowed or []}
        if update_data.get("deal_id") and str(update_data["deal_id"]) not in allowed_set:
            raise HTTPException(status_code=403, detail="No access to target deal")

    result = await db.execute(select(IncomeExpenseEntry).where(IncomeExpenseEntry.id.in_(entry_ids)))
    entries = result.scalars().all()
    if not entries:
        raise HTTPException(status_code=404, detail="Entries not found")

    if allowed is not None:
        allowed_set = {str(value) for value in allowed or []}
        for entry in entries:
            if not entry.deal_id or str(entry.deal_id) not in allowed_set:
                raise HTTPException(status_code=403, detail="No access to selected entries")

    for entry in entries:
        for key, value in update_data.items():
            setattr(entry, key, value)

    await db.commit()
    return {"updated": len(entries)}


@router.patch("/{entry_id}", response_model=IncomeExpenseEntryResponse)
async def update_income_expense_entry(
    entry_id: str,
    payload: IncomeExpenseEntryUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    result = await db.execute(select(IncomeExpenseEntry).where(IncomeExpenseEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    await ensure_can_edit_record(db, request, user, "income_expense", entry)

    update_data = payload.dict(exclude_unset=True)
    for key in ("payer_id", "payee_id"):
        if key in update_data and isinstance(update_data[key], str):
            if not update_data[key].strip():
                update_data[key] = None
    if "payer_id" in update_data and update_data["payer_id"]:
        payer = await db.execute(select(Company).where(Company.id == update_data["payer_id"]))
        if not payer.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Payer company not found")
    if "payee_id" in update_data and update_data["payee_id"]:
        payee = await db.execute(select(Company).where(Company.id == update_data["payee_id"]))
        if not payee.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Payee company not found")

    if "direction" in update_data:
        _validate_direction(update_data["direction"])
    if "deal_id" in update_data and update_data["deal_id"]:
        deal = await db.execute(select(Deal).where(Deal.id == update_data["deal_id"]))
        if not deal.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Deal not found")
    if "contract_id" in update_data and update_data["contract_id"]:
        contract_uuid = _parse_uuid(update_data["contract_id"])
        if not contract_uuid:
            raise HTTPException(status_code=400, detail="Invalid contract_id")
        contract_result = await db.execute(select(Contract).where(Contract.id == contract_uuid))
        contract = contract_result.scalar_one_or_none()
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")
        if not update_data.get("deal_id") and contract.deal_id:
            update_data["deal_id"] = contract.deal_id
    for key, value in update_data.items():
        setattr(entry, key, value)

    if entry.contract_id and not entry.deal_id:
        contract = await Contract.get_by_id(db, entry.contract_id)
        if contract and contract.deal_id:
            entry.deal_id = str(contract.deal_id)

    should_sync_amount = "amount" in update_data
    should_sync_date = "plan_date" in update_data and entry.plan_date is not None
    if entry.stage_id and (should_sync_amount or should_sync_date):
        from app.models import Stage, SubcontractorStage

        stage = await Stage.get_by_id(db, str(entry.stage_id))
        if stage and stage.stage_type == "payment" and entry.direction == "income":
            if should_sync_amount:
                stage.planned_cost = entry.amount
            if should_sync_date:
                if stage.date_end is not None:
                    stage.date_end = entry.plan_date
                else:
                    stage.date_start = entry.plan_date
                    stage.date_end = entry.plan_date
        else:
            sub_stage = await SubcontractorStage.get_by_id(db, str(entry.stage_id))
            if sub_stage and sub_stage.stage_type == "payment" and entry.direction == "expense":
                if should_sync_amount:
                    sub_stage.planned_cost = entry.amount
                if should_sync_date:
                    if sub_stage.date_end is not None:
                        sub_stage.date_end = entry.plan_date
                    else:
                        sub_stage.date_start = entry.plan_date
                        sub_stage.date_end = entry.plan_date

    await db.commit()
    await db.refresh(entry)

    return await _build_entry_response(db, entry)


@router.delete("/{entry_id}")
async def delete_income_expense_entry(
    entry_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user=Depends(CurrentUser),
):
    result = await db.execute(select(IncomeExpenseEntry).where(IncomeExpenseEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    await ensure_can_edit_record(db, request, user, "income_expense", entry)

    read_all, read_assigned = await get_section_permissions(db, user.role_id, "income_expense")
    if not read_all:
        if not read_assigned:
            raise HTTPException(status_code=404, detail="Entry not found")
        allowed = await allowed_deal_ids(db, request, user)
        if not allowed or not entry.deal_id or str(entry.deal_id) not in set(allowed):
            raise HTTPException(status_code=404, detail="Entry not found")

    # Keep reverse linkage with deal stages: if a DDS income entry was created
    # from a payment stage, deleting the entry should remove that stage as well.
    if entry.stage_id and entry.direction == "income":
        from app.models import Stage

        stage = await Stage.get_by_id(db, str(entry.stage_id))
        if stage and stage.stage_type == "payment":
            await Stage.delete(db, str(stage.id))

    await db.execute(
        update(Task)
        .where(Task.income_expense_id == entry_id)
        .values(income_expense_id=None)
    )
    await db.execute(
        update(TreasuryTransaction)
        .where(TreasuryTransaction.income_expense_id == entry_id)
        .values(income_expense_id=None)
    )
    await db.execute(delete(TreasuryAllocation).where(TreasuryAllocation.income_expense_id == entry_id))
    await db.delete(entry)
    await db.commit()
    return {"message": "Deleted"}
