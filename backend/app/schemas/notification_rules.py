"""
Pydantic schemas for notification rules and preferences.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List

from pydantic import BaseModel


class NotificationRuleBase(BaseModel):
    name: str
    trigger: str
    entity_type: Optional[str] = None
    priority: Optional[str] = "info"
    audience_type: Optional[str] = "assigned_user"
    audience_value: Optional[str] = None
    require_subscription: Optional[bool] = False
    conditions: Optional[Dict[str, Any]] = None
    quiet_policy: Optional[str] = "respect"
    deliver_in_app: Optional[bool] = True
    deliver_telegram: Optional[bool] = False
    throttle_minutes: Optional[int] = 0
    title_template: Optional[str] = None
    message_template: Optional[str] = None
    action_url_template: Optional[str] = None
    is_active: Optional[bool] = True


class NotificationRuleCreate(NotificationRuleBase):
    name: str
    trigger: str


class NotificationRuleUpdate(BaseModel):
    name: Optional[str] = None
    trigger: Optional[str] = None
    entity_type: Optional[str] = None
    priority: Optional[str] = None
    audience_type: Optional[str] = None
    audience_value: Optional[str] = None
    require_subscription: Optional[bool] = None
    conditions: Optional[Dict[str, Any]] = None
    quiet_policy: Optional[str] = None
    deliver_in_app: Optional[bool] = None
    deliver_telegram: Optional[bool] = None
    throttle_minutes: Optional[int] = None
    title_template: Optional[str] = None
    message_template: Optional[str] = None
    action_url_template: Optional[str] = None
    is_active: Optional[bool] = None


class NotificationRuleResponse(NotificationRuleBase):
    id: str
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationPreferenceResponse(BaseModel):
    user_id: str
    timezone: str
    quiet_hours_start: str
    quiet_hours_end: str
    digest_enabled: bool
    digest_time: str
    deliver_in_app: bool
    deliver_telegram: bool
    digest_last_sent_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationPreferenceUpdate(BaseModel):
    timezone: Optional[str] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    digest_enabled: Optional[bool] = None
    digest_time: Optional[str] = None
    deliver_in_app: Optional[bool] = None
    deliver_telegram: Optional[bool] = None


class TelegramConnectionStatusResponse(BaseModel):
    bot_configured: bool
    bot_username: Optional[str] = None
    is_connected: bool
    is_enabled: bool
    is_verified: bool
    telegram_username: Optional[str] = None
    chat_id_masked: Optional[str] = None
    linked_at: Optional[datetime] = None
    deliver_telegram: bool


class TelegramLinkResponse(BaseModel):
    bot_configured: bool
    bot_username: Optional[str] = None
    link_url: Optional[str] = None
    expires_at: Optional[datetime] = None


class NotificationSubscriptionCreate(BaseModel):
    entity_type: str
    entity_id: str


class NotificationSubscriptionResponse(BaseModel):
    id: str
    user_id: str
    entity_type: str
    entity_id: str
    is_muted: bool
    mute_until: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NotificationSubscriptionUpdate(BaseModel):
    is_muted: Optional[bool] = None
    mute_until: Optional[datetime] = None
