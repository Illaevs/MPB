"""Feed API — корпоративная лента новостей.

- Читать ленту / комментировать / голосовать / реагировать — любой
  авторизованный.
- Публиковать / править / удалять посты — только `feed.edit_all`
  (или superuser).
- Комментарий удаляет его автор либо `feed.edit_all`.

Фаза 2:
- Опросы: пост может нести `poll` (single/multi, аноним/открытый).
- Эмодзи-реакции: пользователь может поставить несколько РАЗНЫХ
  эмодзи на пост.
- Упоминания: в тексте поста/комментария маркер `@[Имя](user_id)` —
  упомянутый получает уведомление, фронт рендерит ссылку на профиль.
- Уведомления: автор поста получает уведомление о новом комментарии.
"""
from __future__ import annotations

import re
import uuid as _uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import delete as sa_delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from app.core.auth_middleware import CurrentUser
from app.database.session import get_db
from app.models import (
    FeedComment,
    FeedMention,
    FeedPollVote,
    FeedPost,
    FeedReaction,
    FeedView,
    Notification,
    Role,
    User,
    UserProfile,
)
from app.schemas.feed import (
    FeedAuthor,
    FeedCommentCreate,
    FeedCommentResponse,
    FeedPoll,
    FeedPollOption,
    FeedPollResult,
    FeedPollResultOption,
    FeedPostCreate,
    FeedPostPatch,
    FeedPostResponse,
    FeedReactionGroup,
    FeedReactRequest,
    FeedSinceResponse,
    FeedVoteRequest,
)
from app.services.event_outbox import emit_event_safe
from app.services.permissions import get_section_acl, is_superuser


router = APIRouter()

# Маркер упоминания в тексте: @[Полное Имя](user-uuid).
_MENTION_RE = re.compile(r"@\[[^\]]{1,200}\]\(([0-9a-fA-F][0-9a-fA-F-]{7,})\)")


# ---- helpers --------------------------------------------------------------

async def _can_post(db: AsyncSession, request: Request, me: User) -> bool:
    """Право публиковать/править/удалять посты: `feed.edit_all`
    (или superuser)."""
    if is_superuser(request):
        return True
    acl = await get_section_acl(db, me.role_id, "feed")
    return bool(acl.edit_all)


# Картинки постов: <static>/feed/<uuid>.<ext>, раздаём через
# /api/v1/feed/image/<filename> (как avatars — без прямого /static).
_ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}
_MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8 МБ

# Обычные файлы поста — allow-list по расширению.
# Исполняемые и скриптовые расширения сюда сознательно не добавлены,
# чтобы пост не превращался в способ доставки малвари другим юзерам.
_ALLOWED_FILE_EXTS = {
    # документы
    ".pdf", ".doc", ".docx", ".rtf", ".odt", ".txt", ".md",
    # таблицы
    ".xls", ".xlsx", ".csv", ".ods", ".tsv",
    # презентации
    ".ppt", ".pptx", ".odp", ".key",
    # архивы
    ".zip", ".rar", ".7z", ".tar", ".gz", ".tgz",
    # медиа (не картинки — те идут через upload-image)
    ".mp3", ".wav", ".ogg", ".m4a", ".mp4", ".webm", ".mov", ".avi", ".mkv",
    # CAD / проектные форматы — встречаются в строительной переписке
    ".dwg", ".dxf", ".step", ".stp", ".iges", ".igs",
}
_MAX_FILE_BYTES = 50 * 1024 * 1024  # 50 МБ — потолок для любого файла поста


def _feed_images_dir() -> Path:
    """Каталог для картинок ленты. Создаётся при первом обращении."""
    from app.services.user_avatar_bootstrap import avatars_root
    d = avatars_root().parent / "feed"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _feed_files_dir() -> Path:
    """Каталог для произвольных файлов ленты. Отделён от изображений,
    чтобы /api/v1/feed/image/<...> не отдавал документы напрямую — это
    сужает доступ к storage и упрощает аудит."""
    from app.services.user_avatar_bootstrap import avatars_root
    d = avatars_root().parent / "feed-files"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _extract_mention_ids(text: str) -> set[str]:
    """Достаёт user_id из маркеров @[Имя](user_id) в тексте."""
    if not text:
        return set()
    return {m.group(1) for m in _MENTION_RE.finditer(text)}


