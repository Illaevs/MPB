"""Корпоративная лента новостей — модели.

`FeedPost`     — пост (новость). Публикуют только HR/админ (см. роутер).
`FeedComment`  — комментарий к посту (пишут все авторизованные).
`FeedReaction` — «нравится» (один на пользователя+пост).
`FeedView`     — отметка просмотра (уникальная пара пост+пользователь),
                 нужна для честного счётчика уникальных просмотров.

Картинки поста хранятся в `FeedPost.attachments` как JSON-массив
объектов `{ "url": "...", "name": "..." }` — переиспользуем общий
механизм загрузки файлов.
"""
import uuid

from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


# Тип поста: обычный / официальная новость (бейдж в ленте).
FEED_POST_TYPES = ("news", "post")


class FeedPost(Base):
    __tablename__ = "feed_posts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    author_id = Column(String(36), ForeignKey("users.id"), nullable=False)

    body = Column(Text, nullable=False)
    # 'news' — официальная (бейдж), 'post' — обычная запись.
    post_type = Column(String(16), nullable=False, default="news")
    # Закреплённые показываются вверху ленты.
    is_pinned = Column(Boolean, nullable=False, default=False)
    # [{ url, name }] — прикреплённые картинки.
    attachments = Column(JSON, nullable=False, default=list)

    # Опрос (или null). Структура:
    #   { "multi": bool, "anonymous": bool,
    #     "options": [ { "id": "o1", "text": "..." }, ... ] }
    # Голоса хранятся отдельно — в feed_poll_votes.
    poll = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    author = relationship("User", foreign_keys=[author_id])

    __table_args__ = (
        Index("ix_feed_posts_created", "created_at"),
        Index("ix_feed_posts_pinned_created", "is_pinned", "created_at"),
    )


class FeedComment(Base):
    __tablename__ = "feed_comments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(
        String(36),
        ForeignKey("feed_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    body = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    author = relationship("User", foreign_keys=[author_id])

    __table_args__ = (
        Index("ix_feed_comments_post_created", "post_id", "created_at"),
    )


class FeedReaction(Base):
    __tablename__ = "feed_reactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(
        String(36),
        ForeignKey("feed_posts.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    # Эмодзи реакции. Один пользователь может поставить несколько
    # РАЗНЫХ эмодзи на пост (Slack-стиль), но не дублировать один.
    emoji = Column(String(16), nullable=False, default="👍")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", "emoji", name="uq_feed_reaction"),
        Index("ix_feed_reactions_post", "post_id"),
    )


class FeedPollVote(Base):
    """Голос в опросе. При single-choice опросе у пользователя на пост
    одна строка; при multi-choice — по строке на каждый выбранный
    вариант (`option_id` — id из FeedPost.poll['options'])."""
    __tablename__ = "feed_poll_votes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(
        String(36),
        ForeignKey("feed_posts.id", ondelete="CASCADE"),
        nullable=False,
    )
    option_id = Column(String(36), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", "option_id", name="uq_feed_poll_vote"),
        Index("ix_feed_poll_votes_post", "post_id"),
    )


class FeedView(Base):
    __tablename__ = "feed_views"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    post_id = Column(
        String(36),
        ForeignKey("feed_posts.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="uq_feed_view"),
        Index("ix_feed_views_post", "post_id"),
    )
