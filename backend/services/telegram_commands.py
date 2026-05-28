"""
Read-only Telegram bot commands.

The bot never trusts a Telegram chat by itself. Every command is executed only
after resolving an enabled, verified Telegram connection to an active system user
and then applying the same section/deal visibility rules as the API.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from html import escape
from typing import Any, Awaitable, Callable, Iterable, Optional

from sqlalchemy import String, and_, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.config import settings
from app.models import (
    DataHealthIssue,
    Deal,
    DealGip,
    Document,
    IncomeExpenseEntry,
    Lead,
    Notification,
    NotificationPreference,
    OutgoingDocument,
    Role,
    Task,
    TelegramConnection,
    User,
)
from app.services.permissions import get_section_permissions
from app.services.telegram_bot import send_telegram_message, utcnow_naive


HealthReportSender = Callable[[AsyncSession, Optional[Any]], Awaitable[None]]


BOT_COMMANDS: list[dict[str, str]] = [
    {"command": "summary", "description": "Сводка по доступным данным"},
    {"command": "tasks", "description": "Мои/доступные задачи"},
    {"command": "overdue", "description": "Просроченные задачи"},
    {"command": "projects", "description": "Доступные сделки"},
    {"command": "project", "description": "Карточка сделки по ID или названию"},
    {"command": "leads", "description": "Доступные лиды"},
    {"command": "payments", "description": "Плановые и фактические платежи"},
    {"command": "docs", "description": "Документы и письма с учетом прав"},
    {"command": "notifications", "description": "Последние уведомления"},
    {"command": "settings", "description": "Настройки Telegram"},
    {"command": "health", "description": "PDF health-check контроля данных"},
    {"command": "health_pdf", "description": "PDF health-check контроля данных"},
    {"command": "help", "description": "Список команд"},
]

_OPEN_TASK_STATUSES = {"new", "in_progress", "pending", "deferred"}
_DONE_TASK_STATUSES = {"completed", "cancelled"}


@dataclass
class TelegramCommandContext:
    connection: TelegramConnection
    user_id: str
    user_name: str
    role_id: Optional[str]
    is_superuser: bool


def help_text() -> str:
    return (
        "<b>Команды Nexus</b>\n"
        "/summary - краткая сводка\n"
        "/tasks - открытые задачи\n"
        "/overdue - просроченные задачи\n"
        "/projects [поиск] - сделки\n"
        "/project &lt;ID или часть названия&gt; - сделка\n"
        "/leads [поиск] - лиды\n"
        "/payments - ближайшие платежи\n"
        "/docs [поиск] - документы и письма\n"
        "/notifications - последние уведомления\n"
        "/settings - статус Telegram\n"
        "/health - PDF health-check"
    )


def _command_name(text: str) -> str:
    command = (text or "").strip().split(maxsplit=1)[0].lower()
    return command.split("@", 1)[0]


def _command_arg(text: str) -> str:
    parts = (text or "").strip().split(maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else ""


def _fmt_date(value: Any) -> str:
    if not value:
        return "-"
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y")
    if isinstance(value, date):
        return value.strftime("%d.%m.%Y")
    return str(value)


def _fmt_money(value: Any) -> str:
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0.0
    return f"{amount:,.2f} ₽".replace(",", " ")


def _short(value: Any, limit: int = 80) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: max(1, limit - 1)].rstrip() + "…"


def _status_task(value: Any) -> str:
    labels = {
        "new": "Новая",
        "in_progress": "В работе",
        "pending": "Ожидает",
        "completed": "Готово",
        "cancelled": "Отменена",
        "deferred": "Отложена",
    }
    return labels.get(str(value or ""), str(value or "-"))


def _status_deal(value: Any) -> str:
    labels = {
        "active": "Активна",
        "completed": "Завершена",
        "paused": "Пауза",
        "cancelled": "Отменена",
    }
    return labels.get(str(value or ""), str(value or "-"))


def _status_lead(value: Any) -> str:
    labels = {
        "incoming": "Входящий",
        "in_progress": "В работе",
        "converted": "Конвертирован",
        "rejected": "Отклонен",
    }
    return labels.get(str(value or ""), str(value or "-"))


def _status_payment(entry: IncomeExpenseEntry) -> str:
    return "оплачено" if entry.actual_date else "ожидает"


def _normalize_id(value: Any) -> Optional[str]:
    if value in (None, ""):
        return None
    return str(value).replace("-", "").strip().lower() or None


def _normalized_column(column: Any):
    return func.replace(func.lower(cast(column, String)), "-", "")


def _id_filter(column: Any, values: Iterable[Any]):
    normalized = [value for value in (_normalize_id(item) for item in values) if value]
    if not normalized:
        return _normalized_column(column).in_(["__never_match__"])
    return _normalized_column(column).in_(normalized)


def _same_id(column: Any, value: Any):
    normalized = _normalize_id(value)
    if not normalized:
        return _normalized_column(column) == "__never_match__"
    return _normalized_column(column) == normalized


def _same_id_columns(left: Any, right: Any):
    return _normalized_column(left) == _normalized_column(right)


def _app_link(path: str) -> str:
    base_url = (settings.PUBLIC_APP_URL or "").rstrip("/")
    if not base_url:
        return path
    normalized = path if path.startswith("/") else f"/{path}"
    return f"{base_url}{normalized}"


async def _send(chat_id: Optional[Any], text: str, *, reply_markup: Optional[dict] = None) -> None:
    if not chat_id:
        return
    await send_telegram_message(str(chat_id), text, reply_markup=reply_markup)


async def _context_for_chat(db: AsyncSession, chat_id: Optional[Any]) -> Optional[TelegramCommandContext]:
    if chat_id is None:
        return None
    result = await db.execute(
        select(TelegramConnection).where(
            TelegramConnection.chat_id == str(chat_id),
            TelegramConnection.is_enabled.is_(True),
            TelegramConnection.is_verified.is_(True),
            TelegramConnection.user_id.is_not(None),
        )
    )
    connection = result.scalar_one_or_none()
    if not connection:
        return None

    user_result = await db.execute(select(User).where(User.id == str(connection.user_id)))
    user = user_result.scalar_one_or_none()
    if not user or not user.is_active:
        return None

    role = None
    if user.role_id:
        role_result = await db.execute(select(Role).where(Role.id == str(user.role_id)))
        role = role_result.scalar_one_or_none()

    return TelegramCommandContext(
        connection=connection,
        user_id=str(user.id),
        user_name=user.full_name or user.email or str(user.id),
        role_id=str(user.role_id) if user.role_id else None,
        is_superuser=bool(role and role.is_system),
    )


async def _section_access(db: AsyncSession, ctx: TelegramCommandContext, section: str) -> tuple[bool, bool]:
    if ctx.is_superuser:
        return True, True
    return await get_section_permissions(db, ctx.role_id, section)


async def _read_allowed(db: AsyncSession, ctx: TelegramCommandContext, section: str) -> bool:
    read_all, read_assigned = await _section_access(db, ctx, section)
    return bool(read_all or read_assigned)


async def _accessible_deal_ids(db: AsyncSession, ctx: TelegramCommandContext) -> Optional[list[str]]:
    if ctx.is_superuser:
        return None
    read_all, read_assigned = await _section_access(db, ctx, "projects")
    if read_all:
        return None
    if not read_assigned:
        return []
    result = await db.execute(select(DealGip.deal_id).where(DealGip.user_id == ctx.user_id))
    return [str(row[0]) for row in result.all() if row[0]]


async def health_report_allowed_deal_ids(db: AsyncSession, chat_id: Optional[Any]) -> Optional[list[str]]:
    """Return the deal filter for Telegram health reports.

    None means global access, a list means assigned-only access. A PermissionError
    means the chat is not linked or the user cannot read projects at all.
    """
    ctx = await _context_for_chat(db, chat_id)
    if not ctx:
        raise PermissionError("telegram_not_linked")
    if not await _read_allowed(db, ctx, "projects"):
        raise PermissionError("projects_access_denied")
    return await _accessible_deal_ids(db, ctx)


async def _ensure_project_access(db: AsyncSession, ctx: TelegramCommandContext) -> Optional[list[str]]:
    allowed = await _accessible_deal_ids(db, ctx)
    if allowed == []:
        return []
    return allowed


def _apply_deal_access(query, column: Any, allowed_deal_ids: Optional[list[str]]):
    if allowed_deal_ids is None:
        return query
    return query.where(_id_filter(column, allowed_deal_ids))


async def _scalar_count(db: AsyncSession, query) -> int:
    result = await db.execute(query)
    return int(result.scalar() or 0)


async def _tasks_query(db: AsyncSession, ctx: TelegramCommandContext, *, overdue_only: bool = False, include_deal: bool = False):
    read_all, read_assigned = await _section_access(db, ctx, "tasks")
    if not read_all and not read_assigned:
        return None
    query = select(Task)
    if include_deal:
        query = query.options(joinedload(Task.deal))
    query = query.where(Task.status.in_(sorted(_OPEN_TASK_STATUSES)))
    if not read_all:
        query = query.where(Task.assigned_to_user_id == ctx.user_id)
    if overdue_only:
        query = query.where(Task.due_date.is_not(None), Task.due_date < date.today())
    return query


async def _handle_summary(db: AsyncSession, chat_id: Any, ctx: TelegramCommandContext) -> None:
    allowed_deals = await _ensure_project_access(db, ctx)
    projects_count = 0
    if allowed_deals != []:
        projects_query = select(func.count(Deal.id))
        projects_query = _apply_deal_access(projects_query, Deal.id, allowed_deals)
        projects_count = await _scalar_count(db, projects_query)

    tasks_count = overdue_count = 0
    tasks_query = await _tasks_query(db, ctx)
    if tasks_query is not None:
        tasks_count = await _scalar_count(db, tasks_query.with_only_columns(func.count(Task.id)).order_by(None))
        overdue_query = await _tasks_query(db, ctx, overdue_only=True)
        overdue_count = await _scalar_count(db, overdue_query.with_only_columns(func.count(Task.id)).order_by(None)) if overdue_query is not None else 0

    payments_count = 0
    payment_read_all, payment_read_assigned = await _section_access(db, ctx, "income_expense")
    if payment_read_all or payment_read_assigned:
        payments_query = select(func.count(IncomeExpenseEntry.id)).where(
            IncomeExpenseEntry.actual_date.is_(None),
            IncomeExpenseEntry.plan_date >= date.today(),
        )
        if not payment_read_all:
            payments_query = _apply_deal_access(payments_query, IncomeExpenseEntry.deal_id, allowed_deals)
        payments_count = await _scalar_count(db, payments_query)

    health_count = 0
    if allowed_deals != []:
        health_query = select(func.count(DataHealthIssue.id)).where(DataHealthIssue.status.in_(["open", "ignored"]))
        if allowed_deals is not None:
            health_query = health_query.where(DataHealthIssue.deal_id.is_not(None), _id_filter(DataHealthIssue.deal_id, allowed_deals))
        health_count = await _scalar_count(db, health_query)

    await _send(
        chat_id,
        (
            "<b>Сводка</b>\n"
            f"Сделки: <b>{projects_count}</b>\n"
            f"Открытые задачи: <b>{tasks_count}</b>\n"
            f"Просроченные задачи: <b>{overdue_count}</b>\n"
            f"Ожидаемые платежи: <b>{payments_count}</b>\n"
            f"Проблемы контроля данных: <b>{health_count}</b>"
        ),
    )


async def _handle_tasks(db: AsyncSession, chat_id: Any, ctx: TelegramCommandContext, *, overdue_only: bool = False) -> None:
    query = await _tasks_query(db, ctx, overdue_only=overdue_only, include_deal=True)
    if query is None:
        await _send(chat_id, "Нет доступа к задачам.")
        return
    query = query.order_by(Task.due_date.asc().nullslast(), Task.created_at.desc()).limit(10)
    result = await db.execute(query)
    tasks = result.unique().scalars().all()
    title = "Просроченные задачи" if overdue_only else "Открытые задачи"
    if not tasks:
        await _send(chat_id, f"<b>{title}</b>\nНичего не найдено.")
        return
    lines = [f"<b>{title}</b>"]
    for task in tasks:
        deal_title = getattr(getattr(task, "deal", None), "title", None)
        due = _fmt_date(task.due_date)
        lines.append(
            f"• <b>{escape(_short(task.title, 60))}</b> | {escape(_status_task(task.status))} | срок {escape(due)}"
            + (f"\n  {escape(_short(deal_title, 70))}" if deal_title else "")
        )
    await _send(chat_id, "\n".join(lines))


async def _handle_projects(db: AsyncSession, chat_id: Any, ctx: TelegramCommandContext, search: str) -> None:
    allowed = await _accessible_deal_ids(db, ctx)
    if allowed == []:
        await _send(chat_id, "Нет доступа к сделкам.")
        return
    query = select(Deal)
    query = _apply_deal_access(query, Deal.id, allowed)
    if search:
        token = f"%{search}%"
        query = query.where(or_(Deal.title.ilike(token), Deal.obj_name.ilike(token), Deal.address.ilike(token)))
    query = query.order_by(Deal.updated_at.desc().nullslast(), Deal.created_at.desc()).limit(10)
    result = await db.execute(query)
    deals = result.scalars().all()
    if not deals:
        await _send(chat_id, "<b>Сделки</b>\nНичего не найдено.")
        return
    lines = ["<b>Сделки</b>"]
    for deal in deals:
        lines.append(
            f"• <a href=\"{escape(_app_link(f'/projects/{deal.id}'), quote=True)}\">{escape(_short(deal.title, 70))}</a>"
            f" | {escape(_status_deal(deal.status))}"
        )
    await _send(chat_id, "\n".join(lines))


async def _handle_project(db: AsyncSession, chat_id: Any, ctx: TelegramCommandContext, search: str) -> None:
    if not search:
        await _send(chat_id, "Укажите ID или часть названия: /project Новоленская")
        return
    allowed = await _accessible_deal_ids(db, ctx)
    if allowed == []:
        await _send(chat_id, "Нет доступа к сделкам.")
        return
    query = select(Deal)
    query = _apply_deal_access(query, Deal.id, allowed)
    query = query.where(
        or_(
            _same_id(Deal.id, search),
            Deal.title.ilike(f"%{search}%"),
            Deal.obj_name.ilike(f"%{search}%"),
            Deal.address.ilike(f"%{search}%"),
        )
    )
    result = await db.execute(query.order_by(Deal.updated_at.desc().nullslast(), Deal.created_at.desc()).limit(1))
    deal = result.scalar_one_or_none()
    if not deal:
        await _send(chat_id, "Сделка не найдена или недоступна.")
        return

    open_tasks = 0
    if await _read_allowed(db, ctx, "tasks"):
        task_query = select(func.count(Task.id)).where(Task.deal_id == str(deal.id), Task.status.in_(sorted(_OPEN_TASK_STATUSES)))
        read_all, _ = await _section_access(db, ctx, "tasks")
        if not read_all:
            task_query = task_query.where(Task.assigned_to_user_id == ctx.user_id)
        open_tasks = await _scalar_count(db, task_query)

    expected_payments = 0
    if await _read_allowed(db, ctx, "income_expense"):
        expected_payments = await _scalar_count(
            db,
            select(func.count(IncomeExpenseEntry.id)).where(
                IncomeExpenseEntry.deal_id == str(deal.id),
                IncomeExpenseEntry.actual_date.is_(None),
            ),
        )

    docs_count = 0
    if await _read_allowed(db, ctx, "document_registry"):
        docs_count += await _scalar_count(db, select(func.count(Document.id)).where(_same_id(Document.project_id, deal.id)))
    if await _read_allowed(db, ctx, "outgoing_registry"):
        docs_count += await _scalar_count(db, select(func.count(OutgoingDocument.id)).where(_same_id(OutgoingDocument.deal_id, deal.id)))

    await _send(
        chat_id,
        (
            f"<b>{escape(deal.title)}</b>\n"
            f"Статус: {escape(_status_deal(deal.status))}\n"
            f"Объект: {escape(_short(deal.obj_name, 160) or '-')}\n"
            f"Адрес: {escape(_short(deal.address, 160) or '-')}\n"
            f"Стоимость: <b>{escape(_fmt_money(deal.total_contract_value))}</b>\n"
            f"Открытые задачи: <b>{open_tasks}</b>\n"
            f"Ожидаемые платежи: <b>{expected_payments}</b>\n"
            f"Документы/письма: <b>{docs_count}</b>\n"
            f"<a href=\"{escape(_app_link(f'/projects/{deal.id}'), quote=True)}\">Открыть в системе</a>"
        ),
    )


async def _handle_leads(db: AsyncSession, chat_id: Any, ctx: TelegramCommandContext, search: str) -> None:
    read_all, read_assigned = await _section_access(db, ctx, "leads")
    if not read_all and not read_assigned:
        await _send(chat_id, "Нет доступа к лидам.")
        return
    query = select(Lead)
    if not read_all:
        query = query.where(Lead.responsible_user_id == ctx.user_id)
    if search:
        token = f"%{search}%"
        query = query.where(or_(Lead.title.ilike(token), Lead.obj_name.ilike(token), Lead.address.ilike(token)))
    result = await db.execute(query.order_by(Lead.updated_at.desc().nullslast(), Lead.created_at.desc()).limit(10))
    leads = result.scalars().all()
    if not leads:
        await _send(chat_id, "<b>Лиды</b>\nНичего не найдено.")
        return
    lines = ["<b>Лиды</b>"]
    for lead in leads:
        lines.append(f"• <b>{escape(_short(lead.title, 70))}</b> | {escape(_status_lead(lead.status))} | {escape(_fmt_money(lead.total_value))}")
    await _send(chat_id, "\n".join(lines))


async def _handle_payments(db: AsyncSession, chat_id: Any, ctx: TelegramCommandContext) -> None:
    read_all, read_assigned = await _section_access(db, ctx, "income_expense")
    if not read_all and not read_assigned:
        await _send(chat_id, "Нет доступа к платежам.")
        return
    allowed = None if read_all else await _accessible_deal_ids(db, ctx)
    if not read_all and allowed == []:
        await _send(chat_id, "Нет доступных сделок для платежей.")
        return
    query = (
        select(IncomeExpenseEntry, Deal)
        .outerjoin(Deal, _same_id_columns(Deal.id, IncomeExpenseEntry.deal_id))
    )
    query = _apply_deal_access(query, IncomeExpenseEntry.deal_id, allowed)
    query = query.order_by(IncomeExpenseEntry.actual_date.is_not(None), IncomeExpenseEntry.plan_date.asc()).limit(10)
    result = await db.execute(query)
    rows = result.all()
    if not rows:
        await _send(chat_id, "<b>Платежи</b>\nНичего не найдено.")
        return
    lines = ["<b>Платежи</b>"]
    for entry, deal in rows:
        direction = "приход" if entry.direction == "income" else "расход"
        date_value = entry.actual_date or entry.plan_date
        lines.append(
            f"• {escape(_fmt_date(date_value))} | {escape(direction)} | <b>{escape(_fmt_money(entry.amount))}</b> | {escape(_status_payment(entry))}"
            + (f"\n  {escape(_short(deal.title, 70))}" if deal else "")
        )
    await _send(chat_id, "\n".join(lines))


async def _handle_docs(db: AsyncSession, chat_id: Any, ctx: TelegramCommandContext, search: str) -> None:
    """
    Point 7: documents must be rights-aware.

    Sources included:
    - Document Registry only if the user can read `document_registry`.
    - Outgoing Registry only if the user can read `outgoing_registry`.
    - For read_assigned access, both sources are additionally limited to deals
      available to the user through project permissions/DealGip.
    - Orphan/outgoing-without-deal items are shown only to users with read_all
      on the corresponding section.
    """
    allowed = await _accessible_deal_ids(db, ctx)
    items: list[tuple[datetime, str, str, str, Optional[str]]] = []

    doc_read_all, doc_read_assigned = await _section_access(db, ctx, "document_registry")
    if doc_read_all or doc_read_assigned:
        doc_query = select(Document)
        if not doc_read_all:
            if allowed == []:
                doc_query = None
            else:
                doc_query = _apply_deal_access(doc_query, Document.project_id, allowed)
        if doc_query is not None:
            if search:
                token = f"%{search}%"
                doc_query = doc_query.where(or_(Document.title.ilike(token), Document.number.ilike(token), Document.doc_type.ilike(token)))
            result = await db.execute(doc_query.order_by(Document.document_date.desc().nullslast(), Document.created_at.desc()).limit(10))
            for doc in result.scalars().all():
                sort_dt = doc.created_at or datetime.min
                title = doc.title or doc.number or "Документ"
                meta = f"{doc.doc_type or '-'} | {doc.status or '-'} | {_fmt_date(doc.document_date)}"
                items.append((sort_dt, "Документ", title, meta, doc.project_id))

    out_read_all, out_read_assigned = await _section_access(db, ctx, "outgoing_registry")
    if out_read_all or out_read_assigned:
        out_query = select(OutgoingDocument)
        if not out_read_all:
            if allowed == []:
                out_query = None
            else:
                out_query = out_query.where(OutgoingDocument.deal_id.is_not(None))
                out_query = _apply_deal_access(out_query, OutgoingDocument.deal_id, allowed)
        if out_query is not None:
            if search:
                token = f"%{search}%"
                out_query = out_query.where(or_(OutgoingDocument.subject.ilike(token), OutgoingDocument.outgoing_number.ilike(token)))
            result = await db.execute(out_query.order_by(OutgoingDocument.letter_date.desc().nullslast(), OutgoingDocument.created_at.desc()).limit(10))
            for item in result.scalars().all():
                sort_dt = item.created_at or datetime.min
                title = item.subject or item.outgoing_number or "Исходящее письмо"
                meta = f"№ {item.outgoing_number or '-'} | {item.status or '-'} | {_fmt_date(item.letter_date)}"
                items.append((sort_dt, "Письмо", title, meta, item.deal_id))

    if not (doc_read_all or doc_read_assigned or out_read_all or out_read_assigned):
        await _send(chat_id, "Нет доступа к документам и исходящим письмам.")
        return
    if not items:
        await _send(chat_id, "<b>Документы и письма</b>\nНичего не найдено.")
        return

    lines = ["<b>Документы и письма</b>"]
    for _, kind, title, meta, deal_id in sorted(items, key=lambda row: row[0], reverse=True)[:10]:
        line = f"• <b>{escape(kind)}</b>: {escape(_short(title, 72))}\n  {escape(_short(meta, 100))}"
        if deal_id:
            line += f"\n  <a href=\"{escape(_app_link(f'/projects/{deal_id}'), quote=True)}\">Сделка</a>"
        lines.append(line)
    await _send(chat_id, "\n".join(lines))


async def _handle_notifications(db: AsyncSession, chat_id: Any, ctx: TelegramCommandContext) -> None:
    result = await db.execute(
        select(Notification)
        .where(
            Notification.user_id == ctx.user_id,
            or_(Notification.deliver_at.is_(None), Notification.deliver_at <= datetime.utcnow()),
        )
        .order_by(Notification.created_at.desc())
        .limit(10)
    )
    items = result.scalars().all()
    if not items:
        await _send(chat_id, "<b>Уведомления</b>\nНичего не найдено.")
        return
    lines = ["<b>Уведомления</b>"]
    for item in items:
        marker = "непрочитано" if not item.is_read else "прочитано"
        lines.append(f"• <b>{escape(_short(item.title, 70))}</b> | {marker}\n  {escape(_short(item.message, 100))}")
    await _send(chat_id, "\n".join(lines))


async def _handle_settings(db: AsyncSession, chat_id: Any, ctx: TelegramCommandContext) -> None:
    pref_result = await db.execute(select(NotificationPreference).where(NotificationPreference.user_id == ctx.user_id))
    pref = pref_result.scalar_one_or_none()
    await _send(
        chat_id,
        (
            "<b>Telegram</b>\n"
            f"Пользователь: {escape(ctx.user_name)}\n"
            f"Статус: подключен\n"
            f"Доставка уведомлений: {'включена' if pref and pref.deliver_telegram else 'выключена'}\n"
            f"Последняя активность: {escape(_fmt_date(ctx.connection.last_seen_at))}"
        ),
    )


async def handle_telegram_command(
    db: AsyncSession,
    chat_id: Optional[Any],
    text: str,
    *,
    send_health_report: Optional[HealthReportSender] = None,
) -> bool:
    command = _command_name(text)
    if not command or not command.startswith("/"):
        return False

    known = {
        "/summary",
        "/tasks",
        "/overdue",
        "/projects",
        "/project",
        "/leads",
        "/payments",
        "/docs",
        "/notifications",
        "/settings",
        "/help",
        "/health",
        "/health_pdf",
    }
    if command not in known:
        return False

    ctx = await _context_for_chat(db, chat_id)
    if not ctx:
        await _send(chat_id, "Сначала привяжите Telegram к пользователю в системе.")
        return True

    ctx.connection.last_seen_at = utcnow_naive()
    arg = _command_arg(text)

    if command in {"/health", "/health_pdf"}:
        if not await _read_allowed(db, ctx, "projects"):
            await _send(chat_id, "Нет доступа к контролю данных.")
            return True
        if send_health_report:
            await send_health_report(db, chat_id)
        else:
            await _send(chat_id, "PDF health-check временно недоступен.")
        return True
    if command == "/summary":
        await _handle_summary(db, chat_id, ctx)
    elif command == "/tasks":
        await _handle_tasks(db, chat_id, ctx)
    elif command == "/overdue":
        await _handle_tasks(db, chat_id, ctx, overdue_only=True)
    elif command == "/projects":
        await _handle_projects(db, chat_id, ctx, arg)
    elif command == "/project":
        await _handle_project(db, chat_id, ctx, arg)
    elif command == "/leads":
        await _handle_leads(db, chat_id, ctx, arg)
    elif command == "/payments":
        await _handle_payments(db, chat_id, ctx)
    elif command == "/docs":
        await _handle_docs(db, chat_id, ctx, arg)
    elif command == "/notifications":
        await _handle_notifications(db, chat_id, ctx)
    elif command == "/settings":
        await _handle_settings(db, chat_id, ctx)
    else:
        await _send(chat_id, help_text())
    await db.commit()
    return True
