"""
Pydantic schemas for Role model.
"""
from typing import Optional, Union
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_serializer


class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    # Phase 2 (opt-in, head-based): expand "own" to the head's org subtree.
    subtree_scope: Optional[bool] = False
    # Workday tracker (см. work_session): включает блокирующий модал
    # «Начать рабочий день» и счётчик в топбаре. По умолчанию выключено
    # — чтобы заказчики/customer-роли не подвергались учёту.
    track_work_time: Optional[bool] = False
    # Через сколько минут бездействия фронт авто-закрывает сессию.
    # NULL ⇒ дефолт 30 (см. DEFAULT_IDLE_TIMEOUT_MINUTES в schemas/workday).
    idle_timeout_minutes: Optional[int] = None
    model_config = ConfigDict(extra="forbid")


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    subtree_scope: Optional[bool] = None
    track_work_time: Optional[bool] = None
    idle_timeout_minutes: Optional[int] = None
    model_config = ConfigDict(extra="forbid")


class RoleResponse(RoleBase):
    id: Union[str, UUID]
    is_system: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @field_serializer("id")
    def serialize_id(self, value):
        if isinstance(value, UUID):
            return str(value)
        return value
