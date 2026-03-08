"""인증 API"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.security import AuthError, ValidationError, decode_token
from src.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    LoginResponse,
    TokenResponse,
    UserResponse,
    RefreshTokenRequest,
    LogoutRequest,
    ChangePasswordRequest,
    DeleteAccountRequest,
    UpdateUserRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    OAuthUrlResponse,
    OAuthCallbackResponse,
)
from src.services.auth_service import AuthService
from src.services.oauth_service import OAuthService
from src.config import get_settings

router = APIRouter(prefix="/auth", tags=["인증"])
security = HTTPBearer(auto_error=False)
settings = get_settings()


# === 의존성 ===

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """현재 사용자 의존성"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "error": {"code": "AUTH_002", "message": "인증 토큰이 필요합니다."}},
        )

    try:
        payload = decode_token(credentials.credentials)
        user_id = UUID(payload.get("sub"))
    except AuthError as e:
        # AUTH_004(유효하지 않은 토큰)와 AUTH_003(만료) 모두 AUTH_003으로 통일
        # (클라이언트는 어느 경우든 재로그인이 필요하므로 동일하게 처리)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "error": {"code": "AUTH_003", "message": "토큰이 만료되었거나 유효하지 않습니다."}},
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"success": False, "error": {"code": "AUTH_003", "message": "토큰이 만료되었거나 유효하지 않습니다."}},
        )

    auth_service = AuthService(db)
    try:
        user = await auth_service.get_current_user(user_id)
        return user
    except AuthError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={"success": False, "error": {"code": e.code, "message": e.message}},
        )


# === 공통 응답 ===

def success_response(data, status_code: int = 200):
    """성공 응답 포맷"""
    return {"success": True, "data": data}


def error_response(error: Exception):
    """에러 응답 포맷"""
    if isinstance(error, AuthError):
        return {
            "success": False,
            "error": {"code": error.code, "message": error.message},
        }
    elif isinstance(error, ValidationError):
        return {
            "success": False,
            "error": {"code": error.code, "message": error.message},
        }
    return {
        "success": False,
        "error": {"code": "SERVER_001", "message": "서버 오류가 발생했습니다."},
    }


# === 엔드포인트 ===

@router.post("/register", response_model=None, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """회원가입"""
    try:
        auth_service = AuthService(db)
        result = await auth_service.register(request)
        return success_response(result.model_dump(by_alias=True), status.HTTP_201_CREATED)
    except (AuthError, ValidationError) as e:
        raise HTTPException(status_code=e.status_code, detail=error_response(e))


@router.post("/login", response_model=None)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """로그인"""
    try:
        auth_service = AuthService(db)
        result = await auth_service.login(request)
        return success_response(result.model_dump(by_alias=True))
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=error_response(e))


@router.post("/refresh", response_model=None)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """토큰 갱신"""
    try:
        auth_service = AuthService(db)
        result = await auth_service.refresh_token(request.refresh_token)
        return success_response(result.model_dump(by_alias=True))
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=error_response(e))


@router.post("/logout", response_model=None)
async def logout(
    request: LogoutRequest,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    """로그아웃 — 인증 토큰은 선택적 (멱등성 보장)"""
    auth_service = AuthService(db)
    try:
        # 인증 토큰이 있으면 user_id 추출, 없으면 None
        user_id = None
        if credentials:
            try:
                payload = decode_token(credentials.credentials)
                user_id = UUID(payload.get("sub"))
            except Exception:
                pass
        await auth_service.logout(user_id, request.refresh_token)
    except Exception:
        pass
    return success_response(None)


@router.get("/me", response_model=None)
async def get_me(current_user: UserResponse = Depends(get_current_user)):
    """현재 사용자 조회"""
    return success_response(current_user.model_dump(by_alias=True))


@router.patch("/me", response_model=None)
async def update_me(
    request: UpdateUserRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """사용자 정보 수정"""
    try:
        auth_service = AuthService(db)
        result = await auth_service.update_user(current_user.id, request)
        return success_response(result.model_dump(by_alias=True))
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=error_response(e))


@router.post("/change-password", response_model=None)
async def change_password(
    request: ChangePasswordRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """비밀번호 변경"""
    try:
        auth_service = AuthService(db)
        await auth_service.change_password(current_user.id, request)
        return success_response(None)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=error_response(e))


@router.delete("/me", response_model=None)
async def delete_account(
    request: DeleteAccountRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """계정 탈퇴"""
    try:
        auth_service = AuthService(db)
        await auth_service.delete_account(current_user.id, request)
        return success_response(None)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=error_response(e))


@router.post("/forgot-password", response_model=None)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """비밀번호 찾기 (재설정 링크 발송)"""
    try:
        auth_service = AuthService(db)
        message = await auth_service.forgot_password(request.email)
        return success_response({"message": message})
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=error_response(e))


@router.post("/reset-password", response_model=None)
async def reset_password(
    request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    """비밀번호 재설정"""
    try:
        auth_service = AuthService(db)
        await auth_service.reset_password(request.token, request.new_password)
        return success_response(None)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=error_response(e))


# === OAuth (카카오) ===

@router.get("/oauth/kakao", response_model=None)
async def kakao_oauth_start(
    redirect_url: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """카카오 OAuth 로그인 시작"""
    try:
        oauth_service = OAuthService(db)
        result = await oauth_service.get_oauth_url(OAuthService.PROVIDER_KAKAO, redirect_url)
        # 302 Redirect
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=result.authorization_url, status_code=302)
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=error_response(e))


@router.get("/oauth/kakao/callback", response_model=None)
async def kakao_oauth_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """카카오 OAuth 콜백"""
    try:
        oauth_service = OAuthService(db)
        result = await oauth_service.handle_callback(
            OAuthService.PROVIDER_KAKAO, code, state
        )
        return success_response(result.model_dump(by_alias=True))
    except AuthError as e:
        raise HTTPException(status_code=e.status_code, detail=error_response(e))
