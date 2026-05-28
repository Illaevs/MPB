"""
Task chat/messages endpoints.
"""
import json
from datetime import datetime
from typing import Dict, List, Optional, Union
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.core.config import settings
from app.database.session import get_db
from app.models import Task, TaskAssignee, TaskMessage, TaskRead, TaskWatcher, User
from app.schemas.task_message import TaskMessageResponse, TaskMessageUpdate
from app.services.notifications import create_notification
from app.services.permissions import get_section_permissions
from app.services.storage import (
    ensure_path,
    clean_name,
    upload_bytes_with_safe_extension,
    storage_available,
)


router = APIRouter()
MAX_TASK_CHAT_FILE_BYTES = 50 * 1024 * 1024


def _is_admin(request: Request) -> bool:
    if getattr(request.state, "is_superuser", False):
        return True
    role = getattr(request.state, "role", None)
    name = (getattr(role, "name", "") or "").lower()
    return "admin" in name or "админ" in name


async def _require_task_chat_access(
    request: Request,
    db: AsyncSession,
    user: User,
    task: Task,
) -> None:
    if getattr(request.state, "is_superuser", False):
        return
    read_all, read_assigned = await get_section_permissions(db, user.role_id, "task_chat")
    if read_all:
        return
    if not read_assigned:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if not task or not task.assigned_to_user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if str(task.assigned_to_user_id) != str(user.id):
        raise HTTPException(status_code=403, detail="Not enough permissions")


def _download_url(path: str) -> str:
    return f"/api/v1/storage/download?path={quote(path, safe='')}"


def _serialize_message(message: TaskMessage) -> TaskMessageResponse:
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
    return TaskMessageResponse(
        id=str(message.id),
        task_id=str(message.task_id),
        user_id=str(message.user_id),
        user_name=getattr(user_obj, "full_name", None),
        body=None if message.is_deleted else message.body,
        attachments=attachments,
        mentions=message.mentions or [],
        is_deleted=bool(message.is_deleted),
        created_at=message.created_at,
        updated_at=message.updated_at,
        edited_at=message.edited_at,
        deleted_at=message.deleted_at,
    )


