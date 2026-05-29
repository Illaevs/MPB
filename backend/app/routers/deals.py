"""
Deals (Projects) API router.
"""
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import and_, delete, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.core.config import settings
from app.database.session import get_db
from app.models import Deal, DealActivity, DealGip, EventLog, Task, User
from app.schemas.deal import DealCreate, DealGipsUpdate, DealResponse, DealUpdate, DealVatUpdate
from app.services.event_log import log_event
from app.services.permissions import allowed_deal_ids, require_section_write, ensure_can_edit_record
from app.services.storage import clean_name, ensure_path, storage_available, upload_file_with_safe_extension
from app.services.upload_security import write_upload_to_tmp

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
    from app.services.our_company import apply_default_our_company
    from app.services.event_outbox import emit_event_safe
    payload = deal.dict()
    # Нормализация пустых FK: фронт шлёт '' для невыбранных селектов,
    # а SQLite на пустую строку выбрасывает FOREIGN KEY constraint failed
    # (ни одна companies.id == ''). Превращаем '' → None для всех FK-полей.
    for _fk in ("customer_id", "general_contractor_id", "our_company_id"):
        if _fk in payload and isinstance(payload[_fk], str) and not payload[_fk].strip():
            payload[_fk] = None
    await apply_default_our_company(db, payload)
    db_deal = await Deal.create(db, **payload)
    if hasattr(db_deal, "id") and db_deal.id:
        db_deal.id = str(db_deal.id)
    # Auto-attach creator → DealGip (восстановление логики из задачи #18).
    # Без проверки роли: любой кто создал сделку — добавляется в список ГИПов.
    # Кейс: помощник ГИПа создаёт проект «от лица» ГИПа — он должен иметь
    # доступ «свои» (read_assigned), иначе сразу теряет видимость записи.
    # Если набор ГИПов потом меняется через PUT /deals/{id}/gips — там
    # явный DELETE + INSERT, эта запись будет либо сохранена, либо
    # сознательно убрана.
    if user and user.id:
        try:
            db.add(DealGip(deal_id=db_deal.id, user_id=str(user.id)))
            await db.flush()
        except Exception as exc:  # defensive — не валим create если DealGip упал
            logger.warning("auto-attach DealGip failed for deal=%s user=%s: %s",
                           db_deal.id, user.id, exc)
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
    # Event bus: пишем в outbox для внешних подписчиков. emit_event_safe
    # глотает любые ошибки сервиса — бизнес-операция не должна падать
    # из-за проблем event-pipeline (всё равно outbox-pattern).
    await emit_event_safe(
        db,
        event_type="deal.after_create",
        entity_type="deal",
        entity_id=str(db_deal.id),
        payload={
            "id": str(db_deal.id),
            "title": db_deal.title,
            "status": db_deal.status,
            "customer_id": str(db_deal.customer_id) if db_deal.customer_id else None,
            "our_company_id": str(db_deal.our_company_id) if db_deal.our_company_id else None,
            "total_contract_value": float(db_deal.total_contract_value or 0),
            "created_by_user_id": str(user.id) if user else None,
        },
    )
    await db.commit()
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


# =====================================================================
# Timeline endpoints (DealActivity) — пользовательские события сделки:
# комментарии, файлы, привязки задач. Аналог /leads/{id}/timeline и
# /leads/{id}/comments/files/tasks. Системные изменения по сделке
# по-прежнему пишутся в EventLog отдельным механизмом log_event().
# =====================================================================

def _deal_activity_user_brief(actor: Optional[User]) -> Optional[Dict[str, Any]]:
    if not actor:
        return None
    return {
        "id": str(actor.id),
        "full_name": actor.full_name,
        "email": actor.email,
        "avatar_url": getattr(actor, "avatar_url", None),
    }


