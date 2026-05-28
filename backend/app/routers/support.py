"""
Тех. поддержка — тикет-система.

Гейтится секцией прав `support` (на уровне include в main.py).
Сотрудник поддержки = read_all по `support` (или суперюзер): видит все
тикеты, внутренние заметки, меняет статус/исполнителя, создаёт задачи.
Заявитель = есть доступ к секции, но без read_all: видит только свои
тикеты и только публичные сообщения.
"""
import json
import uuid
from datetime import datetime
from typing import List, Optional, Union
from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, HTTPException, Request, UploadFile, File
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError

from app.core.auth_middleware import CurrentUser
from app.core.config import settings
from app.database.session import get_db
from app.models import SupportTicket, SupportMessage, Task, User
from app.schemas.user import _resolve_avatar_filename
from app.schemas.support import (
    CATEGORIES,
    STATUSES,
    CreateTaskFromTicket,
    SupportMessageResponse,
    SupportMessageUpdate,
    SupportTicketCreate,
    SupportTicketDetail,
    SupportTicketResponse,
    SupportTicketUpdate,
)
from app.services.notifications import create_notification
from app.services.permissions import get_section_permissions
from app.services.storage import (
    clean_name,
    ensure_path,
    storage_available,
    upload_bytes_with_safe_extension,
)

router = APIRouter()
MAX_SUPPORT_FILE_BYTES = 25 * 1024 * 1024
SECTION = "support"


async def _is_support_staff(request: Request, db: AsyncSession, user: User) -> bool:
    if getattr(request.state, "is_superuser", False):
        return True
    read_all, _ = await get_section_permissions(db, user.role_id, SECTION)
    return bool(read_all)


def _download_url(path: str) -> str:
    return f"/api/v1/storage/download?path={quote(path, safe='')}"


async def _next_number(db: AsyncSession, model) -> int:
    result = await db.execute(select(func.max(model.number)))
    current = result.scalar() or 0
    return int(current) + 1


def _serialize_message(message: SupportMessage) -> SupportMessageResponse:
    user_obj = message.__dict__.get("user")
    attachments = []
    if not message.is_deleted:
        for item in (message.attachments or []):
            if not isinstance(item, dict):
                continue
            payload = dict(item)
            if payload.get("path"):
                payload["download_url"] = _download_url(payload["path"])
            attachments.append(payload)
    return SupportMessageResponse(
        id=str(message.id),
        ticket_id=str(message.ticket_id),
        user_id=str(message.user_id),
        user_name=getattr(user_obj, "full_name", None),
        body=None if message.is_deleted else message.body,
        attachments=attachments,
        is_internal=bool(message.is_internal),
        is_deleted=bool(message.is_deleted),
        created_at=message.created_at,
        updated_at=message.updated_at,
        edited_at=message.edited_at,
        deleted_at=message.deleted_at,
    )


def _avatar_url_for(user_obj, user_id: Optional[str]) -> Optional[str]:
    if not user_obj or not user_id:
        return None
    filename = _resolve_avatar_filename(user_id, getattr(user_obj, "avatar_url", None))
    if not filename:
        return None
    return f"/api/v1/users/avatar-user/{user_id}"


def _serialize_ticket(ticket: SupportTicket, message_count: int = 0,
                       linked_task_number: Optional[int] = None,
                       last_at=None, last_by: Optional[str] = None) -> SupportTicketResponse:
    created_by = ticket.__dict__.get("created_by")
    assignee = ticket.__dict__.get("assignee")
    attachments = []
    for item in (ticket.attachments or []):
        if not isinstance(item, dict):
            continue
        payload = dict(item)
        if payload.get("path"):
            payload["download_url"] = _download_url(payload["path"])
        attachments.append(payload)
    return SupportTicketResponse(
        id=str(ticket.id),
        number=ticket.number,
        subject=ticket.subject,
        description=ticket.description,
        category=ticket.category or "other",
        status=ticket.status or "new",
        created_by_id=str(ticket.created_by_id),
        created_by_name=getattr(created_by, "full_name", None),
        created_by_avatar=_avatar_url_for(created_by, str(ticket.created_by_id)),
        assignee_id=str(ticket.assignee_id) if ticket.assignee_id else None,
        assignee_name=getattr(assignee, "full_name", None),
        linked_task_id=str(ticket.linked_task_id) if ticket.linked_task_id else None,
        linked_task_number=linked_task_number,
        attachments=attachments,
        message_count=message_count,
        last_message_at=last_at,
        last_message_by=last_by,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        resolved_at=ticket.resolved_at,
    )


