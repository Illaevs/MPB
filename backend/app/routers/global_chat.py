"""
Messenger and global chat endpoints.
"""
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.core.auth_middleware import CurrentUser
from app.core.config import settings
from app.database.session import get_db
from app.models import (
    ChatConversation,
    ChatConversationMember,
    ChatMessageReaction,
    Deal,
    GlobalChatMessage,
    RolePermission,
    Task,
    TaskAssignee,
    User,
)
from app.schemas.chat import (
    ChatConversationCreate,
    ChatConversationDirectCreate,
    ChatConversationMemberAdd,
    ChatConversationMemberResponse,
    ChatConversationResponse,
    ChatConversationStateUpdate,
    ChatConversationUpdate,
    ChatMessageReferenceResponse,
    MentionItem,
    MessageReactionAggregate,
    ReactionToggleRequest,
    SearchableUserResponse,
)
from app.services.permissions import get_section_permissions
from app.schemas.global_chat_message import GlobalChatMessageResponse, GlobalChatMessageUpdate
from app.services.notifications import create_notification
from app.services.storage import (
    clean_name,
    ensure_path,
    storage_available,
    upload_bytes_with_safe_extension,
)


router = APIRouter()

MAX_CHAT_FILE_BYTES = 50 * 1024 * 1024
MANAGEABLE_CONVERSATION_TYPES = {"group", "channel"}

# Phase B.5 — rate-limit anti-spam.
# Окно 60 секунд, лимит 5 «первых сообщений незнакомцам». В памяти
# процесса (per-worker; для multi-worker нужен Redis — Stage E).
# «Первое сообщение» = я отправляю в DM, в котором ещё нет моих
# предыдущих сообщений.
import time as _time_module  # noqa: E402

_FIRST_MSG_WINDOW_SEC = 60
_FIRST_MSG_LIMIT = 5
_first_msg_recents: Dict[str, List[float]] = {}


def _trim_old_first_msg_ts(user_id: str, now: float) -> None:
    """Удаляет старые timestamp'ы (< now - window) из ring buffer'а."""
    cutoff = now - _FIRST_MSG_WINDOW_SEC
    arr = _first_msg_recents.get(user_id, [])
    if not arr:
        return
    # отсечь головной хвост старых
    while arr and arr[0] < cutoff:
        arr.pop(0)
    if arr:
        _first_msg_recents[user_id] = arr
    else:
        _first_msg_recents.pop(user_id, None)


async def _enforce_first_msg_rate_limit(
    db: AsyncSession,
    user_id: str,
    conversation: ChatConversation,
) -> None:
    """Срабатывает на отправке сообщения в DM, в котором у юзера ещё
    нет своих сообщений. Если за последние 60с уже было ≥5 таких
    «первых» — 429.
    """
    if conversation.type != "direct":
        return
    # Есть ли у меня уже сообщения в этом DM?
    prior = (
        await db.execute(
            select(func.count(GlobalChatMessage.id)).where(
                GlobalChatMessage.conversation_id == str(conversation.id),
                GlobalChatMessage.user_id == str(user_id),
            )
        )
    ).scalar() or 0
    if prior > 0:
        return  # уже не «первое»

    now = _time_module.time()
    _trim_old_first_msg_ts(str(user_id), now)
    recent = _first_msg_recents.setdefault(str(user_id), [])
    if len(recent) >= _FIRST_MSG_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Слишком много новых чатов за короткое время "
                f"(лимит {_FIRST_MSG_LIMIT} за {_FIRST_MSG_WINDOW_SEC}с). "
                f"Подождите минуту."
            ),
        )
    recent.append(now)
MESSAGE_LOAD_OPTIONS = [
    joinedload(GlobalChatMessage.user),
    joinedload(GlobalChatMessage.pinned_by),
    joinedload(GlobalChatMessage.reply_to_message).joinedload(GlobalChatMessage.user),
    joinedload(GlobalChatMessage.forwarded_from_message).joinedload(GlobalChatMessage.user),
]
CONVERSATION_LOAD_OPTIONS = [
    selectinload(ChatConversation.members).joinedload(ChatConversationMember.user),
    joinedload(ChatConversation.creator),
]


def _download_url(path: str) -> str:
    return f"/api/v1/storage/download?path={quote(path, safe='')}"


def _utcnow() -> datetime:
    return datetime.utcnow()


def _is_admin(request: Request) -> bool:
    if getattr(request.state, "is_superuser", False):
        return True
    role = getattr(request.state, "role", None)
    name = (getattr(role, "name", "") or "").lower()
    return "admin" in name or "админ" in name or "администратор" in name


def _format_member_count(count: int) -> str:
    mod10 = count % 10
    mod100 = count % 100
    if mod10 == 1 and mod100 != 11:
        word = "участник"
    elif mod10 in {2, 3, 4} and mod100 not in {12, 13, 14}:
        word = "участника"
    else:
        word = "участников"
    return f"{count} {word}"


async def _require_chat_access(
    request: Request,
    db: AsyncSession,
    user: User,
) -> None:
    if getattr(request.state, "is_superuser", False):
        return
    if not user or not user.role_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.role_id == str(user.role_id),
            RolePermission.section == "global_chat",
        )
    )
    perm = result.scalar_one_or_none()
    if perm is None:
        return
    if not (perm.read_all or perm.read_assigned):
        raise HTTPException(status_code=403, detail="Not enough permissions")


def _build_attachment_payload(item: Dict) -> Optional[Dict]:
    if not isinstance(item, dict):
        return None
    payload = dict(item)
    if payload.get("path"):
        payload["download_url"] = _download_url(payload["path"])
    return payload


def _serialize_message_reference(message: Optional[GlobalChatMessage]) -> Optional[ChatMessageReferenceResponse]:
    if not message:
        return None
    attachments = []
    if not message.is_deleted:
        for item in message.attachments or []:
            payload = _build_attachment_payload(item)
            if payload:
                attachments.append(payload)
    user_obj = message.__dict__.get("user")
    return ChatMessageReferenceResponse(
        id=str(message.id),
        user_id=str(message.user_id) if message.user_id else None,
        user_name=getattr(user_obj, "full_name", None),
        body=None if message.is_deleted else message.body,
        attachments=attachments,
        is_deleted=bool(message.is_deleted),
        created_at=message.created_at,
    )


