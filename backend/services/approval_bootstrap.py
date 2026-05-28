"""
Bootstrap helpers for approval workflow schema.
"""
from app.database.base import Base
from app.database.session import engine_sync
from app.models.approval import (
    ApprovalActionLog,
    ApprovalInstance,
    ApprovalInstanceStep,
    ApprovalTemplate,
    ApprovalTemplateStep,
)


def ensure_approval_schema() -> None:
    Base.metadata.create_all(
        engine_sync,
        tables=[
            ApprovalTemplate.__table__,
            ApprovalTemplateStep.__table__,
            ApprovalInstance.__table__,
            ApprovalInstanceStep.__table__,
            ApprovalActionLog.__table__,
        ],
    )
