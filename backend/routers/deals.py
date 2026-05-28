"""
Deals (Projects) API router.
"""
import json
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import and_, delete, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.core.config import settings
from app.database.session import get_db
from app.models import Deal, DealGip, EventLog, User
from app.schemas.deal import DealCreate, DealGipsUpdate, DealResponse, DealUpdate, DealVatUpdate
from app.services.event_log import log_event
from app.services.permissions import allowed_deal_ids, require_section_write
from app.services.storage import clean_name, ensure_path, storage_available

router = APIRouter()


def _id_filter_values(value: Optional[str]) -> List[str]:
    text = str(value or "").strip()
    if not text:
        return []
    compact = text.replace("-", "").lower()
    values = {text, compact}
    if len(compact) == 32:
        values.add(
            f"{compact[0:8]}-{compact[8:12]}-{compact[12:16]}-"
            f"{compact[16:20]}-{compact[20:32]}"
        )
    return list(values)


def _build_root_paths(entity_id: str, title: str) -> dict:
    safe_title = clean_name(title or f"Entity {entity_id}")
    base = (settings.STORAGE_LOCAL_ROOT or "").rstrip("/")
    return {
        "tz": f"{base}/[#{entity_id}] {safe_title} (ТЗ)",
        "other": f"{base}/[#{entity_id}] {safe_title} (Прочее)",
        "results": f"{base}/[#{entity_id}] {safe_title} (Результаты)",
    }


