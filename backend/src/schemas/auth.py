"""인증 관련 스키마"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from typing import Annotated
from pydantic import AliasChoices, BaseModel, ConfigDict, EmailStr, Field, field_validator
from pydantic.alias_generators import to_camel


class CamelCaseResponse(BaseModel):
    """camelCase JSON 응답 기본 클래스"""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )


class CamelCaseRequest(BaseModel):
    """camelCase JSON 요청 기본 클래스 (snake_case도 함께 지원)"""
    model_config = ConfigDict(
        populate_by_name=True,
    )


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


class TokenResponse(CamelCaseResponse):
    """토큰 응답 (camelCase 직렬화)"""
    access_token: str
    refresh_token: str
    expires_in: int = 1800  # 30분


class UserResponse(CamelCaseResponse):
    """사용자 응답 (camelCase 직렬화)"""
    id: UUID
    email: str
    name: str
    phone: Optional[str] = None
    company_id: Optional[UUID] = None
    role: str = "member"
    is_new_user: bool = False
    created_at: datetime


class LoginResponse(CamelCaseResponse):
    """로그인 응답"""
    user: UserResponse
    tokens: TokenResponse


class RefreshTokenRequest(CamelCaseRequest):
    """토큰 갱신 요청 (camelCase: refreshToken 지원)"""
    refresh_token: Annotated[str, Field(
        validation_alias=AliasChoices("refreshToken", "refresh_token"),
    )]


class LogoutRequest(CamelCaseRequest):
    """로그아웃 요청 (camelCase: refreshToken 지원)"""
    refresh_token: Annotated[str, Field(
        validation_alias=AliasChoices("refreshToken", "refresh_token"),
    )]


class ChangePasswordRequest(CamelCaseRequest):
    """비밀번호 변경 요청 (camelCase: currentPassword, newPassword 지원)"""
    current_password: Annotated[str, Field(
        validation_alias=AliasChoices("currentPassword", "current_password"),
    )]
    new_password: Annotated[str, Field(
        validation_alias=AliasChoices("newPassword", "new_password"),
    )]

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """비밀번호 강도 검증 및 길이 검사"""
        if len(v) < 8 or len(v) > 64:
            from src.core.security import ValidationError
            raise ValidationError("VALIDATION_001", "비밀번호는 8자 이상 64자 이하여야 합니다.", 400)
        from src.core.security import validate_password
        validate_password(v)
        return v


class ForgotPasswordRequest(BaseModel):
    """비밀번호 찾기 요청"""
    email: EmailStr


class ResetPasswordRequest(CamelCaseRequest):
    """비밀번호 재설정 요청 (camelCase: newPassword 지원)"""
    token: str
    new_password: Annotated[str, Field(
        validation_alias=AliasChoices("newPassword", "new_password"),
    )]

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """비밀번호 강도 검증 및 길이 검사"""
        if len(v) < 8 or len(v) > 64:
            from src.core.security import ValidationError
            raise ValidationError("VALIDATION_001", "비밀번호는 8자 이상 64자 이하여야 합니다.", 400)
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


class OAuthUrlResponse(CamelCaseResponse):
    """OAuth URL 응답"""
    authorization_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    """OAuth 콜백 요청"""
    code: str
    state: str


class OAuthCallbackResponse(CamelCaseResponse):
    """OAuth 콜백 응답"""
    user: UserResponse
    tokens: TokenResponse
    is_new_user: bool = False