async def _enrich_deal_activity(
    db: AsyncSession,
    act: DealActivity,
    users_cache: Dict[str, Optional[User]],
) -> Dict[str, Any]:
    actor: Optional[User] = None
    if act.actor_user_id:
        if act.actor_user_id in users_cache:
            actor = users_cache[act.actor_user_id]
        else:
            u = (await db.execute(select(User).where(User.id == act.actor_user_id))).scalar_one_or_none()
            users_cache[act.actor_user_id] = u
            actor = u

    payload = act.payload or {}
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            payload = {}

    # task_link → подмешиваем краткую инфу о задаче для UI карточки.
    if act.activity_type == "task_link" and payload.get("task_id"):
        task = (await db.execute(select(Task).where(Task.id == str(payload["task_id"])))).scalar_one_or_none()
        if task:
            payload = {
                **payload,
                "task": {
                    "id": str(task.id),
                    "title": task.title,
                    "status": task.status,
                    "priority": task.priority,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "assigned_to_user_id": str(task.assigned_to_user_id) if task.assigned_to_user_id else None,
                },
            }

    return {
        "id": str(act.id),
        "deal_id": str(act.deal_id),
        "activity_type": act.activity_type,
        "content": act.content,
        "payload": payload,
        "created_at": act.created_at,
        "actor": _deal_activity_user_brief(actor),
    }