async def _get_ticket(db: AsyncSession, ticket_id: str) -> SupportTicket:
    result = await db.execute(
        select(SupportTicket)
        .where(SupportTicket.id == str(ticket_id))
        .options(joinedload(SupportTicket.created_by), joinedload(SupportTicket.assignee))
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Тикет не найден")
    return ticket


async def _store_files(files_list: List[UploadFile], scope: str) -> List[dict]:
    if not files_list:
        return []
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")
    root = settings.STORAGE_LOCAL_ROOT or "/"
    base_path = f"{root.rstrip('/')}/_support/{scope}"
    await ensure_path(base_path)
    max_bytes = min(settings.UPLOAD_TMP_MAX_BYTES or MAX_SUPPORT_FILE_BYTES, MAX_SUPPORT_FILE_BYTES)
    out = []
    for upload in files_list:
        if not upload or not upload.filename:
            continue
        data = await upload.read()
        if max_bytes and len(data) > max_bytes:
            raise HTTPException(status_code=413, detail="Файл слишком большой")
        safe_name = clean_name(upload.filename)
        file_path = f"{base_path.rstrip('/')}/{uuid.uuid4().hex}_{safe_name}"
        await upload_bytes_with_safe_extension(file_path, data)
        out.append({
            "name": safe_name,
            "path": file_path,
            "size": len(data),
            "content_type": upload.content_type,
        })
    return out


@router.get("/tickets", response_model=List[SupportTicketResponse])
async def list_tickets(
    request: Request,
    status: Optional[str] = None,
    category: Optional[str] = None,
    assignee_id: Optional[str] = None,
    q: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    staff = await _is_support_staff(request, db, user)
    query = (
        select(SupportTicket)
        .options(joinedload(SupportTicket.created_by), joinedload(SupportTicket.assignee))
        .order_by(SupportTicket.created_at.desc())
    )
    if not staff:
        query = query.where(SupportTicket.created_by_id == str(user.id))
    if status:
        query = query.where(SupportTicket.status == status)
    if category:
        query = query.where(SupportTicket.category == category)
    if staff and assignee_id:
        query = query.where(SupportTicket.assignee_id == str(assignee_id))
    result = await db.execute(query)
    tickets = result.scalars().all()

    if q:
        ql = q.strip().lower()
        tickets = [
            t for t in tickets
            if ql in (t.subject or "").lower() or ql in (t.description or "").lower()
            or (t.number is not None and ql in str(t.number))
        ]

    ids = [str(t.id) for t in tickets]
    counts = {}
    last_map = {}
    if ids:
        cres = await db.execute(
            select(SupportMessage.ticket_id, func.count(SupportMessage.id))
            .where(SupportMessage.ticket_id.in_(ids))
            .group_by(SupportMessage.ticket_id)
        )
        counts = {str(r[0]): int(r[1]) for r in cres.all()}

        # Последнее сообщение на тикет (заявителю — без внутренних заметок).
        lq = (
            select(SupportMessage.ticket_id, SupportMessage.created_at, User.full_name)
            .join(User, User.id == SupportMessage.user_id)
            .where(SupportMessage.ticket_id.in_(ids))
            .order_by(SupportMessage.created_at.asc())
        )
        if not staff:
            lq = lq.where(SupportMessage.is_internal == False)  # noqa: E712
        lres = await db.execute(lq)
        for tid, created_at, full_name in lres.all():
            last_map[str(tid)] = (created_at, full_name)

    out = []
    for t in tickets:
        last = last_map.get(str(t.id))
        out.append(_serialize_ticket(
            t,
            counts.get(str(t.id), 0),
            last_at=last[0] if last else None,
            last_by=last[1] if last else None,
        ))
    return out


@router.post("/tickets", response_model=SupportTicketResponse)
async def create_ticket(
    request: Request,
    subject: str = Form(...),
    description: Optional[str] = Form(None),
    category: Optional[str] = Form("other"),
    files: Union[UploadFile, List[UploadFile], None] = File(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    subj = (subject or "").strip()
    if not subj:
        raise HTTPException(status_code=400, detail="Укажите тему обращения")
    cat = category if category in CATEGORIES else "other"

    for attempt in range(6):
        ticket = SupportTicket(
            number=await _next_number(db, SupportTicket),
            subject=subj[:255],
            description=(description or "").strip() or None,
            category=cat,
            status="new",
            created_by_id=str(user.id),
            attachments=[],
        )
        db.add(ticket)
        try:
            await db.commit()
            break
        except IntegrityError:
            await db.rollback()
            if attempt == 5:
                raise HTTPException(status_code=500, detail="Не удалось создать тикет")
    await db.refresh(ticket)

    files_list: List[UploadFile] = []
    if files:
        files_list = files if isinstance(files, list) else [files]
    if files_list:
        stored = await _store_files(files_list, str(ticket.id))
        if stored:
            ticket.attachments = stored
            await db.commit()
            await db.refresh(ticket)

    ticket.created_by = user
    return _serialize_ticket(ticket, 0)


@router.get("/tickets/{ticket_id}", response_model=SupportTicketDetail)
async def get_ticket(
    ticket_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    ticket = await _get_ticket(db, ticket_id)
    staff = await _is_support_staff(request, db, user)
    if not staff and str(ticket.created_by_id) != str(user.id):
        raise HTTPException(status_code=403, detail="Нет доступа к тикету")

    mq = (
        select(SupportMessage)
        .where(SupportMessage.ticket_id == str(ticket.id))
        .options(joinedload(SupportMessage.user))
        .order_by(SupportMessage.created_at.asc())
    )
    if not staff:
        mq = mq.where(SupportMessage.is_internal == False)  # noqa: E712
    mres = await db.execute(mq)
    messages = mres.scalars().all()

    linked_number = None
    if ticket.linked_task_id:
        tnum = await db.execute(select(Task.number).where(Task.id == str(ticket.linked_task_id)))
        linked_number = tnum.scalar()

    base = _serialize_ticket(ticket, len(messages), linked_number)
    return SupportTicketDetail(
        **base.model_dump(),
        messages=[_serialize_message(m) for m in messages],
    )


@router.patch("/tickets/{ticket_id}", response_model=SupportTicketResponse)
async def update_ticket(
    ticket_id: str,
    payload: SupportTicketUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    if not await _is_support_staff(request, db, user):
        raise HTTPException(status_code=403, detail="Только тех. поддержка")
    ticket = await _get_ticket(db, ticket_id)

    status_changed = False
    if payload.status is not None:
        if payload.status not in STATUSES:
            raise HTTPException(status_code=400, detail="Недопустимый статус")
        status_changed = ticket.status != payload.status
        ticket.status = payload.status
        ticket.resolved_at = datetime.utcnow() if payload.status in ("resolved", "closed") else None
    if payload.category is not None:
        ticket.category = payload.category if payload.category in CATEGORIES else ticket.category
    assignee_changed = False
    if payload.assignee_id is not None:
        new_assignee = payload.assignee_id or None
        assignee_changed = str(ticket.assignee_id or "") != str(new_assignee or "")
        ticket.assignee_id = new_assignee

    await db.commit()
    await db.refresh(ticket)

    try:
        if status_changed and str(ticket.created_by_id) != str(user.id):
            await create_notification(
                db,
                user_id=str(ticket.created_by_id),
                title=f"Тикет #{ticket.number}: статус изменён",
                message=ticket.subject,
                type="info",
                entity_type="support_ticket",
                entity_id=str(ticket.id),
                action_url=f"/support?ticket_id={ticket.id}",
            )
        if assignee_changed and ticket.assignee_id and str(ticket.assignee_id) != str(user.id):
            await create_notification(
                db,
                user_id=str(ticket.assignee_id),
                title=f"Назначен тикет #{ticket.number}",
                message=ticket.subject,
                type="info",
                entity_type="support_ticket",
                entity_id=str(ticket.id),
                action_url=f"/support?ticket_id={ticket.id}",
            )
    except Exception:
        pass

    result = await db.execute(
        select(SupportTicket).where(SupportTicket.id == str(ticket.id))
        .options(joinedload(SupportTicket.created_by), joinedload(SupportTicket.assignee))
    )
    return _serialize_ticket(result.scalar_one(), 0)


@router.post("/tickets/{ticket_id}/messages", response_model=SupportMessageResponse)
async def add_message(
    ticket_id: str,
    request: Request,
    body: Optional[str] = Form(None),
    is_internal: Optional[bool] = Form(False),
    files: Union[UploadFile, List[UploadFile], None] = File(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    ticket = await _get_ticket(db, ticket_id)
    staff = await _is_support_staff(request, db, user)
    if not staff and str(ticket.created_by_id) != str(user.id):
        raise HTTPException(status_code=403, detail="Нет доступа к тикету")

    internal = bool(is_internal) and staff  # заявитель не может писать внутренние
    content = (body or "").strip()
    files_list: List[UploadFile] = []
    if files:
        files_list = files if isinstance(files, list) else [files]
    if not content and not files_list:
        raise HTTPException(status_code=400, detail="Пустое сообщение")

    message = SupportMessage(
        ticket_id=str(ticket.id),
        user_id=str(user.id),
        body=content or None,
        is_internal=internal,
        attachments=[],
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    if files_list:
        stored = await _store_files(files_list, f"{ticket.id}/{message.id}")
        if stored:
            message.attachments = stored
            await db.commit()
            await db.refresh(message)

    # Автостатус: ответ заявителя на «ожидает ответа» → снова «в работе».
    if not staff and ticket.status == "waiting_user":
        ticket.status = "in_progress"
        await db.commit()

    try:
        if internal:
            if ticket.assignee_id and str(ticket.assignee_id) != str(user.id):
                await create_notification(
                    db, user_id=str(ticket.assignee_id),
                    title=f"Внутр. заметка по тикету #{ticket.number}",
                    message=content[:200] if content else "Вложение",
                    type="info", entity_type="support_ticket", entity_id=str(ticket.id),
                    action_url=f"/support?ticket_id={ticket.id}",
                )
        elif staff:
            if str(ticket.created_by_id) != str(user.id):
                await create_notification(
                    db, user_id=str(ticket.created_by_id),
                    title=f"Ответ поддержки по тикету #{ticket.number}",
                    message=content[:200] if content else "Вложение",
                    type="info", entity_type="support_ticket", entity_id=str(ticket.id),
                    action_url=f"/support?ticket_id={ticket.id}",
                )
        else:
            if ticket.assignee_id and str(ticket.assignee_id) != str(user.id):
                await create_notification(
                    db, user_id=str(ticket.assignee_id),
                    title=f"Сообщение в тикете #{ticket.number}",
                    message=content[:200] if content else "Вложение",
                    type="info", entity_type="support_ticket", entity_id=str(ticket.id),
                    action_url=f"/support?ticket_id={ticket.id}",
                )
    except Exception:
        pass

    result = await db.execute(
        select(SupportMessage).where(SupportMessage.id == message.id)
        .options(joinedload(SupportMessage.user))
    )
    loaded = result.scalar_one_or_none() or message
    return _serialize_message(loaded)


@router.patch("/messages/{message_id}", response_model=SupportMessageResponse)
async def update_message(
    message_id: str,
    payload: SupportMessageUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    message = await db.get(SupportMessage, message_id, options=[joinedload(SupportMessage.user)])
    if not message:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    staff = await _is_support_staff(request, db, user)
    if str(message.user_id) != str(user.id) and not staff:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    if message.is_deleted:
        raise HTTPException(status_code=400, detail="Сообщение удалено")
    text = (payload.body or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Сообщение не может быть пустым")
    message.body = text
    message.edited_at = datetime.utcnow()
    await db.commit()
    await db.refresh(message)
    return _serialize_message(message)


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    message = await db.get(SupportMessage, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Сообщение не найдено")
    staff = await _is_support_staff(request, db, user)
    if str(message.user_id) != str(user.id) and not staff:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    if message.is_deleted:
        return {"deleted": True}
    message.is_deleted = True
    message.deleted_at = datetime.utcnow()
    await db.commit()
    return {"deleted": True}


@router.post("/tickets/{ticket_id}/create-task")
async def create_task_from_ticket(
    ticket_id: str,
    payload: CreateTaskFromTicket,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    if not await _is_support_staff(request, db, user):
        raise HTTPException(status_code=403, detail="Только тех. поддержка")
    ticket = await _get_ticket(db, ticket_id)

    title = (payload.title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Укажите название задачи")

    assigned_user = None
    if payload.assigned_to_user_id:
        assigned_user = await User.get_by_id(db, payload.assigned_to_user_id)
        if not assigned_user:
            raise HTTPException(status_code=404, detail="Исполнитель не найден")

    task = None
    for attempt in range(6):
        task = Task(
            number=await _next_number(db, Task),
            title=title[:255],
            description=payload.description or ticket.description,
            deal_id=None,
            status="new",
            priority=payload.priority or "normal",
            assigned_to_user_id=str(assigned_user.id) if assigned_user else None,
            created_by_user_id=str(user.id),
            start_date=payload.start_date,
            due_date=payload.due_date,
        )
        db.add(task)
        try:
            await db.commit()
            break
        except IntegrityError:
            await db.rollback()
            if attempt == 5:
                raise HTTPException(status_code=500, detail="Не удалось создать задачу")
    await db.refresh(task)

    ticket.linked_task_id = str(task.id)
    if ticket.status == "new":
        ticket.status = "in_progress"

    note = SupportMessage(
        ticket_id=str(ticket.id),
        user_id=str(user.id),
        body=f"Создана задача #{task.number}: {title}",
        is_internal=True,
        attachments=[],
    )
    db.add(note)
    await db.commit()

    try:
        if assigned_user and str(assigned_user.id) != str(user.id):
            await create_notification(
                db, user_id=str(assigned_user.id),
                title=f"Новая задача #{task.number}",
                message=title,
                type="info", entity_type="task", entity_id=str(task.id),
                action_url=f"/tasks?task_id={task.id}",
            )
    except Exception:
        pass

    return {"task_id": str(task.id), "task_number": task.number}
