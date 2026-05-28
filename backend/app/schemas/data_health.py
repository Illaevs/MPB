from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DataHealthIssueResponse(BaseModel):
    id: str
    fingerprint: str
    deal_id: Optional[str] = None
    deal_title: Optional[str] = None
    scope_type: str
    scope_id: Optional[str] = None
    issue_type: str
    module: str
    severity: str
    status: str
    title: str
    description: str = ""
    payload: Dict[str, Any] = Field(default_factory=dict)
    navigation_path: Optional[str] = None
    navigation_query: Dict[str, Any] = Field(default_factory=dict)
    first_detected_at: Optional[datetime] = None
    last_detected_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    ignored_reason: Optional[str] = None
    ignored_until: Optional[datetime] = None
    ignored_by_user_id: Optional[str] = None
    ignored_at: Optional[datetime] = None


class DataHealthIgnoreRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=2000)
    ignored_until: Optional[datetime] = None


class DataHealthSummaryResponse(BaseModel):
    total: int = 0
    open: int = 0
    ignored: int = 0
    resolved: int = 0
    errors: int = 0
    warnings: int = 0
    infos: int = 0


class DataHealthListResponse(BaseModel):
    items: List[DataHealthIssueResponse] = Field(default_factory=list)
    total: int = 0
    summary: DataHealthSummaryResponse = Field(default_factory=DataHealthSummaryResponse)


class DataHealthIssueGroupResponse(BaseModel):
    id: str
    group_key: str
    count: int = 0
    deal_id: Optional[str] = None
    deal_title: Optional[str] = None
    issue_type: str
    module: str
    severity: str
    status: str
    title: str
    description: str = ""
    payload: Dict[str, Any] = Field(default_factory=dict)
    navigation_path: Optional[str] = None
    navigation_query: Dict[str, Any] = Field(default_factory=dict)
    first_detected_at: Optional[datetime] = None
    last_detected_at: Optional[datetime] = None
    items: List[DataHealthIssueResponse] = Field(default_factory=list)


class DataHealthGroupedListResponse(BaseModel):
    items: List[DataHealthIssueGroupResponse] = Field(default_factory=list)
    total: int = 0
    summary: DataHealthSummaryResponse = Field(default_factory=DataHealthSummaryResponse)


class DataHealthDealCountResponse(BaseModel):
    deal_id: str
    total: int = 0
    errors: int = 0
    warnings: int = 0
    ignored: int = 0


class DataHealthDealCountsResponse(BaseModel):
    items: List[DataHealthDealCountResponse] = Field(default_factory=list)
