"""
Notification rules engine and scheduled jobs.
"""
import logging
import json
from datetime import datetime, timedelta, time
from typing import Any, Dict, Iterable, List, Optional

from zoneinfo import ZoneInfo

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    NotificationRule,
    NotificationSubscription,
    NotificationPreference,
    NotificationJob,
    Notification,
    EventLog,
    DealGip,
    Deal,
    RolePermission,
    Task,
    OutgoingDocument,
    Document,
    UploadJob,
    TelegramConnection,
    User,
)
from app.services.data_health import get_health_issues, refresh_all_health_issues
from app.services.data_health_report import build_data_health_report_pdf
from app.services.notifications import create_notification
from app.services.telegram_bot import send_telegram_document


logger = logging.getLogger(__name__)


DEFAULT_RULES: List[Dict[str, Any]] = [
    {
        "name": "Назначение задачи",
        "trigger": "task.assign",
        "entity_type": "task",
        "priority": "info",
        "audience_type": "assigned_user",
        "quiet_policy": "respect",
        "throttle_minutes": 10,
        "title_template": "Назначена новая задача",
        "message_template": "Задача: {task_title}",
        "action_url_template": "/tasks?task_id={task_id}",
        "deliver_telegram": True,
    },
    {
        "name": "Просроченная задача",
        "trigger": "task.overdue",
        "entity_type": "task",
        "priority": "warning",
        "audience_type": "assigned_user",
        "quiet_policy": "respect",
        "throttle_minutes": 120,
        "title_template": "Задача просрочена",
        "message_template": "{task_title} просрочена на {overdue_days} дней",
        "action_url_template": "/tasks?task_id={task_id}",
        "deliver_telegram": True,
    },
    {
        "name": "Обновление сделки",
        "trigger": "deal.update",
        "entity_type": "deal",
        "priority": "info",
        "audience_type": "deal_gip",
        "require_subscription": False,
        "quiet_policy": "respect",
        "throttle_minutes": 30,
        "title_template": "Сделка обновлена",
        "message_template": "Сделка: {deal_title}",
        "action_url_template": "/projects/{deal_id}",
    },
    {
        "name": "Новая сделка",
        "trigger": "deal.create",
        "entity_type": "deal",
        "priority": "info",
        "audience_type": "deal_gip",
        "quiet_policy": "respect",
        "throttle_minutes": 30,
        "title_template": "Создана новая сделка",
        "message_template": "Сделка: {deal_title}",
        "action_url_template": "/projects/{deal_id}",
    },
    {
        "name": "Создан исходящий документ",
        "trigger": "outgoing.create",
        "entity_type": "outgoing",
        "priority": "info",
        "audience_type": "deal_gip",
        "quiet_policy": "respect",
        "throttle_minutes": 30,
        "title_template": "Создан исходящий документ",
        "message_template": "Номер: {outgoing_number}",
        "action_url_template": "/outgoing-registry",
    },
    {
        "name": "Обновление исходящего документа",
        "trigger": "outgoing.version",
        "entity_type": "outgoing",
        "priority": "info",
        "audience_type": "deal_gip",
        "quiet_policy": "respect",
        "throttle_minutes": 30,
        "title_template": "Исходящий документ обновлен",
        "message_template": "Номер: {outgoing_number}",
        "action_url_template": "/outgoing-registry",
    },
    {
        "name": "Отправка документа",
        "trigger": "document.sent",
        "entity_type": "document",
        "priority": "info",
        "audience_type": "deal_gip",
        "quiet_policy": "respect",
        "throttle_minutes": 30,
        "title_template": "Документ отправлен",
        "message_template": "{document_title}",
        "action_url_template": "/document-registry",
    },
    {
        "name": "Получение документа",
        "trigger": "document.received",
        "entity_type": "document",
        "priority": "success",
        "audience_type": "deal_gip",
        "quiet_policy": "respect",
        "throttle_minutes": 30,
        "title_template": "Документ получен",
        "message_template": "{document_title}",
        "action_url_template": "/document-registry",
    },
    {
        "name": "Просроченный документ",
        "trigger": "document.overdue",
        "entity_type": "document",
        "priority": "warning",
        "audience_type": "deal_gip",
        "quiet_policy": "respect",
        "throttle_minutes": 120,
        "title_template": "Документ просрочен",
        "message_template": "{document_title} просрочен на {overdue_days} дней",
        "action_url_template": "/document-registry",
        "deliver_telegram": True,
    },
    {
        "name": "Согласование результатов работ",
        "trigger": "result_review.update",
        "entity_type": "deal",
        "priority": "info",
        "audience_type": "deal_gip",
        "quiet_policy": "respect",
        "throttle_minutes": 30,
        "title_template": "Согласование РР обновлено",
        "message_template": "Изменен статус согласования результата работ",
        "action_url_template": "/work-results-reviews",
    },
    {
        "name": "Ошибка загрузки",
        "trigger": "upload.error",
        "entity_type": "upload",
        "priority": "error",
        "audience_type": "creator_user",
        "quiet_policy": "ignore",
        "throttle_minutes": 5,
        "title_template": "Ошибка загрузки",
        "message_template": "{error_message}",
        "action_url_template": "/",
    },
]


