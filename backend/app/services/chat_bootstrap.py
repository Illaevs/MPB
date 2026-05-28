"""
Idempotent bootstrap for messenger schema.
"""
import re

from sqlalchemy import inspect, or_, select, text, update

from app.database.base import Base
from app.database.session import async_session, engine
from app.models import ChatConversation, ChatConversationMember, GlobalChatMessage, User


CHAT_MESSAGE_COLUMNS = {
    "conversation_id": "VARCHAR(36)",
    "reply_to_message_id": "VARCHAR(36)",
    "forwarded_from_message_id": "VARCHAR(36)",
    "is_pinned": "BOOLEAN DEFAULT FALSE",
    "pinned_at": "TIMESTAMP",
    "pinned_by_user_id": "VARCHAR(36)",
}

_SAFE_SQL_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


async def _table_exists(conn, table_name: str) -> bool:
    return await conn.run_sync(lambda sync_conn: inspect(sync_conn).has_table(table_name))


async def _get_columns(conn, table_name: str) -> set[str]:
    return await conn.run_sync(
        lambda sync_conn: {column["name"] for column in inspect(sync_conn).get_columns(table_name)}
    )


def _safe_add_column_ddl(table_name: str, column_name: str, definition: str) -> str:
    if not _SAFE_SQL_IDENTIFIER_RE.fullmatch(table_name):
        raise ValueError(f"Unsafe SQL table identifier: {table_name}")
    if not _SAFE_SQL_IDENTIFIER_RE.fullmatch(column_name):
        raise ValueError(f"Unsafe SQL column identifier: {column_name}")
    return f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {definition}'


async def ensure_chat_schema() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.create_all,
            tables=[
                ChatConversation.__table__,
                ChatConversationMember.__table__,
                GlobalChatMessage.__table__,
            ],
        )

        if not await _table_exists(conn, "global_chat_messages"):
            return

        existing_columns = await _get_columns(conn, "global_chat_messages")
        for column_name, definition in CHAT_MESSAGE_COLUMNS.items():
            if column_name in existing_columns:
                continue
            await conn.execute(text(_safe_add_column_ddl("global_chat_messages", column_name, definition)))

        await conn.execute(text("UPDATE global_chat_messages SET is_pinned = FALSE WHERE is_pinned IS NULL"))

    async with async_session() as db:
        result = await db.execute(
            select(ChatConversation).where(ChatConversation.type == "global").order_by(ChatConversation.created_at.asc())
        )
        global_conversation = result.scalars().first()
        if global_conversation is None:
            seed_user = (
                await db.execute(select(User).where(User.is_active == True).order_by(User.created_at.asc()).limit(1))
            ).scalars().first()
            global_conversation = ChatConversation(
                type="global",
                title="Global Chat",
                description="Company-wide conversation",
                created_by_user_id=str(seed_user.id) if seed_user else None,
            )
            db.add(global_conversation)
            await db.commit()
            await db.refresh(global_conversation)

        await db.execute(
            update(GlobalChatMessage)
            .where(or_(GlobalChatMessage.conversation_id == None, GlobalChatMessage.conversation_id == ""))
            .values(conversation_id=global_conversation.id)
        )
        await db.commit()