def _serialize_message(
    message: GlobalChatMessage,
    reactions: Optional[List[MessageReactionAggregate]] = None,
) -> GlobalChatMessageResponse:
    attachments = []
    if not message.is_deleted:
        for item in message.attachments or []:
            payload = _build_attachment_payload(item)
            if payload:
                attachments.append(payload)
    user_obj = message.__dict__.get("user")
    return GlobalChatMessageResponse(
        id=str(message.id),
        user_id=str(message.user_id),
        user_name=getattr(user_obj, "full_name", None),
        conversation_id=str(message.conversation_id) if message.conversation_id else None,
        body=None if message.is_deleted else message.body,
        attachments=attachments,
        mentions=message.mentions or [],
        is_deleted=bool(message.is_deleted),
        is_pinned=bool(message.is_pinned),
        pinned_at=message.pinned_at,
        pinned_by_user_id=str(message.pinned_by_user_id) if message.pinned_by_user_id else None,
        reply_to_message=_serialize_message_reference(message.__dict__.get("reply_to_message")),
        forwarded_from_message=_serialize_message_reference(message.__dict__.get("forwarded_from_message")),
        reactions=reactions or [],
        created_at=message.created_at,
        updated_at=message.updated_at,
        edited_at=message.edited_at,
        deleted_at=message.deleted_at,
    )


# Phase B.3: batch-загрузка реакций для списка сообщений.
async def _load_reactions_map(
    db: AsyncSession,
    message_ids: List[str],
    current_user_id: str,
) -> Dict[str, List[MessageReactionAggregate]]:
    """Один SQL на весь список сообщений → группировка в Python.

    Возврат: {message_id: [MessageReactionAggregate, ...]}
    Каждый агрегат — по уникальной emoji-метке внутри одного сообщения,
    с count, user_ids и флагом reacted_by_me.
    """
    if not message_ids:
        return {}
    result = await db.execute(
        select(ChatMessageReaction).where(
            ChatMessageReaction.message_id.in_([str(m) for m in message_ids])
        )
    )
    rows = result.scalars().all()
    # group by (message_id, emoji)
    grouped: Dict[str, Dict[str, MessageReactionAggregate]] = {}
    me = str(current_user_id)
    for r in rows:
        mid = str(r.message_id)
        emoji = r.emoji
        bucket = grouped.setdefault(mid, {})
        agg = bucket.get(emoji)
        if agg is None:
            agg = MessageReactionAggregate(emoji=emoji, count=0, user_ids=[])
            bucket[emoji] = agg
        agg.count += 1
        agg.user_ids.append(str(r.user_id))
        if str(r.user_id) == me:
            agg.reacted_by_me = True
    return {mid: list(bucket.values()) for mid, bucket in grouped.items()}


def _serialize_member(user: User, role: str = "member", joined_at=None) -> ChatConversationMemberResponse:
    return ChatConversationMemberResponse(
        id=f"{user.id}:{role}",
        user_id=str(user.id),
        user_name=user.full_name or user.email or "Пользователь",
        user_email=user.email,
        role=role,
        joined_at=joined_at,
    )


def _conversation_member_lookup(conversation: ChatConversation) -> Dict[str, ChatConversationMember]:
    return {str(member.user_id): member for member in conversation.members or []}


# Дата-«никогда»: используется для muted_forever. SQLite спокойно ест
# datetime до 9999, JSON-сериализация тоже.
_FOREVER = datetime(9999, 12, 31, 23, 59, 59)


def _is_muted_now(member: Optional[ChatConversationMember]) -> bool:
    """Активен ли mute прямо сейчас (для UI badge / push gate)."""
    if not member or member.muted_until is None:
        return False
    try:
        return member.muted_until > _utcnow()
    except TypeError:
        # tz mismatch (naive vs aware) — на всякий случай считаем
        # mute активным, лучше тише чем громче.
        return True


async def _unread_count_for_member(
    db: AsyncSession,
    conversation_id: str,
    user_id: str,
    last_read_at: Optional[datetime],
) -> int:
    """Сколько сообщений ОТ ДРУГИХ юзеров приехало после last_read_at.

    Свои собственные не считаем — они для UI всегда «прочитаны».
    Удалённые (is_deleted=True) тоже не показываем — это soft-delete,
    в badge их учитывать смысла нет.
    """
    stmt = (
        select(func.count(GlobalChatMessage.id))
        .where(
            GlobalChatMessage.conversation_id == str(conversation_id),
            GlobalChatMessage.is_deleted == False,  # noqa: E712
            GlobalChatMessage.user_id != str(user_id),
        )
    )
    if last_read_at is not None:
        stmt = stmt.where(GlobalChatMessage.created_at > last_read_at)
    result = await db.execute(stmt)
    return int(result.scalar() or 0)


async def _conversation_has_messages(
    db: AsyncSession,
    conversation_id: str,
) -> bool:
    """Используется для фильтрации «пустых» DM — чтобы открытый-и-не-
    написанный чат не светился у второго участника в списке.
    """
    stmt = (
        select(func.count(GlobalChatMessage.id))
        .where(GlobalChatMessage.conversation_id == str(conversation_id))
        .limit(1)
    )
    result = await db.execute(stmt)
    return int(result.scalar() or 0) > 0


def _conversation_manage_allowed(request: Request, user: User, conversation: ChatConversation) -> bool:
    if _is_admin(request):
        return True
    if conversation.type not in MANAGEABLE_CONVERSATION_TYPES:
        return False
    member = _conversation_member_lookup(conversation).get(str(user.id))
    if not member:
        return False
    return member.role in {"owner", "admin"} or str(conversation.created_by_user_id or "") == str(user.id)


async def _get_all_active_users(db: AsyncSession) -> List[User]:
    result = await db.execute(select(User).where(User.is_active == True).order_by(User.full_name.asc()))
    return result.scalars().all()


