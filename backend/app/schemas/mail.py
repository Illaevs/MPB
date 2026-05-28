"""
Mail schemas.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr


class MailboxCreate(BaseModel):
    name: str
    email: EmailStr


class MailboxResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    provider: str
    status: str
    last_sync_at: Optional[datetime] = None


class MailboxAuthUrl(BaseModel):
    auth_url: str


class MailboxAppPassword(BaseModel):
    app_password: str


class MailAttachmentResponse(BaseModel):
    id: str
    name: str
    size: Optional[int] = None
    content_type: Optional[str] = None
    blocked: bool = False
    blocked_reason: Optional[str] = None
    download_url: Optional[str] = None


class MailMessageResponse(BaseModel):
    id: str
    mailbox_id: str
    uid: str
    folder: str = "inbox"
    subject: Optional[str] = None
    from_addr: Optional[str] = None
    to_addr: Optional[str] = None
    cc_addr: Optional[str] = None
    date: Optional[datetime] = None
    snippet: Optional[str] = None
    is_read: bool = True
    has_attachments: bool = False
    attachments_count: int = 0


class MailMessageList(BaseModel):
    items: List[MailMessageResponse]
    total: int = 0
    limit: int = 50
    offset: int = 0
    has_more: bool = False
    folder: str = "inbox"


class MailFolderResponse(BaseModel):
    id: str
    label: str
    count: int = 0
    unread_count: int = 0
    icon: str = ""


class MailMessageMoveRequest(BaseModel):
    target: str


class MailSendRequest(BaseModel):
    to: List[EmailStr]
    subject: str
    body: str
    cc: List[EmailStr] = []
    bcc: List[EmailStr] = []


class MailSendResponse(BaseModel):
    message: str = "ok"