# ---- time / poll helpers --------------------------------------------------

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_utc(value) -> Optional[datetime]:
    """ISO-строку/`datetime` → aware UTC. Naive трактуем как UTC.

    Дедлайн опроса хранится как UTC-ISO (фронт шлёт со смещением/`Z`),
    поэтому сравнение `now >= closes_at` не зависит от зоны сервера."""
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        s = str(value).strip().replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(s)
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _poll_is_closed(cfg: Optional[dict]) -> bool:
    """Опрос закрыт, если выставлен флаг `closed` ИЛИ прошёл дедлайн."""
    if not cfg or not isinstance(cfg, dict):
        return False
    if cfg.get("closed"):
        return True
    closes_at = _parse_utc(cfg.get("closes_at"))
    return bool(closes_at and _now_utc() >= closes_at)


def _compute_poll_result(cfg: dict, votes: list) -> FeedPollResult:
    """Итоги опроса из конфига + голосов. Победитель — вариант(ы) с max
    голосов (несколько при ничьей; пустой список, если голосов нет)."""
    counts: dict[str, int] = {}
    voters_all: set[str] = set()
    for v in votes:
        counts[str(v.option_id)] = counts.get(str(v.option_id), 0) + 1
        voters_all.add(str(v.user_id))
    total = len(voters_all)
    opts: list[FeedPollResultOption] = []
    max_votes = 0
    for o in (cfg.get("options") or []):
        oid = str(o.get("id"))
        n = counts.get(oid, 0)
        max_votes = max(max_votes, n)
        opts.append(FeedPollResultOption(
            id=oid, votes=n, pct=round(n / total * 100) if total else 0,
        ))
    winners = [o.id for o in opts if o.votes == max_votes and max_votes > 0]
    return FeedPollResult(
        total_votes=total, options=opts, winner_ids=winners,
        closed_at=_parse_utc(cfg.get("closed_at")),
    )


async def _sync_post_mentions(db: AsyncSession, post_id: str, body: str) -> set[str]:
    """Пересобрать упоминания в ТЕЛЕ поста (comment_id IS NULL): удалить
    прежние и вставить актуальные по тексту. Возвращает множество
    упомянутых user_id (для уведомлений). Коммит — на стороне вызывающего."""
    mentioned = _extract_mention_ids(body)
    await db.execute(sa_delete(FeedMention).where(
        FeedMention.post_id == str(post_id),
        FeedMention.comment_id.is_(None),
    ))
    for uid in mentioned:
        db.add(FeedMention(post_id=str(post_id), comment_id=None, user_id=str(uid)))
    return mentioned


async def _notify(
    db: AsyncSession,
    recipient_ids,
    *,
    ntype: str,
    title: str,
    message: str,
    post_id: str,
    actor_id: str,
):
    """Создать in-app уведомления получателям (кроме самого actor).
    Коммитит отдельно — вызывать после коммита основной сущности."""
    seen: set[str] = set()
    added = 0
    for uid in recipient_ids:
        uid = str(uid or "")
        if not uid or uid == str(actor_id) or uid in seen:
            continue
        seen.add(uid)
        db.add(Notification(
            user_id=uid,
            type=ntype,
            priority="info",
            title=title,
            message=message[:1000] if message else None,
            entity_type="feed_post",
            entity_id=str(post_id),
            action_url="/",
        ))
        added += 1
    if added:
        await db.commit()


async def _authors_map(db: AsyncSession, user_ids: set[str]) -> dict[str, FeedAuthor]:
    """Краткие карточки авторов (с должностью из профиля)."""
    ids = [str(u) for u in user_ids if u]
    if not ids:
        return {}
    rows = (await db.execute(
        select(User.id, User.full_name, User.avatar_url, Role.name)
        .outerjoin(Role, Role.id == User.role_id)
        .where(User.id.in_(ids))
    )).all()
    profiles = (await db.execute(
        select(UserProfile.user_id, UserProfile.job_title, UserProfile.department)
        .where(UserProfile.user_id.in_(ids))
    )).all()
    prof_map = {str(p[0]): (p[1], p[2]) for p in profiles}
    out: dict[str, FeedAuthor] = {}
    for (uid, full_name, avatar, role_name) in rows:
        jt, dept = prof_map.get(str(uid), (None, None))
        out[str(uid)] = FeedAuthor(
            id=str(uid), full_name=full_name, avatar_url=avatar,
            role_name=role_name, job_title=jt, department=dept,
        )
    return out


