"""
Pydantic schemas for Legal Work module.
"""
from datetime import date, datetime, time
from typing import List, Optional

from pydantic import BaseModel


class LegalCaseBase(BaseModel):
    case_number: Optional[str] = None
    judge: Optional[str] = None
    jurisdiction: Optional[str] = None
    judge_assistant: Optional[str] = None
    judge_assistant_phone: Optional[str] = None
    plaintiff_id: Optional[str] = None
    defendant_id: Optional[str] = None
    description: Optional[str] = None


class LegalCaseCreate(LegalCaseBase):
    pass


class LegalCaseUpdate(LegalCaseBase):
    pass


class LegalCaseEventBase(BaseModel):
    event_type: str
    event_date: date
    event_time: Optional[time] = None
    courtroom: Optional[str] = None


class LegalCaseEventCreate(LegalCaseEventBase):
    pass


class LegalCaseEventUpdate(BaseModel):
    event_type: Optional[str] = None
    event_date: Optional[date] = None
    event_time: Optional[time] = None
    courtroom: Optional[str] = None


class LegalCaseEventFileResponse(BaseModel):
    id: str
    event_id: str
    file_name: str
    storage_path: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LegalCaseEventResponse(LegalCaseEventBase):
    id: str
    legal_case_id: str
    files: List[LegalCaseEventFileResponse] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LegalCaseTaskLinkCreate(BaseModel):
    task_id: str


class LegalCaseTaskResponse(BaseModel):
    id: str
    title: str
    status: Optional[str] = None
    due_date: Optional[date] = None
    deal_id: Optional[str] = None
    deal_title: Optional[str] = None


class LegalCaseResponse(LegalCaseBase):
    id: str
    plaintiff_name: Optional[str] = None
    defendant_name: Optional[str] = None
    events: List[LegalCaseEventResponse] = []
    tasks: List[LegalCaseTaskResponse] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