async def _ensure_global_conversation(db: AsyncSession, user: Optional[User] = None) -> ChatConversation:
    result = await db.execute(
        select(ChatConversation)
        .where(ChatConversation.type == "global")
        .options(*CONVERSATION_LOAD_OPTIONS)
        .order_by(ChatConversation.created_at.asc())
        .limit(1)
    )
    conversation = result.scalars().first()
    if conversation:
        updated = False
        if not conversation.title or conversation.title == "Global Chat":
            conversation.title = "Глобальный чат"
            updated = True
        if not conversation.description or conversation.description == "Company-wide conversation":
            conversation.description = "Общий чат компании"
            updated = True
        if updated:
            await db.commit()
            await db.refresh(conversation)
        return conversation

    creator_id = str(user.id) if user and getattr(user, "id", None) else None
    conversation = ChatConversation(
        type="global",
        title="Глобальный чат",
        description="Общий чат компании",
        created_by_user_id=creator_id,
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    result = await db.execute(
        select(ChatConversation)
        .where(ChatConversation.id == conversation.id)
        .options(*CONVERSATION_LOAD_OPTIONS)
    )
    return result.scalars().one()


async def _get_conversation(
    db: AsyncSession,
    conversation_id: str,
) -> Optional[ChatConversation]:
    result = await db.execute(
        select(ChatConversation)
        .where(ChatConversation.id == conversation_id, ChatConversation.is_archived == False)
        .options(*CONVERSATION_LOAD_OPTIONS)
    )
    return result.scalars().first()


async def _require_conversation_access(
    request: Request,
    db: AsyncSession,
    user: User,
    conversation: ChatConversation,
) -> None:
    await _require_chat_access(request, db, user)
    if conversation.type == "global":
        return
    lookup = _conversation_member_lookup(conversation)
    is_member = str(user.id) in lookup
    if conversation.type == "direct" and not is_member:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if _is_admin(request):
        return
    if not is_member:
        raise HTTPException(status_code=403, detail="Not enough permissions")


async def _resolve_conversation_members(
    db: AsyncSession,
    conversation: ChatConversation,
) -> List[ChatConversationMemberResponse]:
    if conversation.type == "global":
        users = await _get_all_active_users(db)
        return [_serialize_member(item) for item in users]

    members = []
    for member in conversation.members or []:
        if not member.user:
            continue
        members.append(_serialize_member(member.user, member.role, member.joined_at))
    members.sort(key=lambda item: item.user_name.lower())
    return members


async def _conversation_last_and_pinned(
    db: AsyncSession,
    conversation_id: str,
) -> Tuple[Optional[GlobalChatMessage], Optional[GlobalChatMessage]]:
    latest_result = await db.execute(
        select(GlobalChatMessage)
        .where(GlobalChatMessage.conversation_id == conversation_id)
        .options(*MESSAGE_LOAD_OPTIONS)
        .order_by(GlobalChatMessage.created_at.desc())
        .limit(1)
    )
    pinned_result = await db.execute(
        select(GlobalChatMessage)
        .where(
            GlobalChatMessage.conversation_id == conversation_id,
            GlobalChatMessage.is_deleted == False,
            GlobalChatMessage.is_pinned == True,
        )
        .options(*MESSAGE_LOAD_OPTIONS)
        .order_by(GlobalChatMessage.pinned_at.desc(), GlobalChatMessage.created_at.desc())
        .limit(1)
    )
    return latest_result.scalars().first(), pinned_result.scalars().first()


def _conversation_display_title(
    conversation: ChatConversation,
    current_user_id: str,
    members: List[ChatConversationMemberResponse],
) -> str:
    if conversation.type == "direct":
        for member in members:
            if str(member.user_id) != str(current_user_id):
                return member.user_name
        return members[0].user_name if members else "Личный чат"
    if conversation.title:
        return conversation.title
    if conversation.type == "channel":
        return "Канал"
    return "Чат"


def _conversation_description(
    conversation: ChatConversation,
    current_user_id: str,
    members: List[ChatConversationMemberResponse],
) -> Optional[str]:
    if conversation.type == "direct":
        for member in members:
            if str(member.user_id) != str(current_user_id):
                return member.user_email or None
        return None
    if conversation.description:
        return conversation.description
    member_count = len(members)
    return _format_member_count(member_count)


async def _serialize_conversation(
    request: Request,
    db: AsyncSession,
    user: User,
    conversation: ChatConversation,
) -> ChatConversationResponse:
    members = await _resolve_conversation_members(db, conversation)
    last_message, pinned_message = await _conversation_last_and_pinned(db, conversation.id)
    title = _conversation_display_title(conversation, str(user.id), members)
    description = _conversation_description(conversation, str(user.id), members)

    # Per-user state. global чат не имеет member-строк (виртуальный
    # список), поэтому для него отдаём нули — unread по global пока
    # не считаем (отдельная задача, требует «last_read глобалки» per user).
    member_lookup_data = _conversation_member_lookup(conversation)
    my_member = member_lookup_data.get(str(user.id))
    peer_last_read_at: Optional[datetime] = None

    if conversation.type == "global" or my_member is None:
        unread = 0
        is_archived = False
        muted_until = None
        last_read_at = None
        is_pinned = False
    else:
        last_read_at = my_member.last_read_at
        unread = await _unread_count_for_member(
            db, str(conversation.id), str(user.id), last_read_at
        )
        is_archived = bool(my_member.is_archived)
        muted_until = my_member.muted_until
        is_pinned = bool(getattr(my_member, "is_pinned", False))

        # Phase B.2: для DM-чатов берём last_read_at второго участника.
        # Фронт сравнит его с created_at МОИХ сообщений → ✓ vs ✓✓.
        if conversation.type == "direct":
            for member in conversation.members or []:
                if str(member.user_id) != str(user.id):
                    peer_last_read_at = member.last_read_at
                    break

    return ChatConversationResponse(
        id=str(conversation.id),
        type=conversation.type,
        title=title,
        description=description,
        member_count=len(members),
        can_manage_members=_conversation_manage_allowed(request, user, conversation),
        members=members,
        last_message=_serialize_message_reference(last_message),
        pinned_message=_serialize_message_reference(pinned_message),
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        unread_count=unread,
        is_archived=is_archived,
        muted_until=muted_until,
        last_read_at=last_read_at,
        is_pinned=is_pinned,
        peer_last_read_at=peer_last_read_at,
    )


async def _list_visible_conversations(
    request: Request,
    db: AsyncSession,
    user: User,
    include_archived: bool = False,
) -> List[ChatConversation]:
    """Список conversations, видимых текущему юзеру.

    Stage 1 правила фильтрации:
      - Глобальный чат — всегда.
      - DM:
          * только если я участник;
          * только если в чате есть хотя бы 1 сообщение (пустые DM
            не светятся; см. UX в плане messenger-implicit-dm);
          * если у меня is_archived=True — скрываем (если только
            include_archived не запрошен явно).
      - Group/channel:
          * только если я участник или админ;
          * скрытие по моему is_archived аналогично.
    """
    await _require_chat_access(request, db, user)
    global_conversation = await _ensure_global_conversation(db, user)

    result = await db.execute(
        select(ChatConversation)
        .where(ChatConversation.is_archived == False)  # noqa: E712 — глобальный архив чата
        .options(*CONVERSATION_LOAD_OPTIONS)
        .order_by(ChatConversation.created_at.asc())
    )
    conversations = result.scalars().unique().all()
    lookup = {}
    direct_lookup: Dict[str, ChatConversation] = {}

    def _conversation_rank(item: ChatConversation) -> Tuple[datetime, datetime]:
        return (
            item.updated_at or item.created_at or datetime.min,
            item.created_at or datetime.min,
        )

    for conversation in conversations:
        if conversation.type == "global":
            lookup[str(conversation.id)] = conversation
            continue
        member_lookup = _conversation_member_lookup(conversation)
        my_member = member_lookup.get(str(user.id))
        is_member = my_member is not None
        # Per-user archive filter.
        if my_member and my_member.is_archived and not include_archived:
            continue
        if conversation.type == "direct":
            if not is_member:
                continue
            # Пустой DM (без сообщений) НЕ светится для собеседника —
            # «я открыл и не написал» не должно создавать карточку у
            # второго участника. Создателю чат остаётся виден сразу
            # (иначе после клика «написать коллеге» получишь пустой
            # экран — DM в БД есть, но в списке нет).
            has_msg = await _conversation_has_messages(db, str(conversation.id))
            if not has_msg and str(conversation.created_by_user_id) != str(user.id):
                continue
            member_ids = sorted(str(member.user_id) for member in conversation.members or [])
            peer_ids = [member_id for member_id in member_ids if member_id != str(user.id)]
            direct_key = peer_ids[0] if peer_ids else str(conversation.id)
            current = direct_lookup.get(direct_key)
            if not current or _conversation_rank(conversation) > _conversation_rank(current):
                direct_lookup[direct_key] = conversation
            continue
        if _is_admin(request) or is_member:
            lookup[str(conversation.id)] = conversation

    for conversation in direct_lookup.values():
        lookup[str(conversation.id)] = conversation
    lookup[str(global_conversation.id)] = global_conversation
    return list(lookup.values())


async def _get_message(
    db: AsyncSession,
    message_id: str,
) -> Optional[GlobalChatMessage]:
    result = await db.execute(
        select(GlobalChatMessage)
        .where(GlobalChatMessage.id == message_id)
        .options(*MESSAGE_LOAD_OPTIONS)
    )
    return result.scalars().first()


async def _load_conversation_messages(
    db: AsyncSession,
    conversation_id: str,
    skip: int = 0,
    limit: int = 500,
) -> List[GlobalChatMessage]:
    result = await db.execute(
        select(GlobalChatMessage)
        .where(GlobalChatMessage.conversation_id == conversation_id)
        .options(*MESSAGE_LOAD_OPTIONS)
        .order_by(GlobalChatMessage.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


def _parse_mentions(mentions: Optional[str]) -> List[str]:
    mentions_list: List[str] = []
    if not mentions:
        return mentions_list
    try:
        parsed = json.loads(mentions)
        if isinstance(parsed, list):
            mentions_list = [str(item) for item in parsed if item]
    except Exception:
        mentions_list = []
    return mentions_list


async def _store_attachments(
    conversation_id: str,
    message_id: str,
    files: List[UploadFile],
) -> List[Dict]:
    if not files:
        return []
    if not storage_available():
        raise HTTPException(status_code=500, detail="Storage is not configured")

    root = settings.STORAGE_LOCAL_ROOT or "/"
    base_path = f"{root.rstrip('/')}/_chat/{conversation_id}/{message_id}"
    await ensure_path(base_path)

    attachments_payload = []
    limit_bytes = min(settings.UPLOAD_TMP_MAX_BYTES or MAX_CHAT_FILE_BYTES, MAX_CHAT_FILE_BYTES)
    for upload in files:
        if not upload or not upload.filename:
            continue
        data = await upload.read()
        if limit_bytes and len(data) > limit_bytes:
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
    return attachments_payload


async def _parse_message_form(
    request: Request,
) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str], List[UploadFile]]:
    form = await request.form()
    files: List[UploadFile] = []
    for item in form.getlist("files"):
        if isinstance(item, StarletteUploadFile) and item.filename:
            files.append(item)
    return (
        form.get("body"),
        form.get("mentions"),
        form.get("reply_to_message_id"),
        form.get("forwarded_from_message_id"),
        files,
    )


async def _notify_global_chat(
    db: AsyncSession,
    author: User,
    message: GlobalChatMessage,
) -> None:
    content = (message.body or "").strip()
    result = await db.execute(select(User).where(User.is_active == True))
    users = result.scalars().all()
    for target in users:
        if not target or str(target.id) == str(author.id):
            continue
        await create_notification(
            db,
            user_id=str(target.id),
            title="Новое сообщение в глобальном чате",
            message=content[:200] if content else "Добавлены файлы",
            type="info",
            entity_type="global_chat",
            entity_id=str(message.id),
            action_url="/messenger",
        )


async def _create_message(
    request: Request,
    db: AsyncSession,
    user: User,
    conversation: ChatConversation,
    body: Optional[str],
    mentions: Optional[str],
    files: Optional[List[UploadFile]],
    reply_to_message_id: Optional[str] = None,
    forwarded_from_message_id: Optional[str] = None,
) -> GlobalChatMessage:
    await _require_conversation_access(request, db, user, conversation)

    reply_to_message = None
    if reply_to_message_id:
        reply_to_message = await _get_message(db, reply_to_message_id)
        if not reply_to_message or str(reply_to_message.conversation_id) != str(conversation.id):
            raise HTTPException(status_code=404, detail="Reply target not found")

    forwarded_from_message = None
    if forwarded_from_message_id:
        forwarded_from_message = await _get_message(db, forwarded_from_message_id)
        if not forwarded_from_message:
            raise HTTPException(status_code=404, detail="Forwarded message not found")
        forwarded_conversation = await _get_conversation(db, str(forwarded_from_message.conversation_id))
        if not forwarded_conversation:
            raise HTTPException(status_code=404, detail="Forwarded message conversation not found")
        await _require_conversation_access(request, db, user, forwarded_conversation)

    content = (body or "").strip()
    files_list = list(files or [])

    if not content and not files_list and not forwarded_from_message:
        raise HTTPException(status_code=400, detail="Message, forward target or files are required")

    # Phase B.5: anti-spam — rate-limit на «первое сообщение незнакомцу».
    # Срабатывает ТОЛЬКО на DM (group/channel/global не трогаем).
    await _enforce_first_msg_rate_limit(db, str(user.id), conversation)

    message = GlobalChatMessage(
        user_id=str(user.id),
        conversation_id=str(conversation.id),
        body=content or None,
        mentions=_parse_mentions(mentions),
        attachments=[],
        reply_to_message_id=str(reply_to_message.id) if reply_to_message else None,
        forwarded_from_message_id=str(forwarded_from_message.id) if forwarded_from_message else None,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    attachments_payload = await _store_attachments(str(conversation.id), str(message.id), files_list)
    if attachments_payload:
        message.attachments = attachments_payload
        await db.commit()
        await db.refresh(message)

    if conversation.type == "global":
        await _notify_global_chat(db, user, message)
        await db.commit()

    loaded = await _get_message(db, str(message.id))
    if not loaded:
        raise HTTPException(status_code=500, detail="Unable to load created message")
    return loaded


async def _find_direct_conversation(
    db: AsyncSession,
    left_user_id: str,
    right_user_id: str,
) -> Optional[ChatConversation]:
    result = await db.execute(
        select(ChatConversation)
        .where(ChatConversation.type == "direct", ChatConversation.is_archived == False)
        .options(*CONVERSATION_LOAD_OPTIONS)
    )
    conversations = result.scalars().unique().all()
    expected = {str(left_user_id), str(right_user_id)}
    matched: List[ChatConversation] = []
    for conversation in conversations:
        member_ids = {str(member.user_id) for member in conversation.members or []}
        if member_ids == expected:
            matched.append(conversation)
    if not matched:
        return None
    matched.sort(
        key=lambda item: (
            item.updated_at or item.created_at or datetime.min,
            item.created_at or datetime.min,
        ),
        reverse=True,
    )
    return matched[0]


@router.get("/conversations", response_model=List[ChatConversationResponse])
async def list_conversations(
    request: Request,
    include_archived: bool = False,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    conversations = await _list_visible_conversations(
        request, db, user, include_archived=include_archived
    )
    serialized = []
    for conversation in conversations:
        payload = await _serialize_conversation(request, db, user, conversation)
        last_message_at = payload.last_message.created_at if payload.last_message else None
        timestamp = last_message_at.timestamp() if last_message_at else 0
        # Sort buckets (Phase B.1):
        #   0 — global чат (всегда сверху)
        #   1 — мои закреплённые (per-user is_pinned)
        #   2 — всё остальное
        if conversation.type == "global":
            priority = 0
        elif payload.is_pinned:
            priority = 1
        else:
            priority = 2
        serialized.append((priority, -timestamp, payload.title.lower(), payload))
    serialized.sort(key=lambda item: (item[0], item[1], item[2]))
    return [item[3] for item in serialized]


@router.post("/conversations/direct", response_model=ChatConversationResponse)
async def create_or_open_direct_conversation(
    payload: ChatConversationDirectCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    await _require_chat_access(request, db, user)
    if str(payload.user_id) == str(user.id):
        raise HTTPException(status_code=400, detail="Cannot create direct chat with yourself")

    target_user = await db.get(User, str(payload.user_id))
    if not target_user or not target_user.is_active:
        raise HTTPException(status_code=404, detail="User not found")

    existing = await _find_direct_conversation(db, str(user.id), str(target_user.id))
    if existing:
        await _require_conversation_access(request, db, user, existing)
        # Open-from-archive: если я раньше архивировал этот чат, при
        # повторном открытии его снова покажем в списке. Архив второго
        # участника НЕ трогаем.
        my_member = _conversation_member_lookup(existing).get(str(user.id))
        if my_member is not None and my_member.is_archived:
            my_member.is_archived = False
            await db.commit()
        return await _serialize_conversation(request, db, user, existing)

    conversation = ChatConversation(
        type="direct",
        created_by_user_id=str(user.id),
    )
    db.add(conversation)
    await db.flush()
    db.add(ChatConversationMember(conversation_id=str(conversation.id), user_id=str(user.id), role="member"))
    db.add(ChatConversationMember(conversation_id=str(conversation.id), user_id=str(target_user.id), role="member"))
    await db.commit()

    loaded = await _get_conversation(db, str(conversation.id))
    if not loaded:
        raise HTTPException(status_code=500, detail="Unable to create conversation")
    return await _serialize_conversation(request, db, user, loaded)


@router.post("/conversations", response_model=ChatConversationResponse)
async def create_conversation(
    payload: ChatConversationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    await _require_chat_access(request, db, user)
    title = (payload.title or "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title is required")

    conversation = ChatConversation(
        type=payload.type,
        title=title,
        description=(payload.description or "").strip() or None,
        created_by_user_id=str(user.id),
    )
    db.add(conversation)
    await db.flush()

    unique_ids = []
    seen = {str(user.id)}
    for member_id in payload.member_ids or []:
        key = str(member_id)
        if not key or key in seen:
            continue
        seen.add(key)
        unique_ids.append(key)

    users_result = await db.execute(select(User).where(User.id.in_(unique_ids), User.is_active == True))
    target_users = users_result.scalars().all()

    db.add(ChatConversationMember(conversation_id=str(conversation.id), user_id=str(user.id), role="owner"))
    for target in target_users:
        db.add(ChatConversationMember(conversation_id=str(conversation.id), user_id=str(target.id), role="member"))

    await db.commit()
    loaded = await _get_conversation(db, str(conversation.id))
    if not loaded:
        raise HTTPException(status_code=500, detail="Unable to create conversation")
    return await _serialize_conversation(request, db, user, loaded)


@router.patch("/conversations/{conversation_id}", response_model=ChatConversationResponse)
async def update_conversation(
    conversation_id: str,
    payload: ChatConversationUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    conversation = await _get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await _require_conversation_access(request, db, user, conversation)
    if not _conversation_manage_allowed(request, user, conversation):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if payload.title is not None:
        title = payload.title.strip()
        if not title:
            raise HTTPException(status_code=400, detail="Title is required")
        conversation.title = title
    if payload.description is not None:
        conversation.description = payload.description.strip() or None
    conversation.updated_at = _utcnow()
    await db.commit()

    loaded = await _get_conversation(db, conversation_id)
    if not loaded:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return await _serialize_conversation(request, db, user, loaded)


@router.post("/conversations/{conversation_id}/members", response_model=ChatConversationResponse)
async def add_conversation_members(
    conversation_id: str,
    payload: ChatConversationMemberAdd,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    conversation = await _get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await _require_conversation_access(request, db, user, conversation)
    if not _conversation_manage_allowed(request, user, conversation):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if conversation.type not in MANAGEABLE_CONVERSATION_TYPES:
        raise HTTPException(status_code=400, detail="Member management is not available for this chat type")

    existing_ids = {str(member.user_id) for member in conversation.members or []}
    target_ids = []
    for member_id in payload.user_ids or []:
        key = str(member_id)
        if not key or key in existing_ids:
            continue
        existing_ids.add(key)
        target_ids.append(key)

    if target_ids:
        result = await db.execute(select(User).where(User.id.in_(target_ids), User.is_active == True))
        for target_user in result.scalars().all():
            db.add(
                ChatConversationMember(
                    conversation_id=str(conversation.id),
                    user_id=str(target_user.id),
                    role="member",
                )
            )
        conversation.updated_at = _utcnow()
        await db.commit()

    loaded = await _get_conversation(db, conversation_id)
    if not loaded:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return await _serialize_conversation(request, db, user, loaded)


@router.delete("/conversations/{conversation_id}/members/{member_user_id}", response_model=ChatConversationResponse)
async def remove_conversation_member(
    conversation_id: str,
    member_user_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    conversation = await _get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await _require_conversation_access(request, db, user, conversation)
    if conversation.type not in MANAGEABLE_CONVERSATION_TYPES:
        raise HTTPException(status_code=400, detail="Member management is not available for this chat type")

    if str(member_user_id) != str(user.id) and not _conversation_manage_allowed(request, user, conversation):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    member_lookup = _conversation_member_lookup(conversation)
    member = member_lookup.get(str(member_user_id))
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    await db.delete(member)
    conversation.updated_at = _utcnow()
    await db.commit()

    loaded = await _get_conversation(db, conversation_id)
    if not loaded:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return await _serialize_conversation(request, db, user, loaded)


@router.patch("/conversations/{conversation_id}/me", response_model=ChatConversationResponse)
async def update_my_conversation_state(
    conversation_id: str,
    payload: ChatConversationStateUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Per-user state: is_archived / muted_until.

    Глобальный чат не имеет member-строк (виртуальный список из всех
    активных), поэтому состояние для него настраивать нельзя — здесь
    отдаём 400. Если понадобится — нужно отдельное хранилище
    «global_chat_member_state».
    """
    conversation = await _get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if conversation.type == "global":
        raise HTTPException(
            status_code=400,
            detail="Global chat doesn't support per-user state in Stage 1",
        )

    await _require_conversation_access(request, db, user, conversation)
    my_member = _conversation_member_lookup(conversation).get(str(user.id))
    if my_member is None:
        raise HTTPException(status_code=403, detail="Not a conversation member")

    changed = False

    if payload.is_archived is not None:
        my_member.is_archived = bool(payload.is_archived)
        changed = True

    if payload.is_pinned is not None:
        my_member.is_pinned = bool(payload.is_pinned)
        changed = True

    # mute_logic:
    #   muted_forever=True  → ставим _FOREVER в muted_until.
    #   muted_forever=False → снимаем mute (None).
    #   muted_until=<dt>    → ставим конкретный дедлайн.
    #   muted_until=None И muted_forever=None → не меняем (sentinel).
    if payload.muted_forever is True:
        my_member.muted_until = _FOREVER
        changed = True
    elif payload.muted_forever is False:
        my_member.muted_until = None
        changed = True
    elif payload.muted_until is not None:
        my_member.muted_until = payload.muted_until
        changed = True

    if changed:
        await db.commit()

    loaded = await _get_conversation(db, conversation_id)
    if not loaded:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return await _serialize_conversation(request, db, user, loaded)


@router.get("/users/searchable", response_model=List[SearchableUserResponse])
async def list_searchable_users(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Все активные юзеры (кроме самого вызывающего) для поиска
    «написать коллеге». Помечает `has_dm=True`, если у нас уже есть
    direct chat — фронт показывает «уже есть чат» / «новый».
    """
    await _require_chat_access(request, db, user)

    # Все активные юзеры кроме меня.
    users_result = await db.execute(
        select(User)
        .where(User.is_active == True, User.id != str(user.id))  # noqa: E712
        .order_by(User.full_name.asc())
    )
    users_list = users_result.scalars().all()

    # Карта peer_user_id → conversation_id для моих DM.
    dm_lookup: Dict[str, str] = {}
    conv_result = await db.execute(
        select(ChatConversation)
        .where(
            ChatConversation.type == "direct",
            ChatConversation.is_archived == False,  # noqa: E712
        )
        .options(selectinload(ChatConversation.members))
    )
    for conv in conv_result.scalars().unique().all():
        member_ids = {str(m.user_id) for m in conv.members or []}
        if str(user.id) not in member_ids:
            continue
        for peer_id in member_ids - {str(user.id)}:
            dm_lookup[peer_id] = str(conv.id)

    return [
        SearchableUserResponse(
            id=str(u.id),
            full_name=u.full_name,
            email=u.email,
            avatar_url=getattr(u, "avatar_url", None),
            has_dm=str(u.id) in dm_lookup,
            dm_conversation_id=dm_lookup.get(str(u.id)),
        )
        for u in users_list
    ]


# ────────────────────────────────────────────────────────────────────
# Phase B.4 — mention сделок/задач/юзеров с ACL-фильтром
# ────────────────────────────────────────────────────────────────────


@router.get("/mention-search", response_model=List[MentionItem])
async def mention_search(
    request: Request,
    q: str = "",
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Объединённый поиск для @-меншенов в composer'е чата.

    Возвращает до 20 элементов разных типов (user/deal/task), отранжированных
    префиксом «совпадение по началу» → «содержит». ACL-фильтр:
      - users: все активные кроме меня
      - deals: superuser ИЛИ has read_all на «deals» ИЛИ created_by == me
      - tasks: superuser ИЛИ has read_all на «tasks» ИЛИ
               created_by == me ИЛИ я в task_assignees

    Минимальная длина q = 1. Пустой q возвращает [] (UI обычно ждёт
    хотя бы один символ).
    """
    await _require_chat_access(request, db, user)
    query = (q or "").strip()
    if not query:
        return []
    like = f"%{query}%"
    is_super = bool(getattr(request.state, "is_superuser", False))

    items: List[MentionItem] = []

    # --- Users (top 10) ---
    user_rows = (
        await db.execute(
            select(User)
            .where(
                User.is_active == True,  # noqa: E712
                User.id != str(user.id),
                (User.full_name.ilike(like)) | (User.email.ilike(like)),
            )
            .order_by(User.full_name.asc())
            .limit(10)
        )
    ).scalars().all()
    for u in user_rows:
        items.append(
            MentionItem(
                kind="user",
                id=str(u.id),
                label=u.full_name or u.email or str(u.id),
                sublabel=u.email if u.full_name else None,
                avatar_url=getattr(u, "avatar_url", None),
                href=None,
            )
        )

    # --- Deals (top 5) ---
    deals_read_all, _ = await get_section_permissions(db, user.role_id, "deals")
    deal_stmt = (
        select(Deal)
        .where(
            (Deal.title.ilike(like)) | (Deal.obj_name.ilike(like))
        )
        .order_by(Deal.created_at.desc())
        .limit(5)
    )
    if not is_super and not deals_read_all:
        deal_stmt = deal_stmt.where(Deal.created_by == str(user.id))
    deal_rows = (await db.execute(deal_stmt)).scalars().all()
    for d in deal_rows:
        title = d.title or d.obj_name or f"Сделка {str(d.id)[:8]}"
        items.append(
            MentionItem(
                kind="deal",
                id=str(d.id),
                label=title,
                sublabel=d.obj_name if d.obj_name and d.obj_name != title else None,
                avatar_url=None,
                href=f"/deals/{d.id}",
            )
        )

    # --- Tasks (top 5) ---
    tasks_read_all, _ = await get_section_permissions(db, user.role_id, "tasks")
    task_stmt = (
        select(Task)
        .where(Task.title.ilike(like))
        .order_by(Task.created_at.desc())
        .limit(5)
    )
    if not is_super and not tasks_read_all:
        # created_by == me OR me ∈ task_assignees
        my_assigned = select(TaskAssignee.task_id).where(
            TaskAssignee.user_id == str(user.id)
        )
        task_stmt = task_stmt.where(
            (Task.created_by == str(user.id)) | (Task.id.in_(my_assigned))
        )
    task_rows = (await db.execute(task_stmt)).scalars().all()
    for t in task_rows:
        items.append(
            MentionItem(
                kind="task",
                id=str(t.id),
                label=t.title or f"Задача {str(t.id)[:8]}",
                sublabel=None,
                avatar_url=None,
                href=f"/tasks/{t.id}",
            )
        )

    return items


@router.get("/conversations/{conversation_id}/messages", response_model=List[GlobalChatMessageResponse])
async def list_conversation_messages(
    conversation_id: str,
    request: Request,
    skip: int = 0,
    limit: int = 500,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    conversation = await _get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await _require_conversation_access(request, db, user, conversation)
    messages = await _load_conversation_messages(db, conversation_id, skip, limit)

    # Auto mark-read: открыли чат → обновляем last_read_at у моей
    # member-строки. Глобальный чат не имеет member-строк, скип.
    if conversation.type != "global":
        my_member = _conversation_member_lookup(conversation).get(str(user.id))
        if my_member is not None:
            my_member.last_read_at = _utcnow()
            await db.commit()

    # Phase B.3: batch-загрузка реакций ОДНИМ запросом на весь список.
    reactions_map = await _load_reactions_map(
        db, [str(m.id) for m in messages], str(user.id)
    )
    return [
        _serialize_message(message, reactions_map.get(str(message.id), []))
        for message in messages
    ]


@router.post("/conversations/{conversation_id}/messages", response_model=GlobalChatMessageResponse)
async def create_conversation_message(
    conversation_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    conversation = await _get_conversation(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    body, mentions, reply_to_message_id, forwarded_from_message_id, files = await _parse_message_form(request)
    message = await _create_message(
        request,
        db,
        user,
        conversation,
        body,
        mentions,
        files,
        reply_to_message_id=reply_to_message_id,
        forwarded_from_message_id=forwarded_from_message_id,
    )
    return _serialize_message(message)


@router.post("/messages/{message_id}/pin", response_model=GlobalChatMessageResponse)
async def pin_message(
    message_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    message = await _get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    if message.is_deleted:
        raise HTTPException(status_code=400, detail="Message deleted")

    conversation = await _get_conversation(db, str(message.conversation_id))
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await _require_conversation_access(request, db, user, conversation)

    result = await db.execute(
        select(GlobalChatMessage).where(
            GlobalChatMessage.conversation_id == str(conversation.id),
            GlobalChatMessage.is_pinned == True,
        )
    )
    for item in result.scalars().all():
        item.is_pinned = False
        item.pinned_at = None
        item.pinned_by_user_id = None

    message.is_pinned = True
    message.pinned_at = _utcnow()
    message.pinned_by_user_id = str(user.id)
    conversation.updated_at = _utcnow()
    await db.commit()

    loaded = await _get_message(db, message_id)
    if not loaded:
        raise HTTPException(status_code=404, detail="Message not found")
    return _serialize_message(loaded)


@router.delete("/messages/{message_id}/pin", response_model=GlobalChatMessageResponse)
async def unpin_message(
    message_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    message = await _get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    conversation = await _get_conversation(db, str(message.conversation_id))
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await _require_conversation_access(request, db, user, conversation)

    message.is_pinned = False
    message.pinned_at = None
    message.pinned_by_user_id = None
    conversation.updated_at = _utcnow()
    await db.commit()

    loaded = await _get_message(db, message_id)
    if not loaded:
        raise HTTPException(status_code=404, detail="Message not found")
    return _serialize_message(loaded)


# ────────────────────────────────────────────────────────────────────
# Phase B.3 — emoji reactions
# ────────────────────────────────────────────────────────────────────


@router.post("/messages/{message_id}/reactions", response_model=GlobalChatMessageResponse)
async def toggle_message_reaction(
    message_id: str,
    payload: ReactionToggleRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Idempotent toggle: если такой эмодзи от меня уже есть — снимаем,
    нет — ставим. Возвращает обновлённое сообщение целиком.

    Доступ: я должен иметь доступ к conversation сообщения
    (require_conversation_access). На удалённые сообщения не реагируем
    (400).
    """
    emoji = (payload.emoji or "").strip()
    if not emoji:
        raise HTTPException(status_code=400, detail="emoji is required")

    message = await _get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    if message.is_deleted:
        raise HTTPException(status_code=400, detail="Message is deleted")

    conversation = await _get_conversation(db, str(message.conversation_id))
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await _require_conversation_access(request, db, user, conversation)

    # Ищем существующую реакцию (me, emoji) на этом сообщении.
    existing = (
        await db.execute(
            select(ChatMessageReaction).where(
                ChatMessageReaction.message_id == str(message.id),
                ChatMessageReaction.user_id == str(user.id),
                ChatMessageReaction.emoji == emoji,
            )
        )
    ).scalar_one_or_none()

    if existing:
        await db.delete(existing)
    else:
        db.add(
            ChatMessageReaction(
                message_id=str(message.id),
                user_id=str(user.id),
                emoji=emoji,
            )
        )

    await db.commit()

    # Загружаем актуальные реакции для отдачи свежего сообщения.
    reactions_map = await _load_reactions_map(db, [str(message.id)], str(user.id))
    loaded = await _get_message(db, str(message.id))
    if not loaded:
        raise HTTPException(status_code=404, detail="Message not found")
    return _serialize_message(loaded, reactions_map.get(str(message.id), []))


@router.get("/messages", response_model=List[GlobalChatMessageResponse])
async def list_global_messages(
    request: Request,
    skip: int = 0,
    limit: int = 200,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    global_conversation = await _ensure_global_conversation(db, user)
    await _require_conversation_access(request, db, user, global_conversation)
    messages = await _load_conversation_messages(db, str(global_conversation.id), skip, limit)
    reactions_map = await _load_reactions_map(
        db, [str(m.id) for m in messages], str(user.id)
    )
    return [
        _serialize_message(message, reactions_map.get(str(message.id), []))
        for message in messages
    ]


@router.post("/messages", response_model=GlobalChatMessageResponse)
async def create_global_message(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    global_conversation = await _ensure_global_conversation(db, user)
    body, mentions, reply_to_message_id, forwarded_from_message_id, files = await _parse_message_form(request)
    message = await _create_message(
        request,
        db,
        user,
        global_conversation,
        body,
        mentions,
        files,
        reply_to_message_id=reply_to_message_id,
        forwarded_from_message_id=forwarded_from_message_id,
    )
    return _serialize_message(message)


@router.patch("/messages/{message_id}", response_model=GlobalChatMessageResponse)
async def update_message(
    message_id: str,
    payload: GlobalChatMessageUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    message = await _get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    conversation = await _get_conversation(db, str(message.conversation_id))
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await _require_conversation_access(request, db, user, conversation)
    if str(message.user_id) != str(user.id) and not _is_admin(request):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if message.is_deleted:
        raise HTTPException(status_code=400, detail="Message deleted")

    body = (payload.body or "").strip()
    if not body:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    message.body = body
    message.edited_at = _utcnow()
    conversation.updated_at = _utcnow()
    await db.commit()

    loaded = await _get_message(db, message_id)
    if not loaded:
        raise HTTPException(status_code=404, detail="Message not found")
    return _serialize_message(loaded)


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    message = await _get_message(db, message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    conversation = await _get_conversation(db, str(message.conversation_id))
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await _require_conversation_access(request, db, user, conversation)
    if str(message.user_id) != str(user.id) and not _is_admin(request):
        raise HTTPException(status_code=403, detail="Not enough permissions")
    if message.is_deleted:
        return {"deleted": True}

    message.is_deleted = True
    message.deleted_at = _utcnow()
    message.body = None
    message.attachments = []
    if message.is_pinned:
        message.is_pinned = False
        message.pinned_at = None
        message.pinned_by_user_id = None
    conversation.updated_at = _utcnow()
    await db.commit()
    return {"deleted": True}