async def _post_aggregates(db: AsyncSession, post_ids: list[str], me_id: str):
    """Агрегаты по постам: реакции (по эмодзи) / комментарии / просмотры /
    голоса опросов."""
    empty = ({}, {}, {}, {}, {})
    if not post_ids:
        return empty
    # Реакции: post_id -> {emoji: count}; и post_id -> set(мои эмодзи)
    react_rows = (await db.execute(
        select(FeedReaction.post_id, FeedReaction.emoji, func.count(FeedReaction.id))
        .where(FeedReaction.post_id.in_(post_ids))
        .group_by(FeedReaction.post_id, FeedReaction.emoji)
    )).all()
    reactions: dict[str, dict[str, int]] = {}
    for (pid, emoji, n) in react_rows:
        reactions.setdefault(str(pid), {})[emoji] = int(n)
    my_react_rows = (await db.execute(
        select(FeedReaction.post_id, FeedReaction.emoji)
        .where(FeedReaction.post_id.in_(post_ids), FeedReaction.user_id == str(me_id))
    )).all()
    my_reactions: dict[str, set[str]] = {}
    for (pid, emoji) in my_react_rows:
        my_reactions.setdefault(str(pid), set()).add(emoji)

    comments = dict((str(pid), int(n)) for pid, n in (await db.execute(
        select(FeedComment.post_id, func.count(FeedComment.id))
        .where(FeedComment.post_id.in_(post_ids))
        .group_by(FeedComment.post_id)
    )).all())
    views = dict((str(pid), int(n)) for pid, n in (await db.execute(
        select(FeedView.post_id, func.count(FeedView.id))
        .where(FeedView.post_id.in_(post_ids))
        .group_by(FeedView.post_id)
    )).all())

    # Голоса опросов: post_id -> [FeedPollVote]
    votes_rows = (await db.execute(
        select(FeedPollVote).where(FeedPollVote.post_id.in_(post_ids))
    )).scalars().all()
    votes_by_post: dict[str, list] = {}
    for v in votes_rows:
        votes_by_post.setdefault(str(v.post_id), []).append(v)

    return reactions, my_reactions, comments, views, votes_by_post


def _build_poll(
    post: FeedPost,
    votes: list,
    me_id: str,
    authors: dict[str, FeedAuthor],
) -> Optional[FeedPoll]:
    """Собирает FeedPoll из post.poll + список голосов."""
    cfg = post.poll
    if not cfg or not isinstance(cfg, dict):
        return None
    options_cfg = cfg.get("options") or []
    anonymous = bool(cfg.get("anonymous"))
    # option_id -> [user_id]
    by_option: dict[str, list[str]] = {}
    voters_all: set[str] = set()
    for v in votes:
        by_option.setdefault(str(v.option_id), []).append(str(v.user_id))
        voters_all.add(str(v.user_id))
    options: list[FeedPollOption] = []
    for o in options_cfg:
        oid = str(o.get("id"))
        voter_ids = by_option.get(oid, [])
        options.append(FeedPollOption(
            id=oid,
            text=str(o.get("text") or ""),
            votes=len(voter_ids),
            voted=str(me_id) in voter_ids,
            voters=[] if anonymous else [
                authors[uid] for uid in voter_ids if uid in authors
            ],
        ))
    closed = _poll_is_closed(cfg)
    # Итоги считаем для закрытого опроса. Снапшот, зафиксированный при
    # явном закрытии, лежит в cfg["result"]; для закрытого по дедлайну
    # считаем на лету (голосовать уже нельзя — набор голосов стабилен).
    result = _compute_poll_result(cfg, votes) if closed else None
    return FeedPoll(
        multi=bool(cfg.get("multi")),
        anonymous=anonymous,
        options=options,
        total_votes=len(voters_all),
        my_voted=str(me_id) in voters_all,
        closes_at=_parse_utc(cfg.get("closes_at")),
        closed=closed,
        closed_at=_parse_utc(cfg.get("closed_at")),
        result=result,
    )


def _reaction_groups(emoji_counts: dict[str, int], mine: set[str]) -> List[FeedReactionGroup]:
    groups = [
        FeedReactionGroup(emoji=e, count=c, mine=(e in mine))
        for e, c in emoji_counts.items()
    ]
    groups.sort(key=lambda g: (-g.count, g.emoji))
    return groups


