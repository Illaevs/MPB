"""
Task chat/messages endpoints.
"""
import json
from datetime import datetime
from typing import List, Optional, Union
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_middleware import CurrentUser
from app.core.config import settings
from app.database.session import get_db
from app.models import Task, TaskMessage, User
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

