"""OAuth 서비스 (카카오)"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import httpx
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.core.security import AuthError, create_access_token, create_refresh_token
from src.models.user import User
from src.models.refresh_token import RefreshToken
from src.models.oauth_state import OAuthState
from src.schemas.auth import OAuthUrlResponse, LoginResponse, TokenResponse, UserResponse

settings = get_settings()


class OAuthService:
    """OAuth 서비스"""

    PROVIDER_KAKAO = "kakao"

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_oauth_url(self, provider: str, redirect_url: Optional[str] = None) -> OAuthUrlResponse:
        """OAuth 인증 URL 생성"""
        if provider != self.PROVIDER_KAKAO:
            raise AuthError("AUTH_009", "지원하지 않는 OAuth 제공자입니다.", 400)

        # State 생성 (CSRF 방지)
        state = secrets.token_urlsafe(32)

        # State DB 저장
        oauth_state = OAuthState(
            state=state,
            provider=provider,
            redirect_url=redirect_url,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        self.db.add(oauth_state)
        await self.db.commit()

        # 카카오 OAuth URL 생성
        authorization_url = self._build_kakao_authorization_url(state)

        return OAuthUrlResponse(
            authorization_url=authorization_url,
            state=state,
        )

    async def handle_callback(
        self, provider: str, code: str, state: str
    ) -> LoginResponse:
        """OAuth 콜백 처리"""
        if provider != self.PROVIDER_KAKAO:
            raise AuthError("AUTH_009", "지원하지 않는 OAuth 제공자입니다.", 400)

        # State 검증
        oauth_state = await self._validate_state(state)
        if not oauth_state:
            raise AuthError("AUTH_011", "State 검증 실패 (CSRF)", 400)

        # State 사용 처리 (일회용)
        await self.db.delete(oauth_state)
        await self.db.flush()

        # 카카오 토큰 획득
        kakao_tokens = await self._get_kakao_tokens(code)
        access_token = kakao_tokens.get("access_token")

        if not access_token:
            raise AuthError("AUTH_009", "카카오 OAuth 인증 실패", 401)

        # 카카오 사용자 정보 획득
        kakao_user_info = await self._get_kakao_user_info(access_token)
        kakao_id = str(kakao_user_info.get("id"))
        kakao_account = kakao_user_info.get("kakao_account", {})
        profile = kakao_account.get("profile", {})

        email = kakao_account.get("email")
        name = profile.get("nickname", "카카오사용자")

        # 사용자 조회 또는 생성
        user = await self._get_user_by_kakao_id(kakao_id)
        is_new_user = False

        if not user:
            # 신규 사용자 생성
            user = User(
                email=email or f"kakao_{kakao_id}@bidmaster.local",
                name=name,
                kakao_id=kakao_id,
                password_hash=None,  # 소셜 로그인 사용자는 비밀번호 없음
            )
            self.db.add(user)
            await self.db.flush()
            is_new_user = True
        else:
            # 탈퇴 여부 확인
            if user.is_deleted:
                raise AuthError("AUTH_010", "탈퇴한 계정입니다.", 403)

            # 로그인 시간 갱신
            user.last_login_at = datetime.now(timezone.utc)

        # 토큰 생성
        tokens = await self._create_tokens(user)

        await self.db.commit()

        return LoginResponse(
            user=self._to_user_response(user, is_new_user),
            tokens=tokens,
        )

    # === 내부 메서드 ===

    async def _validate_state(self, state: str) -> Optional[OAuthState]:
        """State 검증"""
        result = await self.db.execute(
            select(OAuthState).where(OAuthState.state == state)
        )
        oauth_state = result.scalar_one_or_none()

        if not oauth_state:
            return None

        if oauth_state.is_expired():
            return None

        return oauth_state

    async def _get_user_by_kakao_id(self, kakao_id: str) -> Optional[User]:
        """카카오 ID로 사용자 조회"""
        result = await self.db.execute(
            select(User).where(
                and_(User.kakao_id == kakao_id, User.deleted_at.is_(None))
            )
        )
        return result.scalar_one_or_none()

    def _build_kakao_authorization_url(self, state: str) -> str:
        """카카오 인증 URL 생성"""
        base_url = "https://kauth.kakao.com/oauth/authorize"
        params = {
            "client_id": settings.kakao_client_id,
            "redirect_uri": settings.kakao_redirect_uri,
            "response_type": "code",
            "state": state,
        }
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{base_url}?{query_string}"

    async def _get_kakao_tokens(self, code: str) -> dict:
        """카카오 토큰 획득"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://kauth.kakao.com/oauth/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": settings.kakao_client_id,
                    "client_secret": settings.kakao_client_secret,
                    "redirect_uri": settings.kakao_redirect_uri,
                    "code": code,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

            if response.status_code != 200:
                raise AuthError("AUTH_009", "카카오 OAuth 인증 실패", 401)

            return response.json()

    async def _get_kakao_user_info(self, access_token: str) -> dict:
        """카카오 사용자 정보 획득"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://kapi.kakao.com/v2/user/me",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )

            if response.status_code != 200:
                raise AuthError("AUTH_009", "카카오 OAuth 인증 실패", 401)

            return response.json()

    async def _create_tokens(self, user: User) -> TokenResponse:
        """액세스/리프레시 토큰 생성"""
        from src.services.auth_service import AuthService
        auth_service = AuthService(self.db)
        return await auth_service._create_tokens(user)

    def _to_user_response(self, user: User, is_new_user: bool = False) -> UserResponse:
        """User 모델을 응답 스키마로 변환"""
        return UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            phone=user.phone,
            company_id=user.company_id,
            role=user.role,
            is_new_user=is_new_user,
            created_at=user.created_at,
        )
