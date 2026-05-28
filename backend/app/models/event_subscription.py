"""
EventSubscription — подписка внешнего приёмника на события из event bus.

Подписки матчатся воркером по `event_type_pattern` (glob с *: `deal.*`,
`*.after_create`, `*`).  Доставка HMAC-подписана (sha256) ключом
`hmac_secret` — секрет хранится только на бэкенде и в самой строке.

В MVP — единственный delivery_method=`webhook` (POST на target_url),
остальные (`queue`, `email`) добавим по мере появления реальных
интеграций. Архитектура не меняется — runtime подключения добавятся в
воркере.
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON
from sqlalchemy.sql import func

from app.database.base import Base


class EventSubscription(Base):
    __tablename__ = "event_subscriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Имя для UI (admin-friendly: "Telegram-канал отдел продаж").
    name = Column(String(255), nullable=False)

    # Glob-паттерн на event_type. "*" = все события, "deal.*" = все
    # события сделки, "*.after_create" = все события создания, "deal.after_create" = точное.
    event_type_pattern = Column(String(128), nullable=False, index=True)

    # Способ доставки. В MVP только webhook.
    delivery_method = Column(String(16), nullable=False, default="webhook")

    # Куда доставлять (для webhook — URL).
    target_url = Column(String(1024), nullable=False)

    # Секрет для HMAC sha256-подписи. Подписчик использует тот же, чтобы
    # проверять что запрос пришёл от нас, а не от случайного клиента.
    hmac_secret = Column(String(255), nullable=False)

    # Можно временно отключить без удаления.
    is_active = Column(Boolean, nullable=False, default=True)

    # JSON-Logic фильтр поверх payload события. Если NULL/пустой —
    # подписка получает ВСЕ совпавшие по event_type_pattern события.
    # Если задан — worker оценивает правило перед доставкой и пропускает
    # только match'ащиеся. Поддерживаемые операторы — см.
    # `app.services.json_logic`.
    #
    # Пример: подписаться на «крупные подписанные контракты»:
    #   condition_json = {"and": [
    #       {"==": [{"var": "status"}, "signed"]},
    #       {">": [{"var": "amount"}, 1000000]}
    #   ]}
    condition_json = Column(JSON, nullable=True)

    # Опциональные комментарии админа.
    description = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @classmethod
    async def create(cls, db, **kwargs):
        kwargs.setdefault("id", str(uuid.uuid4()))
        kwargs.setdefault("delivery_method", "webhook")
        kwargs.setdefault("is_active", True)
        kwargs.setdefault("created_at", datetime.now())
        item = cls(**kwargs)
        db.add(item)
        await db.commit()
        await db.refresh(item)
        return item