async def _ensure_deal_access(
    deal_id: str,
    *,
    request: Request,
    db: AsyncSession,
    user: User,
) -> Deal:
    deal = await Deal.get_by_id(db, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Проект не найден")
    allowed = await allowed_deal_ids(db, request, user)
    if allowed is not None and str(deal.id) not in allowed:
        raise HTTPException(status_code=404, detail="Проект не найден")
    return deal


def _parse_event_details(value: Optional[str]) -> Dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    except Exception:
        return {"text": value}


def _format_activity_date(value: Any) -> Optional[str]:
    if not value:
        return None
    try:
        text = str(value).strip()
        if len(text) >= 10:
            yyyy, mm, dd = text[:10].split("-")
            return f"{dd}.{mm}.{yyyy}"
    except Exception:
        return str(value)
    return str(value)


def _pick_first(details: Dict[str, Any], *keys: str) -> Optional[Any]:
    for key in keys:
        value = details.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def _summarize_stage_changes(details: Dict[str, Any]) -> Optional[str]:
    changes = details.get("changes") or {}
    if not isinstance(changes, dict) or not changes:
        return None
    changed_labels = {
        "name": "название",
        "date_start": "дата начала",
        "date_end": "дата окончания",
        "close_date": "дата закрытия",
        "status": "статус",
        "is_closed": "признак закрытия",
        "planned_cost": "стоимость",
        "duration": "длительность",
        "term_type": "тип срока",
        "parent_id": "родительский этап",
    }
    labels = [changed_labels[field] for field in changes.keys() if field in changed_labels]
    if not labels:
        return None
    return "Изменено: " + ", ".join(labels[:4])


def _deal_snapshot(deal: Optional[Deal]) -> Dict[str, Any]:
    if not deal:
        return {}
    return {
        "title": deal.title,
        "obj_name": deal.obj_name,
        "address": deal.address,
        "object_type": deal.object_type,
        "object_area": deal.object_area,
        "customer_id": str(deal.customer_id) if deal.customer_id else None,
        "our_company_id": str(deal.our_company_id) if deal.our_company_id else None,
        "general_contractor_id": str(deal.general_contractor_id) if deal.general_contractor_id else None,
        "status": deal.status,
        "total_contract_value": deal.total_contract_value,
        "total_paid": deal.total_paid,
        "vat_rate": deal.vat_rate,
        "vat_included": deal.vat_included,
    }


def _deal_changes(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    changes: Dict[str, Dict[str, Any]] = {}
    for field, before_value in (before or {}).items():
        after_value = (after or {}).get(field)
        if before_value != after_value:
            changes[field] = {
                "before": before_value,
                "after": after_value,
            }
    return changes


def _summarize_deal_changes(details: Dict[str, Any]) -> Optional[str]:
    changes = details.get("changes") or {}
    if not isinstance(changes, dict) or not changes:
        return None
    changed_labels = {
        "title": "имя проекта",
        "obj_name": "наименование объекта",
        "address": "адрес",
        "object_type": "тип объекта",
        "object_area": "площадь",
        "customer_id": "заказчик",
        "our_company_id": "наша компания",
        "general_contractor_id": "генподрядчик",
        "status": "статус",
        "total_contract_value": "договорная стоимость",
        "total_paid": "оплачено",
        "vat_rate": "ставка НДС",
        "vat_included": "режим НДС",
    }
    labels = [changed_labels[field] for field in changes.keys() if field in changed_labels]
    if not labels:
        return None
    return "Изменено: " + ", ".join(labels[:5])


def _build_activity_item(event: EventLog, actor_names: Dict[str, str]) -> Dict[str, Any]:
    details = _parse_event_details(event.details)
    action = str(event.action or "")
    category = "deal"
    title = "Событие по сделке"
    summary = None
    action_label = action

    if action.startswith("stage."):
        category = "stages"
        stage_name = _pick_first(details, "stage_name", "successor_name") or "Этап"
        if action == "stage.create":
            title = "Этап создан"
            start_date = _format_activity_date(details.get("date_start"))
            end_date = _format_activity_date(details.get("date_end"))
            summary = f"{stage_name} · {start_date} — {end_date}" if start_date and end_date else str(stage_name)
        elif action == "stage.update":
            title = "Этап обновлен"
            closed_date = _pick_first(details, "close_date", "closed_date")
            summary = f"{stage_name} закрыт {(_format_activity_date(closed_date) or closed_date)}" if closed_date else (_summarize_stage_changes(details) or str(stage_name))
        elif action == "stage.delete":
            title = "Этап удален"
            summary = str(stage_name)
        elif action == "stage.dependency":
            title = "Связи этапа изменены"
            predecessors = details.get("predecessor_names") or []
            summary = f"{stage_name}: после {', '.join(predecessors)}" if predecessors else f"Для этапа {stage_name} связи очищены"
        elif action == "stage.products":
            title = "Товары этапа изменены"
            products_count = int(details.get("products_count") or 0)
            summary = f"{stage_name}: назначено товаров {products_count}"
    elif action.startswith("task."):
        category = "tasks"
        task_title = _pick_first(details, "task_title", "title") or "Задача"
        title = {
            "task.assign": "Задача назначена",
            "task.create": "Создана задача",
            "task.update": "Задача обновлена",
        }.get(action, "Событие по задаче")
        summary = str(task_title)
    elif action.startswith("document."):
        category = "documents"
        doc_title = _pick_first(details, "document_title", "title") or "Документ"
        title = {
            "document.create": "Создан документ",
            "document.update": "Документ обновлен",
            "document.sent": "Документ отправлен",
            "document.received": "Документ получен",
        }.get(action, "Событие по документу")
        summary = str(doc_title)
    elif action.startswith("outgoing."):
        category = "letters"
        number = _pick_first(details, "outgoing_number", "outgoing_number_display")
        title = {
            "outgoing.create": "Создано письмо",
            "outgoing.attach": "Добавлены вложения к письму",
            "outgoing.version": "Создана версия письма",
        }.get(action, "Событие по письму")
        summary = f"Исходящее {number}" if number else "Исходящее письмо"
    elif action.startswith("contract."):
        category = "contracts"
        contract_number = _pick_first(details, "contract_number", "number") or "Договор"
        title = {
            "contract.create": "Создан договор",
            "contract.update": "Договор обновлен",
            "contract.link": "Привязка договора изменена",
            "contract.delete": "Договор удален",
            "contract.document.upload": "Загружен документ договора",
        }.get(action, "Событие по договору")
        status = details.get("status")
        summary = f"{contract_number}{f' · {status}' if status else ''}"
    else:
        deal_title = _pick_first(details, "deal_title", "title")
        title = {
            "deal.create": "Сделка создана",
            "deal.update": "Сделка обновлена",
        }.get(action, "Событие по сделке")
        summary = str(deal_title or "Сделка")

    actor_id = str(event.created_by) if event.created_by else None
    return {
        "id": str(event.id),
        "happened_at": event.created_at,
        "category": category,
        "action": action,
        "title": title,
        "summary": summary,
        "actor_id": actor_id,
        "actor_name": actor_names.get(actor_id, "Система") if actor_id else "Система",
        "details": details,
    }


def _build_activity_item_v2(event: EventLog, actor_names: Dict[str, str]) -> Dict[str, Any]:
    details = _parse_event_details(event.details)
    action = str(event.action or "")
    category = "deal"
    title = "Событие по сделке"
    summary = None
    action_label = action

    if action.startswith("stage."):
        category = "stages"
        stage_name = _pick_first(details, "stage_name", "successor_name") or "Этап"
        if action == "stage.create":
            title = "Этап создан"
            action_label = "Создание этапа"
            start_date = _format_activity_date(details.get("date_start"))
            end_date = _format_activity_date(details.get("date_end"))
            summary = f"{stage_name} · {start_date} — {end_date}" if start_date and end_date else str(stage_name)
        elif action == "stage.update":
            title = "Этап обновлен"
            action_label = "Обновление этапа"
            closed_date = _pick_first(details, "close_date", "closed_date")
            summary = (
                f"{stage_name} закрыт {(_format_activity_date(closed_date) or closed_date)}"
                if closed_date
                else (_summarize_stage_changes(details) or str(stage_name))
            )
        elif action == "stage.delete":
            title = "Этап удален"
            action_label = "Удаление этапа"
            summary = str(stage_name)
        elif action == "stage.dependency":
            title = "Связи этапа изменены"
            action_label = "Изменение связей этапа"
            predecessors = details.get("predecessor_names") or []
            summary = f"{stage_name}: после {', '.join(predecessors)}" if predecessors else f"Для этапа {stage_name} связи очищены"
        elif action == "stage.products":
            title = "Товары этапа изменены"
            action_label = "Изменение товаров этапа"
            products_count = int(details.get("products_count") or 0)
            summary = f"{stage_name}: назначено товаров {products_count}"
    elif action.startswith("task."):
        category = "tasks"
        task_title = _pick_first(details, "task_title", "title") or "Задача"
        title = {
            "task.assign": "Задача назначена",
            "task.create": "Создана задача",
            "task.update": "Задача обновлена",
        }.get(action, "Событие по задаче")
        action_label = {
            "task.assign": "Назначение задачи",
            "task.create": "Создание задачи",
            "task.update": "Обновление задачи",
        }.get(action, title)
        summary = str(task_title)
    elif action.startswith("document."):
        category = "documents"
        doc_title = _pick_first(details, "document_title", "title") or "Документ"
        title = {
            "document.create": "Создан документ",
            "document.update": "Документ обновлен",
            "document.sent": "Документ отправлен",
            "document.received": "Документ получен",
        }.get(action, "Событие по документу")
        action_label = title
        summary = str(doc_title)
    elif action.startswith("outgoing."):
        category = "letters"
        number = _pick_first(details, "outgoing_number_display", "outgoing_number")
        title = {
            "outgoing.create": "Создано письмо",
            "outgoing.attach": "Добавлены вложения к письму",
            "outgoing.version": "Создана версия письма",
        }.get(action, "Событие по письму")
        action_label = title
        summary = f"Исходящее {number}" if number else "Исходящее письмо"
    elif action.startswith("contract."):
        category = "contracts"
        contract_number = _pick_first(details, "contract_number", "number") or "Договор"
        title = {
            "contract.create": "Создан договор",
            "contract.update": "Договор обновлен",
            "contract.link": "Привязка договора изменена",
            "contract.delete": "Договор удален",
            "contract.document.upload": "Загружен документ договора",
        }.get(action, "Событие по договору")
        action_label = title
        status = details.get("status")
        summary = f"{contract_number}{f' · {status}' if status else ''}"
    else:
        deal_title = _pick_first(details, "deal_title", "title")
        title = {
            "deal.create": "Сделка создана",
            "deal.update": "Сделка обновлена",
        }.get(action, "Событие по сделке")
        action_label = title
        if action == "deal.update":
            summary = _summarize_deal_changes(details) or str(deal_title or "Сделка")
        else:
            summary = str(deal_title or "Сделка")

    actor_id = str(event.created_by) if event.created_by else None
    return {
        "id": str(event.id),
        "happened_at": event.created_at,
        "category": category,
        "action": action,
        "action_label": action_label,
        "title": title,
        "summary": summary,
        "actor_id": actor_id,
        "actor_name": actor_names.get(actor_id, "Система") if actor_id else "Система",
        "details": details,
    }


@router.get("/", response_model=List[DealResponse])
async def get_deals(
    request: Request,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    min_contract_value: Optional[float] = None,
    max_contract_value: Optional[float] = None,
    search: Optional[str] = None,
    customer_id: Optional[str] = None,
    our_company_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    try:
        allowed = await allowed_deal_ids(db, request, user)
        if allowed == []:
            return []
        if allowed is not None:
            query = select(Deal)
            filters = []
            if status:
                filters.append(Deal.status == status)
            customer_values = _id_filter_values(customer_id)
            if customer_values:
                filters.append(Deal.customer_id.in_(customer_values))
            our_company_values = _id_filter_values(our_company_id)
            if our_company_values:
                filters.append(Deal.our_company_id.in_(our_company_values))
            if min_contract_value is not None:
                filters.append(Deal.total_contract_value >= min_contract_value)
            if max_contract_value is not None:
                filters.append(Deal.total_contract_value <= max_contract_value)
            if search and search.strip():
                search_term = f"%{search.strip()}%"
                filters.append(
                    or_(
                        Deal.title.ilike(search_term),
                        Deal.obj_name.ilike(search_term),
                        Deal.address.ilike(search_term),
                    )
                )
            filters.append(Deal.id.in_(allowed))
            if filters:
                query = query.where(and_(*filters))
            query = query.offset(skip).limit(limit)
            result = await db.execute(query)
            deals = result.scalars().all()
        else:
            deals = await Deal.get_filtered(
                db,
                skip=skip,
                limit=limit,
                status=status,
                min_contract_value=min_contract_value,
                max_contract_value=max_contract_value,
                search=search,
                customer_id=customer_id,
                our_company_id=our_company_id,
            )
        for deal in deals:
            if hasattr(deal, "id") and deal.id:
                deal.id = str(deal.id)
        return deals
    except Exception:
        return []


@router.post("/", response_model=DealResponse)
async def create_deal(
    deal: DealCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    _=Depends(require_section_write("projects")),
):
    db_deal = await Deal.create(db, **deal.dict())
    if hasattr(db_deal, "id") and db_deal.id:
        db_deal.id = str(db_deal.id)
    try:
        await log_event(
            db,
            entity_type="deal",
            entity_id=str(db_deal.id),
            action="deal.create",
            created_by=str(user.id),
            details={
                "deal_id": str(db_deal.id),
                "deal_title": db_deal.title,
            },
        )
    except Exception:
        pass
    return db_deal


@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    return await _ensure_deal_access(deal_id, request=request, db=db, user=user)


@router.get("/{deal_id}/activity")
async def get_deal_activity(
    deal_id: str,
    request: Request,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    deal = await _ensure_deal_access(deal_id, request=request, db=db, user=user)
    deal_id_str = str(deal.id)
    safe_limit = max(1, min(limit, 100))
    scan_limit = max(200, min(500, skip + safe_limit + 150))
    details_pattern = f'%\"deal_id\": \"{deal_id_str}\"%'

    result = await db.execute(
        select(EventLog)
        .where(
            or_(
                and_(EventLog.entity_type == "deal", EventLog.entity_id == deal_id_str),
                EventLog.details.like(details_pattern),
            )
        )
        .order_by(desc(EventLog.created_at))
        .limit(scan_limit)
    )
    events = result.scalars().all()

    user_ids = sorted({str(item.created_by) for item in events if getattr(item, "created_by", None)})
    actor_names: Dict[str, str] = {}
    if user_ids:
        users_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        actor_names = {
            str(item.id): (item.full_name or item.email or str(item.id))
            for item in users_result.scalars().all()
        }

    normalized_items = [_build_activity_item_v2(event, actor_names) for event in events]
    if category:
        normalized_items = [item for item in normalized_items if item["category"] == category]

    return {
        "items": normalized_items[skip:skip + safe_limit],
        "has_more": len(normalized_items) > skip + safe_limit,
        "total": len(normalized_items),
    }


@router.get("/{deal_id}/folders")
async def get_deal_folders(
    deal_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    deal = await _ensure_deal_access(deal_id, request=request, db=db, user=user)
    paths = _build_root_paths(str(deal.id), deal.title)
    if storage_available():
        try:
            await ensure_path(paths["tz"])
            await ensure_path(paths["other"])
            await ensure_path(paths["results"])
        except Exception:
            pass
    return paths


@router.put("/{deal_id}", response_model=DealResponse)
async def update_deal(
    deal_id: str,
    deal_update: DealUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    _=Depends(require_section_write("projects")),
):
    existing_deal = await _ensure_deal_access(deal_id, request=request, db=db, user=user)
    filtered_data = deal_update.model_dump(exclude_unset=True)
    if not filtered_data:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")
    before_snapshot = _deal_snapshot(existing_deal)
    deal = await Deal.update(db, deal_id, **filtered_data)
    if not deal:
        raise HTTPException(status_code=404, detail="Проект не найден")
    try:
        await log_event(
            db,
            entity_type="deal",
            entity_id=str(deal.id),
            action="deal.update",
            created_by=str(user.id),
            details={
                "deal_id": str(deal.id),
                "deal_title": deal.title,
                "changes": _deal_changes(before_snapshot, _deal_snapshot(deal)),
            },
        )
    except Exception:
        pass
    return deal


@router.patch("/{deal_id}/vat")
async def update_deal_vat(
    deal_id: str,
    payload: DealVatUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    _=Depends(require_section_write("projects")),
):
    await _ensure_deal_access(deal_id, request=request, db=db, user=user)
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Нет данных для обновления НДС")
    deal = await Deal.update(db, deal_id, **update_data)
    if not deal:
        raise HTTPException(status_code=404, detail="Проект не найден")
    return {"message": "Настройки НДС обновлены"}


@router.delete("/{deal_id}")
async def delete_deal(
    deal_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    _=Depends(require_section_write("projects")),
):
    await _ensure_deal_access(deal_id, request=request, db=db, user=user)
    success = await Deal.delete(db, deal_id)
    if not success:
        raise HTTPException(status_code=404, detail="Проект не найден")
    return {"message": "Проект удален"}


@router.get("/{deal_id}/gips")
async def get_deal_gips(
    deal_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    deal = await _ensure_deal_access(deal_id, request=request, db=db, user=user)
    result = await db.execute(select(DealGip).where(DealGip.deal_id == deal.id))
    links = result.scalars().all()
    user_ids = [str(link.user_id) for link in links]
    users = []
    if user_ids:
        user_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        users = user_result.scalars().all()
    return [{"id": str(u.id), "full_name": u.full_name, "email": u.email} for u in users]


@router.put("/{deal_id}/gips")
async def set_deal_gips(
    deal_id: str,
    payload: DealGipsUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    _=Depends(require_section_write("projects")),
):
    deal = await _ensure_deal_access(deal_id, request=request, db=db, user=user)
    user_ids = payload.user_ids or []
    if user_ids:
        user_result = await db.execute(select(User).where(User.id.in_(user_ids)))
        users = user_result.scalars().all()
        if len(users) != len(user_ids):
            raise HTTPException(status_code=400, detail="В payload передан неверный user_id")
    await db.execute(delete(DealGip).where(DealGip.deal_id == deal.id))
    for user_id in user_ids:
        db.add(DealGip(deal_id=deal.id, user_id=user_id))
    await db.commit()
    return {"message": "ГИПы проекта обновлены"}
