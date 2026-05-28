"""
Pydantic schemas for authentication.
"""
from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr

from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: Optional[str] = None


class SessionResponse(BaseModel):
    user: Optional[UserResponse] = None
    permissions: Dict[str, Dict[str, bool]] = {}
    is_superuser: bool = False


class TokenResponse(SessionResponse):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class LoginResponse(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: Optional[UserResponse] = None
    permissions: Dict[str, Dict[str, bool]] = {}
    is_superuser: bool = False
    requires_2fa: bool = False
    requires_2fa_setup: bool = False
    challenge_token: Optional[str] = None


class TwoFactorVerifyRequest(BaseModel):
    challenge_token: str
    code: str


class TwoFactorSetupStartResponse(BaseModel):
    secret: str
    otpauth_url: str
    issuer: str
    email: EmailStr


class TwoFactorSetupConfirmRequest(BaseModel):
    secret: str
    code: str


class TwoFactorStatusResponse(BaseModel):
    enabled: bool = False
    enabled_at: Optional[datetime] = None
    backup_codes_remaining: int = 0


class TwoFactorBackupCodesResponse(TwoFactorStatusResponse):
    backup_codes: List[str] = []


class TwoFactorDisableRequest(BaseModel):
    password: str


class TwoFactorRegenerateBackupCodesRequest(BaseModel):
    code: str
