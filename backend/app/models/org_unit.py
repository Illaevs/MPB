"""
OrgUnit model - organisation structure tree (departments / teams / positions).

Adjacency list (`parent_id`) + materialised `path` for cheap subtree queries
on SQLite (`path LIKE '<path>%'` returns the node and all descendants).
`path` always starts and ends with '/' and includes the node's own id, e.g.
root: '/<id>/', child: '<parent.path><id>/'.

`head_user_id` is org-chart metadata in Phase 1; in Phase 2 it becomes the
functional pivot for the opt-in subtree permission scope (only the unit head
gets the expanded "own + subtree" view).
"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, Integer, ForeignKey
from sqlalchemy.sql import func

from app.database.base import Base


class OrgUnit(Base):
    __tablename__ = "org_units"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    parent_id = Column(String(36), ForeignKey("org_units.id"), nullable=True)
    name = Column(String(255), nullable=False)
    # company / department / team / position — purely descriptive metadata.
    kind = Column(String(32), nullable=True)
    # use_alter breaks the users <-> org_units circular FK for create_all.
    head_user_id = Column(
        String(36),
        ForeignKey("users.id", use_alter=True, name="fk_org_units_head_user"),
        nullable=True,
    )
    sort_order = Column(Integer, default=0, nullable=False)
    # Materialised path incl. self ('/a/b/c/'), maintained on create/move.
    path = Column(String(1024), nullable=True)
    depth = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @classmethod
    async def get_all(cls, db):
        from sqlalchemy import select
        result = await db.execute(
            select(cls).order_by(cls.depth, cls.sort_order, cls.name)
        )
        return result.scalars().all()

    @classmethod
    async def get_by_id(cls, db, unit_id: str):
        from sqlalchemy import select
        result = await db.execute(select(cls).where(cls.id == str(unit_id)))
        return result.scalar_one_or_none()