class _SafeDict(dict):
    def __missing__(self, key):
        return ""


async def ensure_default_rules(db: AsyncSession) -> None:
    result = await db.execute(select(func.count(NotificationRule.id)))
    count = int(result.scalar() or 0)
    if count > 0:
        return
    for rule in DEFAULT_RULES:
        db.add(NotificationRule(**rule))
    await db.commit()


async def _get_job(db: AsyncSession, name: str) -> NotificationJob:
    result = await db.execute(select(NotificationJob).where(NotificationJob.name == name))
    job = result.scalar_one_or_none()
    if job:
        return job
    job = NotificationJob(name=name)
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


def _parse_details(value: Optional[str]) -> Dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {"details": value}


def _render_template(template: Optional[str], context: Dict[str, Any]) -> str:
    if not template:
        return ""
    try:
        return template.format_map(_SafeDict(context))
    except Exception:
        return template


def _time_from_str(value: str, fallback: time) -> time:
    try:
        parts = value.split(":")
        return time(hour=int(parts[0]), minute=int(parts[1]))
    except Exception:
        return fallback


def _is_quiet(now_local: datetime, start_str: str, end_str: str) -> bool:
    start = _time_from_str(start_str, time(22, 0))
    end = _time_from_str(end_str, time(8, 0))
    if start < end:
        return start <= now_local.time() < end
    return now_local.time() >= start or now_local.time() < end


def _next_quiet_end(now_local: datetime, end_str: str) -> datetime:
    end = _time_from_str(end_str, time(8, 0))
    candidate = now_local.replace(hour=end.hour, minute=end.minute, second=0, microsecond=0)
    if candidate <= now_local:
        candidate += timedelta(days=1)
    return candidate


async def _get_preference(db: AsyncSession, user_id: str) -> NotificationPreference:
    result = await db.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == str(user_id))
    )
    pref = result.scalar_one_or_none()
    if pref:
        return pref
    pref = NotificationPreference(user_id=str(user_id))
    db.add(pref)
    await db.commit()
    await db.refresh(pref)
    return pref


async def _resolve_audience(
    db: AsyncSession,
    rule: NotificationRule,
    payload: Dict[str, Any],
    event_created_by: Optional[str],
) -> List[str]:
    audience = rule.audience_type or "assigned_user"
    value = rule.audience_value
    if audience == "assigned_user":
        user_id = payload.get("assigned_to_user_id") or payload.get("assigned_user_id")
        return [str(user_id)] if user_id else []
    if audience == "creator_user":
        user_id = payload.get("created_by") or event_created_by
        return [str(user_id)] if user_id else []
    if audience == "deal_gip":
        deal_id = payload.get("deal_id")
        if not deal_id:
            return []
        result = await db.execute(select(DealGip.user_id).where(DealGip.deal_id == str(deal_id)))
        return [str(item[0]) for item in result.all()]
    if audience == "role":
        if not value:
            return []
        result = await db.execute(select(User.id).where(User.role_id == str(value)))
        return [str(item[0]) for item in result.all()]
    if audience == "user":
        return [str(value)] if value else []
    if audience == "all":
        result = await db.execute(select(User.id).where(User.is_active.is_(True)))
        return [str(item[0]) for item in result.all()]
    if audience == "subscribers":
        entity_type = payload.get("entity_type")
        entity_id = payload.get("entity_id")
        if not (entity_type and entity_id):
            return []
        result = await db.execute(
            select(NotificationSubscription.user_id).where(
                NotificationSubscription.entity_type == str(entity_type),
                NotificationSubscription.entity_id == str(entity_id),
                NotificationSubscription.is_muted.is_(False),
            )
        )
        return [str(item[0]) for item in result.all()]
    return []