@router.get("/{deal_id}/timeline")
async def get_deal_timeline(
    deal_id: str,
    request: Request,
    limit: int = 200,
    offset: int = 0,
    types: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Лента пользовательских событий по сделке.

    Источники:
      • DealActivity-таблица — комментарии/файлы и task_link, добавленные
        из самого composer'а на странице проекта.
      • tasks.deal_id — ВСЕ задачи, привязанные к проекту любым способом
        (через таб-задач, через /api/v1/tasks/, импорт и т.п.); они
        отдают синтетический activity_type='task_link' с тем же payload
        форматом, что и из DealActivity (фронт-рендер не различает).

    Фильтр `types` (comma-separated) применяется к итоговому списку.
    """
    deal = await _ensure_deal_access(deal_id, request=request, db=db, user=user)
    deal_id_str = str(deal.id)
    users_cache: Dict[str, Optional[User]] = {}

    # 1) Реальные DealActivity (без сужения по types — фильтр снизу).
    activities = (await db.execute(
        select(DealActivity)
        .where(DealActivity.deal_id == deal_id_str)
        .order_by(DealActivity.created_at.desc())
    )).scalars().all()
    activity_items: List[Dict[str, Any]] = [
        await _enrich_deal_activity(db, act, users_cache) for act in activities
    ]

    # 2) Pseudo-events из задач: task_link для каждой Task с deal_id =
    # текущий. Чтобы не дублировать со «своими» из composer'а — пропускаем
    # task_id, уже представленный в DealActivity payload.
    linked_task_ids = {
        str(it.get("payload", {}).get("task_id"))
        for it in activity_items
        if it.get("activity_type") == "task_link" and it.get("payload", {}).get("task_id")
    }
    tasks_rows = (await db.execute(
        select(Task).where(Task.deal_id == deal_id_str)
    )).scalars().all()
    for task in tasks_rows:
        if str(task.id) in linked_task_ids:
            continue
        actor: Optional[User] = None
        actor_id = getattr(task, "created_by_user_id", None)
        if actor_id:
            if actor_id in users_cache:
                actor = users_cache[actor_id]
            else:
                actor = (await db.execute(select(User).where(User.id == actor_id))).scalar_one_or_none()
                users_cache[actor_id] = actor
        # id выбираем уникальный — `task-<id>`, чтобы фронт мог отличить
        # синтетический pseudo-event от реальной строки DealActivity (если
        # вдруг где-то это важно для delete-кнопки и т.п.).
        activity_items.append({
            "id": f"task-{task.id}",
            "deal_id": deal_id_str,
            "activity_type": "task_link",
            "content": f"Задача «{task.title}»",
            "payload": {
                "task_id": str(task.id),
                "task": {
                    "id": str(task.id),
                    "title": task.title,
                    "status": task.status,
                    "priority": task.priority,
                    "due_date": task.due_date.isoformat() if task.due_date else None,
                    "assigned_to_user_id": str(task.assigned_to_user_id) if task.assigned_to_user_id else None,
                },
            },
            "created_at": task.created_at,
            "actor": _deal_activity_user_brief(actor),
        })

    # 3) Сортируем итог: новые сверху.
    activity_items.sort(
        key=lambda x: x.get("created_at") or "",
        reverse=True,
    )

    # 4) Фильтр по types и пагинация.
    if types:
        wanted = {t.strip() for t in types.split(",") if t.strip()}
        if wanted:
            activity_items = [i for i in activity_items if i.get("activity_type") in wanted]
    safe_limit = max(1, min(limit, 500))
    safe_offset = max(0, offset)
    return activity_items[safe_offset:safe_offset + safe_limit]


@router.post("/{deal_id}/comments")
async def add_deal_comment(
    deal_id: str,
    request: Request,
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    deal = await _ensure_deal_access(deal_id, request=request, db=db, user=user)
    content = (body or {}).get("content") or ""
    if not content.strip():
        raise HTTPException(status_code=400, detail="Empty comment")
    act = await DealActivity.create(
        db,
        deal_id=str(deal.id),
        activity_type="comment",
        content=content.strip(),
        payload={},
        actor_user_id=str(user.id) if user else None,
    )
    return await _enrich_deal_activity(db, act, {})


@router.post("/{deal_id}/files")
async def upload_deal_file(
    deal_id: str,
    request: Request,
    file: UploadFile = File(...),
    caption: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    deal = await _ensure_deal_access(deal_id, request=request, db=db, user=user)
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage not configured")

    folder = f"deals/{deal.id}/files"
    await ensure_path(folder)
    safe_name = clean_name(file.filename or "file")
    file_path = f"{folder}/{safe_name}"

    tmp_path, size = await write_upload_to_tmp(file)
    try:
        await upload_file_with_safe_extension(file_path, tmp_path)
    finally:
        try:
            import os
            os.unlink(tmp_path)
        except Exception:
            pass

    act = await DealActivity.create(
        db,
        deal_id=str(deal.id),
        activity_type="file",
        content=(caption or "").strip() or safe_name,
        payload={
            "file_name": safe_name,
            "file_path": file_path,
            "file_size": size,
            "content_type": file.content_type,
        },
        actor_user_id=str(user.id) if user else None,
    )
    return await _enrich_deal_activity(db, act, {})


@router.post("/{deal_id}/tasks")
async def create_deal_task(
    deal_id: str,
    request: Request,
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Создать задачу, привязанную к сделке, и добавить запись в timeline.

    Поведение в одну строку с POST /api/v1/tasks/:
      • парсим `due_date` из строки в `date` (SQLite Date не принимает str);
      • выставляем `number` через MAX(number)+1 с retry на UNIQUE-гонке;
      • валидируем FK для assigned_to_user_id.

    Раньше тут принимался raw `dict`, что приводило к двум багам:
    при пустом due_date — задача без номера, при заполненном — 500
    StatementError на SQLite Date type.
    """
    from datetime import date as _date_type, datetime as _datetime_type
    from sqlalchemy import func as sa_func, select as sa_select
    from sqlalchemy.exc import IntegrityError

    deal = await _ensure_deal_access(deal_id, request=request, db=db, user=user)
    title = (body or {}).get("title")
    if not title or not str(title).strip():
        raise HTTPException(status_code=400, detail="Title is required")

    # Конвертация due_date: ISO-строка → date. Пустую строку и None пропускаем.
    due_date_raw = (body or {}).get("due_date")
    due_date_val = None
    if isinstance(due_date_raw, _date_type):
        due_date_val = due_date_raw
    elif isinstance(due_date_raw, str) and due_date_raw.strip():
        try:
            s = due_date_raw.strip()
            # Поддерживаем "2026-06-15" и "2026-06-15T00:00:00[Z]"
            if "T" in s:
                due_date_val = _datetime_type.fromisoformat(s.replace("Z", "+00:00")).date()
            else:
                due_date_val = _date_type.fromisoformat(s)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid due_date: {due_date_raw!r}")

    # Валидация assigned_to_user_id (FK).
    assigned_user_id = (body or {}).get("assigned_to_user_id") or None
    if assigned_user_id:
        u = await User.get_by_id(db, assigned_user_id)
        if not u:
            raise HTTPException(status_code=404, detail="Assigned user not found")

    task_kwargs = {
        "title": str(title).strip(),
        "description": (body or {}).get("description"),
        "status": (body or {}).get("status", "new"),
        "priority": (body or {}).get("priority", "normal"),
        "due_date": due_date_val,
        "assigned_to_user_id": assigned_user_id,
        "deal_id": str(deal.id),
        "created_by_user_id": str(user.id) if user else None,
    }
    # Numbering: тот же подход что в /api/v1/tasks/ create_task.
    task = None
    attempts = max(1, settings.TASK_NUMBER_MAX_RETRIES)
    for attempt in range(attempts):
        next_number_q = await db.execute(
            sa_select(sa_func.coalesce(sa_func.max(Task.number), 0) + 1)
        )
        next_number = int(next_number_q.scalar() or 1)
        try:
            task = await Task.create(db, number=next_number, **task_kwargs)
            break
        except IntegrityError as exc:
            await db.rollback()
            msg = str(getattr(exc, "orig", exc))
            if "tasks.number" in msg and attempt < attempts - 1:
                continue
            raise HTTPException(status_code=500, detail=f"Failed to create task: {msg}")

    act = await DealActivity.create(
        db,
        deal_id=str(deal.id),
        activity_type="task_link",
        content=f"Создана задача «{task.title}»",
        payload={"task_id": str(task.id), "task_number": task.number},
        actor_user_id=str(user.id) if user else None,
    )
    return await _enrich_deal_activity(db, act, {})


@router.delete("/activities/{activity_id}")
async def delete_deal_activity(
    activity_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Удалить пользовательский timeline-элемент. Можно только comment/file
    и только автору (либо суперюзеру)."""
    act = (await db.execute(select(DealActivity).where(DealActivity.id == str(activity_id)))).scalar_one_or_none()
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")
    if act.activity_type not in {"comment", "file"}:
        raise HTTPException(status_code=400, detail="System activities cannot be deleted")
    is_superuser = bool(getattr(user, "is_superuser", False))
    if (
        not is_superuser
        and act.actor_user_id
        and user
        and str(act.actor_user_id) != str(user.id)
    ):
        raise HTTPException(status_code=403, detail="Not author")
    await DealActivity.delete(db, str(activity_id))
    return {"ok": True}


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
    from app.services.event_outbox import emit_event_safe
    existing_deal = await _ensure_deal_access(deal_id, request=request, db=db, user=user)
    await ensure_can_edit_record(db, request, user, "projects", existing_deal)
    filtered_data = deal_update.model_dump(exclude_unset=True)
    if not filtered_data:
        raise HTTPException(status_code=400, detail="Нет данных для обновления")
    # Нормализация пустых FK (см. create_deal): '' → None, иначе FK fail.
    for _fk in ("customer_id", "general_contractor_id", "our_company_id"):
        if _fk in filtered_data and isinstance(filtered_data[_fk], str) and not filtered_data[_fk].strip():
            filtered_data[_fk] = None
    before_snapshot = _deal_snapshot(existing_deal)
    prev_status = existing_deal.status
    deal = await Deal.update(db, deal_id, **filtered_data)
    if not deal:
        raise HTTPException(status_code=404, detail="Проект не найден")
    after_snapshot = _deal_snapshot(deal)
    changes = _deal_changes(before_snapshot, after_snapshot)
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
                "changes": changes,
            },
        )
    except Exception:
        pass
    # Event bus: общее событие обновления.
    await emit_event_safe(
        db,
        event_type="deal.after_update",
        entity_type="deal",
        entity_id=str(deal.id),
        payload={
            "id": str(deal.id),
            "title": deal.title,
            "status": deal.status,
            "changes": changes,
            "actor_user_id": str(user.id) if user else None,
        },
    )
    # Отдельное событие смены статуса — частый кейс для интеграций
    # (Telegram-уведомления, BI-обновление воронки).
    if prev_status and deal.status and prev_status != deal.status:
        await emit_event_safe(
            db,
            event_type="deal.after_status_change",
            entity_type="deal",
            entity_id=str(deal.id),
            payload={
                "id": str(deal.id),
                "title": deal.title,
                "status_from": prev_status,
                "status_to": deal.status,
                "actor_user_id": str(user.id) if user else None,
            },
        )
    await db.commit()
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
    _vat_deal = await _ensure_deal_access(deal_id, request=request, db=db, user=user)
    await ensure_can_edit_record(db, request, user, "projects", _vat_deal)
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
    _del_deal = await _ensure_deal_access(deal_id, request=request, db=db, user=user)
    await ensure_can_edit_record(db, request, user, "projects", _del_deal)
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
    # avatar_url нужен фронту для чипа ГИПа (Overview): без него после
    # сохранения список перезагружается без аватара и он «пропадает».
    return [
        {
            "id": str(u.id),
            "full_name": u.full_name,
            "email": u.email,
            "avatar_url": getattr(u, "avatar_url", None),
        }
        for u in users
    ]


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
    await ensure_can_edit_record(db, request, user, "projects", deal)
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