def _post_to_response(
    p: FeedPost,
    author: Optional[FeedAuthor],
    *,
    reactions: List[FeedReactionGroup],
    comments: int,
    views: int,
    poll: Optional[FeedPoll],
    can_edit: bool,
) -> FeedPostResponse:
    return FeedPostResponse(
        id=str(p.id),
        author=author,
        body=p.body,
        post_type=p.post_type or "news",
        is_pinned=bool(p.is_pinned),
        attachments=list(p.attachments or []),
        poll=poll,
        created_at=p.created_at,
        updated_at=p.updated_at,
        reactions=reactions,
        comments_count=comments,
        views_count=views,
        can_edit=can_edit,
    )


async def _serialize_posts(
    db: AsyncSession, rows: list[FeedPost], me_id: str, can_post: bool,
) -> list[FeedPostResponse]:
    """Сериализует пачку постов: один проход агрегатов + авторов."""
    post_ids = [str(p.id) for p in rows]
    reactions, my_reactions, comments, views, votes_by_post = \
        await _post_aggregates(db, post_ids, me_id)

    # Авторы постов + авторы голосов (для voters не-анонимных опросов).
    need_ids: set[str] = {str(p.author_id) for p in rows}
    for v_list in votes_by_post.values():
        for v in v_list:
            need_ids.add(str(v.user_id))
    authors = await _authors_map(db, need_ids)

    out: list[FeedPostResponse] = []
    for p in rows:
        pid = str(p.id)
        out.append(_post_to_response(
            p, authors.get(str(p.author_id)),
            reactions=_reaction_groups(reactions.get(pid, {}), my_reactions.get(pid, set())),
            comments=comments.get(pid, 0),
            views=views.get(pid, 0),
            poll=_build_poll(p, votes_by_post.get(pid, []), me_id, authors),
            can_edit=can_post or str(p.author_id) == str(me_id),
        ))
    return out


def _normalize_poll(poll_input) -> Optional[dict]:
    """FeedPollInput → dict для хранения (генерирует id вариантов)."""
    if not poll_input:
        return None
    opts = [o for o in (poll_input.options or []) if o]
    if len(opts) < 2:
        raise HTTPException(status_code=400, detail="В опросе нужно минимум 2 варианта")
    cfg = {
        "multi": bool(poll_input.multi),
        "anonymous": bool(poll_input.anonymous),
        "options": [{"id": _uuid.uuid4().hex[:8], "text": t} for t in opts],
        "closed": False,
    }
    closes_at = _parse_utc(poll_input.closes_at)
    if closes_at is not None:
        if closes_at <= _now_utc():
            raise HTTPException(status_code=400, detail="Дедлайн опроса должен быть в будущем")
        # Храним как UTC-ISO — однозначно при сравнении на любом сервере.
        cfg["closes_at"] = closes_at.isoformat()
    return cfg


# ---- list / create --------------------------------------------------------

@router.get("", response_model=List[FeedPostResponse])
async def list_feed(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tab: str = Query("all"),
):
    """Лента: закреплённые сверху, далее по убыванию даты.

    `tab`: all (всё) | news (официальные новости) | polls (посты с
    опросом) | mentions (где упомянут текущий пользователь, по
    feed_mentions — включая упоминания в комментариях). Неизвестное
    значение → all."""
    stmt = select(FeedPost)
    if tab == "news":
        stmt = stmt.where(FeedPost.post_type == "news")
    elif tab == "polls":
        stmt = stmt.where(FeedPost.poll.isnot(None))
    elif tab == "mentions":
        stmt = stmt.where(FeedPost.id.in_(
            select(FeedMention.post_id).where(FeedMention.user_id == str(user.id))
        ))
    rows = (await db.execute(
        stmt
        .order_by(FeedPost.is_pinned.desc(), FeedPost.created_at.desc())
        .limit(limit).offset(offset)
    )).scalars().all()
    can_post = await _can_post(db, request, user)
    return await _serialize_posts(db, rows, str(user.id), can_post)


@router.get("/since", response_model=FeedSinceResponse)
async def feed_since(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    after: Optional[datetime] = Query(None),
):
    """Сколько НЕзакреплённых постов появилось после `after` (created_at
    самого свежего поста у клиента). Лёгкий polling для плашки «N новых».
    Без `after` — только `latest` (инициализация курсора, count=0)."""
    latest = (await db.execute(select(func.max(FeedPost.created_at)))).scalar_one_or_none()
    count = 0
    if after is not None:
        count = (await db.execute(
            select(func.count(FeedPost.id)).where(
                FeedPost.is_pinned.is_(False),
                FeedPost.created_at > after,
            )
        )).scalar_one()
    return FeedSinceResponse(count=int(count or 0), latest=latest)


