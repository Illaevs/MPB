"""
Pydantic schemas for approval workflows.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ApprovalTemplateStepWrite(BaseModel):
    client_id: Optional[str] = None
    parent_client_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    assignee_type: str = "user"
    assignee_user_id: Optional[str] = None
    assignee_role_id: Optional[str] = None
    is_required: bool = True
    step_order: int = Field(default=1, ge=1)

    model_config = ConfigDict(extra="forbid")


class ApprovalTemplateWrite(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    entity_type: str
    is_active: bool = True
    tags: List[str] = Field(default_factory=list)
    steps: List[ApprovalTemplateStepWrite] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class ApprovalTemplateStepResponse(BaseModel):
    id: str
    parent_step_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    assignee_type: str
    assignee_user_id: Optional[str] = None
    assignee_role_id: Optional[str] = None
    assignee_label: Optional[str] = None
    is_required: bool = True
    step_order: int

    model_config = ConfigDict(from_attributes=True)


class ApprovalTemplateResponse(BaseModel):
    id: str
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    entity_type: str
    is_active: bool
    tags: List[str] = Field(default_factory=list)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    steps: List[ApprovalTemplateStepResponse] = Field(default_factory=list)
    active_instances_count: int = 0
    total_instances_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ApprovalInstanceStart(BaseModel):
    template_id: str
    entity_id: str
    entity_type: Optional[str] = None
    entity_label: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class ApprovalInstanceAction(BaseModel):
    comment: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


class ApprovalInstanceStepResponse(BaseModel):
    id: str
    template_step_id: Optional[str] = None
    parent_template_step_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    assignee_type: str
    assignee_user_id: Optional[str] = None
    assignee_role_id: Optional[str] = None
    assignee_label: Optional[str] = None
    status: str
    is_required: bool
    step_order: int
    depth: int
    acted_by: Optional[str] = None
    acted_by_label: Optional[str] = None
    acted_at: Optional[datetime] = None
    comment: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ApprovalActionLogResponse(BaseModel):
    id: str
    instance_step_id: Optional[str] = None
    action: str
    actor_user_id: Optional[str] = None
    actor_label: Optional[str] = None
    comment: Optional[str] = None
    payload_json: Optional[Any] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ApprovalInstanceResponse(BaseModel):
    id: str
    template_id: str
    template_name: str
    entity_type: str
    entity_id: str
    entity_label: Optional[str] = None
    status: str
    current_step_id: Optional[str] = None
    started_by: Optional[str] = None
    started_by_label: Optional[str] = None
    completed_by: Optional[str] = None
    completed_by_label: Optional[str] = None
    completed_comment: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    steps: List[ApprovalInstanceStepResponse] = Field(default_factory=list)
    actions: List[ApprovalActionLogResponse] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ApprovalInboxItem(BaseModel):
    id: str
    template_name: str
    entity_type: str
    entity_type_label: str
    entity_id: str
    entity_label: Optional[str] = None
    status: str
    started_by: Optional[str] = None
    started_by_label: Optional[str] = None
    started_by_avatar_url: Optional[str] = None
    completed_by_label: Optional[str] = None
    completed_by_avatar_url: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_steps: int
    completed_steps: int
    current_step_order: Optional[int] = None
    current_step_title: Optional[str] = None
    current_step_assignee_label: Optional[str] = None
    progress_label: str
    current_stage_label: str
    waiting_for_me: bool = False
    involved_by_me: bool = False
    action_url: Optional[str] = None


class ApprovalInboxStats(BaseModel):
    pending_me: int = 0
    active: int = 0
    history: int = 0
    total_visible: int = 0


class ApprovalInboxResponse(BaseModel):
    stats: ApprovalInboxStats
    items: List[ApprovalInboxItem] = Field(default_factory=list)
    total: int = 0
    offset: int = 0
    limit: int = 0