def _match_conditions(payload: Dict[str, Any], conditions: Optional[Dict[str, Any]]) -> bool:
    if not conditions:
        return True
    for key, value in conditions.items():
        if key == "status_in":
            if payload.get("status") not in (value or []):
                return False
        elif key == "status_not_in":
            if payload.get("status") in (value or []):
                return False
        elif key == "doc_types":
            if payload.get("doc_type") not in (value or []):
                return False
        elif key == "overdue_days":
            if int(payload.get("overdue_days", 0)) < int(value or 0):
                return False
        else:
            if payload.get(key) != value:
                return False
    return True


async def _should_notify(
    db: AsyncSession,
    rule: NotificationRule,
    user_id: str,
    payload: Dict[str, Any],
    source_event_id: Optional[str],
) -> bool:
    if await Notification.exists_for_event(db, user_id, rule.id, source_event_id):
        return False
    throttle = int(rule.throttle_minutes or 0)
    if throttle > 0:
        since = datetime.utcnow() - timedelta(minutes=throttle)
        has_recent = await Notification.find_recent(
            db,
            user_id,
            rule.id,
            payload.get("entity_type"),
            payload.get("entity_id"),
            since,
        )
        if has_recent:
            return False
    if rule.require_subscription:
        entity_type = payload.get("entity_type")
        entity_id = payload.get("entity_id")
        if not (entity_type and entity_id):
            return False
        result = await db.execute(
            select(NotificationSubscription.id).where(
                NotificationSubscription.user_id == str(user_id),
                NotificationSubscription.entity_type == str(entity_type),
                NotificationSubscription.entity_id == str(entity_id),
                NotificationSubscription.is_muted.is_(False),
            )
        )
        if result.scalar_one_or_none() is None:
            return False
    return True