@router.get("/popular", response_model=List[FeedPostResponse])
async def popular_feed(
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(5, ge=1, le=20),
):
    """Топ постов за период по сумме (реакции + комментарии)."""
    since = datetime.utcnow() - timedelta(days=days)
    rows = (await db.execute(
        select(FeedPost).where(FeedPost.created_at >= since)
    )).scalars().all()
    if not rows:
        return []
    can_post = await _can_post(db, request, user)
    serialized = await _serialize_posts(db, list(rows), str(user.id), can_post)
    serialized.sort(
        key=lambda p: sum(r.count for r in p.reactions) + p.comments_count,
        reverse=True,
    )
    return serialized[:limit]


@router.post("", response_model=FeedPostResponse)
async def create_post(
    payload: FeedPostCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Создать пост. Требует `feed.edit_all` (или superuser)."""
    if not await _can_post(db, request, user):
        raise HTTPException(status_code=403, detail="Нет прав на публикацию в ленте")

    body = (payload.body or "").strip()
    poll = _normalize_poll(payload.poll)
    if not body and not payload.attachments and not poll:
        raise HTTPException(status_code=400, detail="Пост пустой")

    p = FeedPost(
        author_id=str(user.id),
        body=body,
        post_type=payload.post_type,
        is_pinned=bool(payload.is_pinned),
        attachments=[a.model_dump() for a in payload.attachments],
        poll=poll,
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)

    # Эмитим для BI (engagement metrics) и Telegram (echo в общий канал
    # компании, если включён) — после commit'а, чтобы p.id был.
    await emit_event_safe(
        db,
        event_type="feed_post.after_create",
        entity_type="feed_post",
        entity_id=str(p.id),
        payload={
            "id": str(p.id),
            "author_id": str(user.id),
            "post_type": payload.post_type,
            "has_attachments": bool(payload.attachments),
            "has_poll": bool(poll),
            "body_length": len(body),
        },
        payload_version=1,
    )
    await db.commit()

    # Индекс упоминаний (для вкладки «упомянули меня») + уведомления.
    mentioned = await _sync_post_mentions(db, str(p.id), body)
    await db.commit()
    if mentioned:
        await _notify(
            db, mentioned,
            ntype="feed_mention",
            title="Вас упомянули в ленте",
            message=f"{user.full_name or 'Коллега'}: {body}",
            post_id=str(p.id), actor_id=str(user.id),
        )

    authors = await _authors_map(db, {str(p.author_id)})
    return _post_to_response(
        p, authors.get(str(p.author_id)),
        reactions=[], comments=0, views=0,
        poll=_build_poll(p, [], str(user.id), {}),
        can_edit=True,
    )


@router.patch("/{post_id}", response_model=FeedPostResponse)
async def patch_post(
    post_id: str,
    payload: FeedPostPatch,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Правка поста. Автор или `feed.edit_all`. Опрос правкой не
    меняется (чтобы не сбивать уже отданные голоса)."""
    p = (await db.execute(
        select(FeedPost).where(FeedPost.id == str(post_id))
    )).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Пост не найден")
    can_post = await _can_post(db, request, user)
    if not can_post and str(p.author_id) != str(user.id):
        raise HTTPException(status_code=403, detail="Нет прав на правку поста")

    data = payload.model_dump(exclude_unset=True)
    body_changed = False
    if "body" in data and data["body"] is not None:
        p.body = data["body"].strip()
        body_changed = True
    if "post_type" in data and data["post_type"] is not None:
        p.post_type = data["post_type"]
    if "is_pinned" in data and data["is_pinned"] is not None:
        p.is_pinned = bool(data["is_pinned"])
    if "attachments" in data and data["attachments"] is not None:
        p.attachments = [
            a if isinstance(a, dict) else a.model_dump()
            for a in data["attachments"]
        ]
    # Правка тела могла добавить/убрать упоминания — пересобираем индекс,
    # чтобы вкладка «упомянули меня» отражала актуальный текст.
    if body_changed:
        await _sync_post_mentions(db, str(p.id), p.body)
    await db.commit()
    await db.refresh(p)

    serialized = await _serialize_posts(db, [p], str(user.id), True)
    return serialized[0]


@router.delete("/{post_id}")
async def delete_post(
    post_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Удалить пост. Автор или `feed.edit_all`. Каскадно чистит
    комментарии/реакции/просмотры/голоса."""
    p = (await db.execute(
        select(FeedPost).where(FeedPost.id == str(post_id))
    )).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Пост не найден")
    can_post = await _can_post(db, request, user)
    if not can_post and str(p.author_id) != str(user.id):
        raise HTTPException(status_code=403, detail="Нет прав на удаление")

    for model in (FeedComment, FeedReaction, FeedView, FeedPollVote, FeedMention):
        await db.execute(sa_delete(model).where(model.post_id == str(post_id)))
    await db.delete(p)
    await db.commit()
    return {"ok": True}


# ---- view -----------------------------------------------------------------

@router.post("/{post_id}/view")
async def mark_view(
    post_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Отметить просмотр (идемпотентно — пара пост+пользователь uniq)."""
    exists = (await db.execute(
        select(FeedView.id).where(
            FeedView.post_id == str(post_id),
            FeedView.user_id == str(user.id),
        )
    )).scalar_one_or_none()
    if not exists:
        db.add(FeedView(post_id=str(post_id), user_id=str(user.id)))
        try:
            await db.commit()
        except Exception:
            await db.rollback()
    return {"ok": True}


# ---- reactions ------------------------------------------------------------

@router.post("/{post_id}/react")
async def toggle_reaction(
    post_id: str,
    payload: FeedReactRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Поставить/снять эмодзи-реакцию (toggle). Пользователь может
    держать несколько разных эмодзи на одном посте."""
    post = (await db.execute(
        select(FeedPost.id, FeedPost.author_id).where(FeedPost.id == str(post_id))
    )).first()
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    post_author_id = str(post[1])
    emoji = payload.emoji.strip()
    existing = (await db.execute(
        select(FeedReaction.id).where(
            FeedReaction.post_id == str(post_id),
            FeedReaction.user_id == str(user.id),
            FeedReaction.emoji == emoji,
        )
    )).scalar_one_or_none()
    is_set = not existing  # True — поставили реакцию, False — сняли
    if existing:
        await db.execute(sa_delete(FeedReaction).where(FeedReaction.id == existing))
    else:
        db.add(FeedReaction(post_id=str(post_id), user_id=str(user.id), emoji=emoji))
    try:
        await db.commit()
    except Exception:
        await db.rollback()

    # Уведомить автора — только при ПОСТАНОВКЕ (не снятии) и не о своей
    # же реакции. Антиспам: пока автор не прочитал предыдущее уведомление
    # о реакции на этот пост, новых не плодим (реакции — шумное событие).
    if is_set and post_author_id != str(user.id):
        already = (await db.execute(
            select(Notification.id).where(
                Notification.user_id == post_author_id,
                Notification.type == "feed_reaction",
                Notification.entity_id == str(post_id),
                Notification.is_read.is_(False),
            ).limit(1)
        )).scalar_one_or_none()
        if not already:
            await _notify(
                db, [post_author_id],
                ntype="feed_reaction",
                title="Реакция на вашу запись",
                message=f"{user.full_name or 'Коллега'} отреагировал(а): {emoji}",
                post_id=str(post_id), actor_id=str(user.id),
            )

    rows = (await db.execute(
        select(FeedReaction.emoji, func.count(FeedReaction.id))
        .where(FeedReaction.post_id == str(post_id))
        .group_by(FeedReaction.emoji)
    )).all()
    mine = set(e for (e,) in (await db.execute(
        select(FeedReaction.emoji).where(
            FeedReaction.post_id == str(post_id),
            FeedReaction.user_id == str(user.id),
        )
    )).all())
    return {
        "ok": True,
        "reactions": [
            g.model_dump() for g in
            _reaction_groups({e: int(n) for e, n in rows}, mine)
        ],
    }


# ---- poll vote ------------------------------------------------------------

@router.post("/{post_id}/vote", response_model=FeedPoll)
async def vote_poll(
    post_id: str,
    payload: FeedVoteRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Проголосовать в опросе. Single — учитывается один вариант;
    multi — весь переданный набор (заменяет прежний выбор)."""
    p = (await db.execute(
        select(FeedPost).where(FeedPost.id == str(post_id))
    )).scalar_one_or_none()
    if not p or not p.poll:
        raise HTTPException(status_code=404, detail="Опрос не найден")

    cfg = p.poll
    # Серверная проверка закрытости (не только UI): после дедлайна или
    # ручного закрытия голос не принимаем.
    if _poll_is_closed(cfg):
        raise HTTPException(status_code=403, detail="Опрос закрыт")
    valid_ids = {str(o.get("id")) for o in (cfg.get("options") or [])}
    chosen = [str(o) for o in (payload.option_ids or []) if str(o) in valid_ids]
    if not cfg.get("multi"):
        chosen = chosen[:1]

    # Перезаписываем выбор пользователя целиком.
    await db.execute(sa_delete(FeedPollVote).where(
        FeedPollVote.post_id == str(post_id),
        FeedPollVote.user_id == str(user.id),
    ))
    for oid in chosen:
        db.add(FeedPollVote(post_id=str(post_id), option_id=oid, user_id=str(user.id)))
    await db.commit()

    votes = (await db.execute(
        select(FeedPollVote).where(FeedPollVote.post_id == str(post_id))
    )).scalars().all()
    authors = {}
    if not cfg.get("anonymous"):
        authors = await _authors_map(db, {str(v.user_id) for v in votes})
    return _build_poll(p, list(votes), str(user.id), authors)


@router.post("/{post_id}/poll/close", response_model=FeedPoll)
async def close_poll(
    post_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Досрочно закрыть опрос вручную. Право: автор поста или
    `feed.edit_all`. Идемпотентно: повторный вызов вернёт уже закрытый
    опрос. При закрытии фиксируем снапшот итогов в poll['result']."""
    p = (await db.execute(
        select(FeedPost).where(FeedPost.id == str(post_id))
    )).scalar_one_or_none()
    if not p or not p.poll:
        raise HTTPException(status_code=404, detail="Опрос не найден")
    can_post = await _can_post(db, request, user)
    if not can_post and str(p.author_id) != str(user.id):
        raise HTTPException(status_code=403, detail="Нет прав на закрытие опроса")

    votes = (await db.execute(
        select(FeedPollVote).where(FeedPollVote.post_id == str(post_id))
    )).scalars().all()

    if not p.poll.get("closed"):
        cfg = dict(p.poll)
        cfg["closed"] = True
        cfg["closed_at"] = _now_utc().isoformat()
        cfg["result"] = _compute_poll_result(cfg, list(votes)).model_dump(mode="json")
        p.poll = cfg
        flag_modified(p, "poll")  # JSON-мутацию SQLAlchemy иначе не заметит
        await db.commit()
        await db.refresh(p)

    authors = {}
    if not p.poll.get("anonymous"):
        authors = await _authors_map(db, {str(v.user_id) for v in votes})
    return _build_poll(p, list(votes), str(user.id), authors)


# ---- comments -------------------------------------------------------------

@router.get("/{post_id}/comments", response_model=List[FeedCommentResponse])
async def list_comments(
    post_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Комментарии поста по возрастанию даты."""
    rows = (await db.execute(
        select(FeedComment)
        .where(FeedComment.post_id == str(post_id))
        .order_by(FeedComment.created_at.asc())
    )).scalars().all()
    can_post = await _can_post(db, request, user)
    authors = await _authors_map(db, {str(c.author_id) for c in rows})
    return [
        FeedCommentResponse(
            id=str(c.id), post_id=str(c.post_id),
            author=authors.get(str(c.author_id)),
            body=c.body, created_at=c.created_at,
            can_delete=can_post or str(c.author_id) == str(user.id),
        )
        for c in rows
    ]


@router.post("/{post_id}/comments", response_model=FeedCommentResponse)
async def create_comment(
    post_id: str,
    payload: FeedCommentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Оставить комментарий. Автор поста получает уведомление;
    упомянутые в комментарии — тоже."""
    post = (await db.execute(
        select(FeedPost).where(FeedPost.id == str(post_id))
    )).scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Пост не найден")
    body = payload.body.strip()
    c = FeedComment(post_id=str(post_id), author_id=str(user.id), body=body)
    db.add(c)
    await db.commit()
    await db.refresh(c)

    # Уведомления: автору поста + упомянутым.
    comment_mentions = _extract_mention_ids(body)
    # Индекс упоминаний из комментария (для вкладки «упомянули меня» —
    # пост всплывёт, даже если в теле поста юзера не упоминали).
    for uid in comment_mentions:
        db.add(FeedMention(post_id=str(post_id), comment_id=str(c.id), user_id=str(uid)))
    if comment_mentions:
        await db.commit()
    recipients = set(comment_mentions)
    recipients.add(str(post.author_id))
    snippet = f"{user.full_name or 'Коллега'}: {body}"
    await _notify(
        db, recipients,
        ntype="feed_comment",
        title="Новый комментарий в ленте",
        message=snippet,
        post_id=str(post_id), actor_id=str(user.id),
    )

    authors = await _authors_map(db, {str(c.author_id)})
    return FeedCommentResponse(
        id=str(c.id), post_id=str(c.post_id),
        author=authors.get(str(c.author_id)),
        body=c.body, created_at=c.created_at, can_delete=True,
    )


@router.post("/upload-image")
async def upload_feed_image(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Загрузить картинку для поста. Возвращает `{url, name}`.
    Доступно тем, кто может публиковать (`feed.edit_all`)."""
    if not await _can_post(db, request, user):
        raise HTTPException(status_code=403, detail="Нет прав на загрузку картинок в ленту")

    ext = _ALLOWED_IMAGE_TYPES.get((file.content_type or "").lower())
    if not ext:
        raise HTTPException(status_code=400, detail="Допустимы только JPG, PNG, WEBP, GIF")
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Файл пустой")
    if len(content) > _MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="Максимальный размер картинки 8 МБ")

    filename = f"{_uuid.uuid4().hex}{ext}"
    (_feed_images_dir() / filename).write_bytes(content)
    return {
        "url": f"/api/v1/feed/image/{filename}",
        "name": file.filename or filename,
    }


@router.get("/image/{filename}")
async def get_feed_image(filename: str):
    """Отдать картинку поста. Защита от path traversal."""
    safe = Path(filename).name
    target = _feed_images_dir() / safe
    try:
        target.resolve().relative_to(_feed_images_dir().resolve())
    except (ValueError, OSError):
        raise HTTPException(status_code=404, detail="Not found")
    if not target.exists():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(str(target))


@router.post("/upload-file")
async def upload_feed_file(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Загрузить произвольный файл к посту (документ/архив/CAD/медиа).
    Возвращает `{url, name, size, kind: "file"}`.

    Картинки — отдельным эндпоинтом `/upload-image` (там идёт inline-
    галерея, тут — список «скрепок»). Разнесли по двум каталогам, чтобы
    /image/<filename> не превратился в раздачу любых файлов.

    ACL: только `feed.edit_all` — как у `upload-image` и публикации поста.
    """
    if not await _can_post(db, request, user):
        raise HTTPException(status_code=403, detail="Нет прав на загрузку файлов в ленту")

    orig_name = (file.filename or "file").strip() or "file"
    ext = Path(orig_name).suffix.lower()
    if ext not in _ALLOWED_FILE_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"Этот тип файла не поддержан. Разрешены: документы, таблицы, "
                   f"архивы, аудио/видео, CAD-проекты"
        )
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Файл пустой")
    if len(content) > _MAX_FILE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"Максимальный размер файла {_MAX_FILE_BYTES // (1024 * 1024)} МБ"
        )

    filename = f"{_uuid.uuid4().hex}{ext}"
    (_feed_files_dir() / filename).write_bytes(content)
    return {
        "url": f"/api/v1/feed/file/{filename}",
        "name": orig_name,
        "size": len(content),
        "kind": "file",
    }


@router.get("/file/{filename}")
async def get_feed_file(filename: str, name: Optional[str] = Query(None)):
    """Отдать файл поста с оригинальным именем для скачивания.
    `name` — это исходное имя файла из attachment'а (для Content-Disposition);
    физически на диске мы храним под UUID-именем."""
    safe = Path(filename).name
    target = _feed_files_dir() / safe
    try:
        target.resolve().relative_to(_feed_files_dir().resolve())
    except (ValueError, OSError):
        raise HTTPException(status_code=404, detail="Not found")
    if not target.exists():
        raise HTTPException(status_code=404, detail="Not found")
    # Передаём оригинальное имя в Content-Disposition, чтобы юзер
    # скачал файл с тем именем, под которым он был загружен.
    display = (name or safe).strip() or safe
    return FileResponse(
        str(target),
        filename=display,
        media_type="application/octet-stream",
    )


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(CurrentUser),
):
    """Удалить комментарий. Автор или `feed.edit_all`."""
    c = (await db.execute(
        select(FeedComment).where(FeedComment.id == str(comment_id))
    )).scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Комментарий не найден")
    can_post = await _can_post(db, request, user)
    if not can_post and str(c.author_id) != str(user.id):
        raise HTTPException(status_code=403, detail="Нет прав на удаление комментария")
    # Подчистить упоминания этого комментария из индекса.
    await db.execute(sa_delete(FeedMention).where(FeedMention.comment_id == str(c.id)))
    await db.delete(c)
    await db.commit()
    return {"ok": True}
