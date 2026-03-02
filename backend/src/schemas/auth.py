"""인증 관련 스키마"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """회원가입 요청"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64)
    name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """비밀번호 강도 검증"""
        from src.core.security import validate_password
        validate_password(v)
        return v


class LoginRequest(BaseModel):
    """로그인 요청"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """토큰 응답"""
    access_token: str
    refresh_token: str
    expires_in: int = 3600  # 1시간


class UserResponse(BaseModel):
    """사용자 응답"""
    id: UUID
    email: str
    name: str
    phone: Optional[str] = None
    company_id: Optional[UUID] = None
    role: str = "member"
    is_new_user: bool = False
    created_at: datetime


class LoginResponse(BaseModel):
    """로그인 응답"""
    user: UserResponse
    tokens: TokenResponse


class RefreshTokenRequest(BaseModel):
    """토큰 갱신 요청"""
    refresh_token: str


class LogoutRequest(BaseModel):
    """로그아웃 요청"""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """비밀번호 변경 요청"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=64)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """비밀번호 강도 검증"""
        from src.core.security import validate_password
        validate_password(v)
        return v


class ForgotPasswordRequest(BaseModel):
    """비밀번호 찾기 요청"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """비밀번호 재설정 요청"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=64)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """비밀번호 강도 검증"""
        from src.core.security import validate_password
        validate_password(v)
        return v


class DeleteAccountRequest(BaseModel):
    """계정 탈퇴 요청"""
    password: str
    reason: Optional[str] = None


class UpdateUserRequest(BaseModel):
    """사용자 정보 수정 요청"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)


class OAuthUrlResponse(BaseModel):
    """OAuth URL 응답"""
    authorization_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    """OAuth 콜백 요청"""
    code: str
    state: str