async def _build_context(
    db: AsyncSession,
    event: Dict[str, Any],
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    context = dict(payload)
    context.setdefault("entity_type", event.get("entity_type"))
    context.setdefault("entity_id", event.get("entity_id"))
    context.setdefault("action", event.get("action"))

    actor_id = event.get("created_by")
    if actor_id:
        user = await User.get_by_id(db, actor_id)
        if user:
            context["actor_name"] = user.full_name

    entity_type = event.get("entity_type")
    entity_id = event.get("entity_id")
    if entity_type == "deal" and entity_id:
        deal = await Deal.get_by_id(db, entity_id)
        if deal:
            context["deal_id"] = str(deal.id)
            context["deal_title"] = deal.title
    if entity_type == "task" and entity_id:
        task = await Task.get_by_id(db, entity_id)
        if task:
            context["task_id"] = str(task.id)
            context["task_title"] = task.title
            context["assigned_to_user_id"] = str(task.assigned_to_user_id) if task.assigned_to_user_id else None
            context["deal_id"] = str(task.deal_id) if task.deal_id else None
    if entity_type == "outgoing" and entity_id:
        outgoing = await OutgoingDocument.get_by_id(db, entity_id)
        if outgoing:
            context["outgoing_number"] = outgoing.outgoing_number
            context["deal_id"] = str(outgoing.deal_id) if outgoing.deal_id else None
    if entity_type == "document" and entity_id:
        result = await db.execute(select(Document).where(Document.id == str(entity_id)))
        doc = result.scalar_one_or_none()
        if doc:
            context["document_title"] = doc.title
            context["doc_type"] = doc.doc_type
            context["status"] = doc.status
            context["deal_id"] = doc.project_id
    if entity_type == "upload" and entity_id:
        result = await db.execute(select(UploadJob).where(UploadJob.id == str(entity_id)))
        job = result.scalar_one_or_none()
        if job:
            context["file_name"] = job.file_name
            context["error_message"] = job.error_message
            context["module"] = job.module
    return context


async def process_event(db: AsyncSession, event: EventLog) -> None:
    await ensure_default_rules(db)
    rules = await NotificationRule.get_active_for_trigger(db, event.action)
    if not rules:
        return

    payload = _parse_details(event.details)
    payload.setdefault("entity_type", event.entity_type)
    payload.setdefault("entity_id", event.entity_id)
    payload.setdefault("created_by", event.created_by)
    payload.setdefault("action", event.action)
    context = await _build_context(
        db,
        {
            "entity_type": event.entity_type,
            "entity_id": event.entity_id,
            "action": event.action,
            "created_by": event.created_by,
        },
        payload,
    )

    for rule in rules:
        if rule.entity_type and rule.entity_type != payload.get("entity_type"):
            continue
        if not _match_conditions(payload, rule.conditions or {}):
            continue
        recipients = await _resolve_audience(db, rule, payload, event.created_by)
        if not recipients:
            continue
        for user_id in recipients:
            pref = await _get_preference(db, user_id)
            if not (pref.deliver_in_app or pref.deliver_telegram):
                continue
            if not await _should_notify(db, rule, user_id, payload, str(event.id)):
                continue
            deliver_at = None
            if rule.quiet_policy != "ignore":
                try:
                    zone = ZoneInfo(pref.timezone or "UTC")
                except Exception:
                    zone = ZoneInfo("UTC")
                now_local = datetime.now(tz=zone)
                if _is_quiet(now_local, pref.quiet_hours_start, pref.quiet_hours_end):
                    deliver_at = _next_quiet_end(now_local, pref.quiet_hours_end).astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
            title = _render_template(rule.title_template, context) or rule.name
            message = _render_template(rule.message_template, context)
            action_url = _render_template(rule.action_url_template, context)
            await create_notification(
                db,
                user_id=str(user_id),
                title=title,
                message=message,
                type=rule.priority or "info",
                priority=rule.priority or "info",
                entity_type=payload.get("entity_type"),
                entity_id=payload.get("entity_id"),
                action_url=action_url,
                rule_id=str(rule.id),
                source_event_id=str(event.id),
                deliver_at=deliver_at,
            )


async def process_event_logs(db: AsyncSession) -> None:
    job = await _get_job(db, "event_logs")
    since = job.last_run_at or (datetime.utcnow() - timedelta(days=1))
    result = await db.execute(
        select(EventLog)
        .where(EventLog.created_at >= since)
        .order_by(EventLog.created_at.asc())
    )
    events = result.scalars().all()
    last_seen = job.last_run_at
    for event in events:
        await process_event(db, event)
        last_seen = event.created_at
    if last_seen:
        job.last_run_at = last_seen
        await db.commit()


async def process_task_overdue(db: AsyncSession) -> None:
    await ensure_default_rules(db)
    today = datetime.utcnow().date()
    result = await db.execute(
        select(Task).where(
            Task.due_date.is_not(None),
            Task.status != "completed",
            Task.due_date < today,
        )
    )
    tasks = result.scalars().all()
    for task in tasks:
        overdue_days = (today - task.due_date).days if task.due_date else 0
        payload = {
            "entity_type": "task",
            "entity_id": str(task.id),
            "task_id": str(task.id),
            "task_title": task.title,
            "assigned_to_user_id": str(task.assigned_to_user_id) if task.assigned_to_user_id else None,
            "deal_id": str(task.deal_id) if task.deal_id else None,
            "overdue_days": overdue_days,
        }
        rules = await NotificationRule.get_active_for_trigger(db, "task.overdue")
        for rule in rules:
            if not _match_conditions(payload, rule.conditions or {}):
                continue
            recipients = await _resolve_audience(db, rule, payload, None)
            if not recipients:
                continue
            for user_id in recipients:
                pref = await _get_preference(db, user_id)
                if not (pref.deliver_in_app or pref.deliver_telegram):
                    continue
                source_event_id = f"task.overdue:{task.id}:{today.isoformat()}"
                if not await _should_notify(db, rule, user_id, payload, source_event_id):
                    continue
                deliver_at = None
                if rule.quiet_policy != "ignore":
                    try:
                        zone = ZoneInfo(pref.timezone or "UTC")
                    except Exception:
                        zone = ZoneInfo("UTC")
                    now_local = datetime.now(tz=zone)
                    if _is_quiet(now_local, pref.quiet_hours_start, pref.quiet_hours_end):
                        deliver_at = _next_quiet_end(now_local, pref.quiet_hours_end).astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
                title = _render_template(rule.title_template, payload) or "Задача просрочена"
                message = _render_template(rule.message_template, payload)
                action_url = _render_template(rule.action_url_template, payload) or f"/tasks?task_id={task.id}"
                await create_notification(
                    db,
                    user_id=str(user_id),
                    title=title,
                    message=message,
                    type=rule.priority or "warning",
                    priority=rule.priority or "warning",
                    entity_type="task",
                    entity_id=str(task.id),
                    action_url=action_url,
                    rule_id=str(rule.id),
                    source_event_id=source_event_id,
                    deliver_at=deliver_at,
                )


async def process_document_overdue(db: AsyncSession) -> None:
    await ensure_default_rules(db)
    today = datetime.utcnow().date()
    result = await db.execute(
        select(Document).where(
            Document.document_date.is_not(None),
            Document.status.notin_(["received", "archive"]),
        )
    )
    docs = result.scalars().all()
    for doc in docs:
        overdue_days = (today - doc.document_date).days if doc.document_date else 0
        if overdue_days <= 0:
            continue
        payload = {
            "entity_type": "document",
            "entity_id": str(doc.id),
            "document_title": doc.title,
            "doc_type": doc.doc_type,
            "status": doc.status,
            "deal_id": doc.project_id,
            "overdue_days": overdue_days,
        }
        rules = await NotificationRule.get_active_for_trigger(db, "document.overdue")
        for rule in rules:
            if not _match_conditions(payload, rule.conditions or {}):
                continue
            recipients = await _resolve_audience(db, rule, payload, None)
            if not recipients:
                continue
            for user_id in recipients:
                pref = await _get_preference(db, user_id)
                if not (pref.deliver_in_app or pref.deliver_telegram):
                    continue
                source_event_id = f"document.overdue:{doc.id}:{today.isoformat()}"
                if not await _should_notify(db, rule, user_id, payload, source_event_id):
                    continue
                deliver_at = None
                if rule.quiet_policy != "ignore":
                    try:
                        zone = ZoneInfo(pref.timezone or "UTC")
                    except Exception:
                        zone = ZoneInfo("UTC")
                    now_local = datetime.now(tz=zone)
                    if _is_quiet(now_local, pref.quiet_hours_start, pref.quiet_hours_end):
                        deliver_at = _next_quiet_end(now_local, pref.quiet_hours_end).astimezone(ZoneInfo("UTC")).replace(tzinfo=None)
                title = _render_template(rule.title_template, payload) or "Документ просрочен"
                message = _render_template(rule.message_template, payload)
                action_url = _render_template(rule.action_url_template, payload) or "/document-registry"
                await create_notification(
                    db,
                    user_id=str(user_id),
                    title=title,
                    message=message,
                    type=rule.priority or "warning",
                    priority=rule.priority or "warning",
                    entity_type="document",
                    entity_id=str(doc.id),
                    action_url=action_url,
                    rule_id=str(rule.id),
                    source_event_id=source_event_id,
                    deliver_at=deliver_at,
                )


async def process_digests(db: AsyncSession) -> None:
    now_utc = datetime.utcnow()
    result = await db.execute(select(User).where(User.is_active.is_(True)))
    users = result.scalars().all()
    for user in users:
        pref = await _get_preference(db, user.id)
        if not pref.digest_enabled:
            continue
        try:
            zone = ZoneInfo(pref.timezone or "UTC")
        except Exception:
            zone = ZoneInfo("UTC")
        now_local = datetime.now(tz=zone)
        digest_time = _time_from_str(pref.digest_time, time(9, 0))
        if now_local.time() < digest_time:
            continue
        last_sent = pref.digest_last_sent_at
        if last_sent and last_sent.date() == now_local.date():
            continue
        result = await db.execute(
            select(func.count(Notification.id)).where(
                Notification.user_id == str(user.id),
                Notification.created_at >= (now_utc - timedelta(days=1)),
            )
        )
        total = int(result.scalar() or 0)
        if total <= 0:
            pref.digest_last_sent_at = now_utc
            await db.commit()
            continue
        await create_notification(
            db,
            user_id=str(user.id),
            title="Ежедневная сводка",
            message=f"У вас {total} уведомлений за последние 24 часа.",
            type="info",
            priority="info",
            entity_type=None,
            entity_id=None,
            action_url="/",
            rule_id=None,
            source_event_id=f"digest:{user.id}:{now_local.date().isoformat()}",
            deliver_at=None,
        )
        pref.digest_last_sent_at = now_utc
        await db.commit()


async def _ensure_data_health_daily_rule(db: AsyncSession) -> NotificationRule:
    trigger = "data_health.daily"
    result = await db.execute(select(NotificationRule).where(NotificationRule.trigger == trigger))
    rule = result.scalar_one_or_none()
    if rule:
        if not rule.deliver_telegram:
            rule.deliver_telegram = True
        if not rule.deliver_in_app:
            rule.deliver_in_app = True
        if not rule.is_active:
            rule.is_active = True
        await db.commit()
        await db.refresh(rule)
        return rule

    rule = NotificationRule(
        name="Ежедневная сводка контроля данных",
        trigger=trigger,
        entity_type="data_health",
        priority="warning",
        audience_type="all",
        quiet_policy="respect",
        deliver_in_app=True,
        deliver_telegram=True,
        throttle_minutes=0,
        title_template="Ежедневный health-check данных",
        message_template="{message}",
        action_url_template="/data-health",
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


async def _data_health_summary_recipients(db: AsyncSession) -> List[User]:
    result = await db.execute(
        select(User)
        .join(RolePermission, RolePermission.role_id == User.role_id)
        .where(
            User.is_active.is_(True),
            RolePermission.section == "projects",
            (RolePermission.read_all.is_(True)) | (RolePermission.read_assigned.is_(True)),
        )
        .distinct()
    )
    return result.scalars().all()


async def process_data_health_daily_summary(db: AsyncSession) -> None:
    zone = ZoneInfo("Europe/Moscow")
    now_local = datetime.now(tz=zone)
    if now_local.time() < time(9, 0):
        return

    job = await _get_job(db, "data_health_daily")
    if job.last_run_at:
        last_run = job.last_run_at
        if last_run.tzinfo is None:
            last_run = last_run.replace(tzinfo=ZoneInfo("UTC"))
        if last_run.astimezone(zone).date() == now_local.date():
            return

    await refresh_all_health_issues(db)
    data = await get_health_issues(db, status="active", offset=0, limit=5)
    summary = data.get("summary") or {}
    total = int(summary.get("total") or 0)
    errors = int(summary.get("errors") or 0)
    warnings = int(summary.get("warnings") or 0)
    priority = "warning" if total else "info"
    top_items = data.get("items") or []
    top_lines = []
    for issue in top_items[:5]:
        deal_title = issue.get("deal_title")
        suffix = f" ({deal_title})" if deal_title else ""
        top_lines.append(f"- {issue.get('title')}{suffix}")
    details = "\n".join(top_lines)
    message = f"Активных проблем: {total}. Ошибок: {errors}. Предупреждений: {warnings}."
    if details:
        message = f"{message}\n\nПервые проблемы:\n{details}"

    rule = await _ensure_data_health_daily_rule(db)
    recipients = await _data_health_summary_recipients(db)
    today_key = now_local.date().isoformat()
    telegram_report_users: List[User] = []
    for user in recipients:
        pref = await _get_preference(db, str(user.id))
        if not (pref.deliver_in_app or pref.deliver_telegram):
            continue
        source_event_id = f"data_health.daily:{user.id}:{today_key}"
        if await Notification.exists_for_event(db, str(user.id), str(rule.id), source_event_id):
            continue
        await create_notification(
            db,
            user_id=str(user.id),
            title="Ежедневный health-check данных",
            message=message,
            type=priority,
            priority=priority,
            entity_type="data_health",
            entity_id=None,
            action_url="/data-health",
            rule_id=str(rule.id),
            source_event_id=source_event_id,
            deliver_at=None,
        )
        if pref.deliver_telegram:
            telegram_report_users.append(user)

    if telegram_report_users:
        try:
            pdf_bytes = await build_data_health_report_pdf(db, status="active", grouped=True, limit=1000)
        except Exception as error:
            logger.warning("Failed to build data health PDF report: %s", error)
            pdf_bytes = b""
        if pdf_bytes:
            for user in telegram_report_users:
                connection_result = await db.execute(
                    select(TelegramConnection).where(
                        TelegramConnection.user_id == str(user.id),
                        TelegramConnection.is_enabled.is_(True),
                        TelegramConnection.is_verified.is_(True),
                        TelegramConnection.chat_id.is_not(None),
                    )
                )
                connection = connection_result.scalar_one_or_none()
                if not connection:
                    continue
                try:
                    await send_telegram_document(
                        str(connection.chat_id),
                        pdf_bytes,
                        f"data-health-{today_key}.pdf",
                        caption="PDF-отчет контроля данных",
                    )
                except Exception as error:
                    logger.warning("Failed to send data health PDF report to Telegram for user %s: %s", user.id, error)

    job.last_run_at = datetime.utcnow()
    await db.commit()