@router.get("/tasks/{task_id}/messages", response_model=List[TaskMessageResponse])
async def list_task_messages(
    task_id: str,
    request: Request,
    skip: int = 0,
    limit: int = 200,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    task = await Task.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await _require_task_chat_access(request, db, user, task)

    query = (
        select(TaskMessage)
        .where(TaskMessage.task_id == str(task.id))
        .options(joinedload(TaskMessage.user))
        .order_by(TaskMessage.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    result = await db.execute(query)
    messages = result.scalars().all()
    return [_serialize_message(msg) for msg in messages]


@router.post("/tasks/{task_id}/messages", response_model=TaskMessageResponse)
async def create_task_message(
    task_id: str,
    request: Request,
    body: Optional[str] = Form(None),
    mentions: Optional[str] = Form(None),
    # FastAPI + Pydantic v2 does not always coerce a single uploaded file into a 1-item list.
    # Accept both shapes and normalize below.
    files: Union[UploadFile, List[UploadFile], None] = File(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    task = await Task.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await _require_task_chat_access(request, db, user, task)

    content = (body or "").strip()
    if not content and not files:
        raise HTTPException(status_code=400, detail="Message or files are required")

    mentions_list: List[str] = []
    if mentions:
        try:
            parsed = json.loads(mentions)
            if isinstance(parsed, list):
                mentions_list = [str(item) for item in parsed if item]
        except Exception:
            mentions_list = []

    message = TaskMessage(
        task_id=str(task.id),
        user_id=str(user.id),
        body=content or None,
        mentions=mentions_list,
        attachments=[],
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    message.user = user

    files_list: List[UploadFile] = []
    if files:
        files_list = files if isinstance(files, list) else [files]

    attachments_payload = []
    if files_list:
        if not storage_available():
            raise HTTPException(status_code=500, detail="Storage is not configured")
        root = settings.STORAGE_LOCAL_ROOT or "/"
        base_path = f"{root.rstrip('/')}/_task_chat/{task.id}/{message.id}"
        await ensure_path(base_path)
        max_bytes = min(settings.UPLOAD_TMP_MAX_BYTES or MAX_TASK_CHAT_FILE_BYTES, MAX_TASK_CHAT_FILE_BYTES)
        for upload in files_list:
            if not upload or not upload.filename:
                continue
            data = await upload.read()
            if max_bytes and len(data) > max_bytes:
                raise HTTPException(status_code=413, detail="File too large")
            safe_name = clean_name(upload.filename)
            file_path = f"{base_path.rstrip('/')}/{safe_name}"
            await upload_bytes_with_safe_extension(file_path, data)
            attachments_payload.append(
                {
                    "name": safe_name,
                    "path": file_path,
                    "size": len(data),
                    "content_type": upload.content_type,
                }
            )
        if attachments_payload:
            message.attachments = attachments_payload
            await db.commit()
            await db.refresh(message)

    # Notifications: assigned user + mentions
    try:
        notify_targets = set()
        if task.assigned_to_user_id and str(task.assigned_to_user_id) != str(user.id):
            notify_targets.add(str(task.assigned_to_user_id))
        for mentioned in mentions_list:
            if mentioned and str(mentioned) != str(user.id):
                notify_targets.add(str(mentioned))
        for target_id in notify_targets:
            await create_notification(
                db,
                user_id=target_id,
                title="Новое сообщение в задаче",
                message=content[:200] if content else "Добавлены файлы",
                type="info",
                entity_type="task",
                entity_id=str(task.id),
                action_url=f"/tasks?task_id={task.id}",
            )
    except Exception:
        pass

    # Reload with user relation
    # AsyncSession.get(..., options=...) isn't reliable across SQLAlchemy versions; use SELECT + joinedload.
    result = await db.execute(
        select(TaskMessage).where(TaskMessage.id == message.id).options(joinedload(TaskMessage.user))
    )
    loaded = result.scalar_one_or_none()
    if loaded is None:
        return _serialize_message(message)
    return _serialize_message(loaded)


@router.patch("/tasks/messages/{message_id}", response_model=TaskMessageResponse)
async def update_task_message(
    message_id: str,
    payload: TaskMessageUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    message = await db.get(TaskMessage, message_id, options=[joinedload(TaskMessage.user)])
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    task = await Task.get_by_id(db, message.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await _require_task_chat_access(request, db, user, task)
    if str(message.user_id) != str(user.id) and not _is_admin(request):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if message.is_deleted:
        raise HTTPException(status_code=400, detail="Message deleted")

    body = (payload.body or "").strip()
    if not body:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    message.body = body
    message.edited_at = datetime.utcnow()
    await db.commit()
    await db.refresh(message)
    return _serialize_message(message)


@router.delete("/tasks/messages/{message_id}")
async def delete_task_message(
    message_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    message = await db.get(TaskMessage, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    task = await Task.get_by_id(db, message.task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await _require_task_chat_access(request, db, user, task)
    if str(message.user_id) != str(user.id) and not _is_admin(request):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if message.is_deleted:
        return {"deleted": True}
    message.is_deleted = True
    message.deleted_at = datetime.utcnow()
    await db.commit()
    return {"deleted": True}


# ── Chat unread counters / read-markers ─────────────────────────────
# Используется в Tasks.vue (список + канбан): рядом со статус-точкой
# задачи показываем «бейдж» с числом непрочитанных сообщений ОТ ДРУГИХ
# юзеров. При открытии модалки задачи фронт зовёт mark-read, и счётчик
# обнуляется.

@router.get("/tasks/chat/unread-counts")
async def list_chat_unread_counts(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
) -> Dict[str, int]:
    """Возвращает {task_id: count} непрочитанных сообщений от других
    юзеров. Видимость должна совпадать с видимостью списка задач —
    иначе юзер вроде задачу видит, но её бейджа в списке нет.

    Логика:
    - superuser или `tasks.read_all` → считаем по ВСЕМ задачам;
    - иначе → ограничиваем 4-мя ролями (assignee/creator/multi-assignee
      /watcher), это и privacy, и быстрее.

    Раньше always фильтровали по 4 ролям — у админа, не записанного в
    задачу явно, бейдж в списке был 0 даже при свежем сообщении.
    """
    user_id = str(user.id)

    # Проверка broad-доступа. is_superuser ставится auth-middleware'ом
    # из user.is_superuser. read_all берём из секции `tasks`, чтобы
    # совпадать с гард-логикой роутера задач.
    is_super = bool(getattr(request.state, "is_superuser", False))
    tasks_read_all = False
    if not is_super:
        ra, _ = await get_section_permissions(db, user.role_id, "tasks")
        tasks_read_all = bool(ra)
    broad_scope = is_super or tasks_read_all

    task_ids: Optional[set[str]] = None
    if not broad_scope:
        # Узкий скоп — собираем множество task_id, к которым юзер
        # явно привязан. Раньше это был единственный путь.
        task_ids = set()

        rows = await db.execute(
            select(Task.id).where(
                or_(
                    Task.assigned_to_user_id == user_id,
                    Task.created_by_user_id == user_id,
                )
            )
        )
        for (tid,) in rows.all():
            task_ids.add(str(tid))

        rows = await db.execute(
            select(TaskAssignee.task_id).where(TaskAssignee.user_id == user_id)
        )
        for (tid,) in rows.all():
            task_ids.add(str(tid))

        try:
            rows = await db.execute(
                select(TaskWatcher.task_id).where(TaskWatcher.user_id == user_id)
            )
            for (tid,) in rows.all():
                task_ids.add(str(tid))
        except Exception:  # pragma: no cover — таблица всегда есть
            pass

        if not task_ids:
            return {}

    # last_read_at по всем релевантным записям пользователя.
    if task_ids is None:
        reads_rows = await db.execute(
            select(TaskRead.task_id, TaskRead.last_read_at).where(TaskRead.user_id == user_id)
        )
    else:
        reads_rows = await db.execute(
            select(TaskRead.task_id, TaskRead.last_read_at).where(
                and_(TaskRead.user_id == user_id, TaskRead.task_id.in_(task_ids))
            )
        )
    reads: Dict[str, datetime] = {str(tid): ts for tid, ts in reads_rows.all()}

    # Сообщения от других юзеров; в узком скопе ограничиваем по task_ids.
    base_filter = and_(
        TaskMessage.user_id != user_id,
        TaskMessage.is_deleted.is_(False),
    )
    if task_ids is None:
        msg_rows = await db.execute(
            select(TaskMessage.task_id, TaskMessage.created_at, TaskMessage.user_id).where(
                base_filter
            )
        )
    else:
        msg_rows = await db.execute(
            select(TaskMessage.task_id, TaskMessage.created_at, TaskMessage.user_id).where(
                and_(base_filter, TaskMessage.task_id.in_(task_ids))
            )
        )

    counts: Dict[str, int] = {}
    for tid, created_at, _author_id in msg_rows.all():
        tid_str = str(tid)
        cutoff = reads.get(tid_str)
        if cutoff is not None and created_at is not None and created_at <= cutoff:
            continue
        counts[tid_str] = counts.get(tid_str, 0) + 1
    return counts


@router.post("/tasks/{task_id}/chat/mark-read")
async def mark_task_chat_read(
    task_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Обнуляет непрочитанный счётчик: ставит last_read_at = сейчас.

    Делает UPSERT по (user_id, task_id). Если строки нет — создаёт, если
    есть — обновляет timestamp. Доступ требует прав на чтение чата
    задачи (тот же гард, что и просмотр сообщений).
    """
    task = await Task.get_by_id(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await _require_task_chat_access(request, db, user, task)

    user_id = str(user.id)
    task_id_str = str(task.id)

    existing = await db.execute(
        select(TaskRead).where(
            and_(TaskRead.user_id == user_id, TaskRead.task_id == task_id_str)
        )
    )
    row = existing.scalar_one_or_none()
    now = datetime.utcnow()
    if row is None:
        row = TaskRead(user_id=user_id, task_id=task_id_str, last_read_at=now)
        db.add(row)
    else:
        row.last_read_at = now
    await db.commit()
    return {"task_id": task_id_str, "last_read_at": now.isoformat()}

