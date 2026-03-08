"""인증 서비스"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.core.security import (
    AuthError,
    ValidationError,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    validate_password,
    verify_password,
)
from src.models.user import User
from src.models.refresh_token import RefreshToken
from src.models.password_reset_token import PasswordResetToken
from src.models.oauth_state import OAuthState
from src.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    LoginResponse,
    TokenResponse,
    UserResponse,
    ChangePasswordRequest,
    DeleteAccountRequest,
    UpdateUserRequest,
)

settings = get_settings()


class AuthService:
    """인증 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(self, data: RegisterRequest) -> LoginResponse:
        """회원가입"""
        # 이메일 중복 확인
        existing_user = await self._get_user_by_email(data.email)
        if existing_user:
            raise AuthError("AUTH_007", "이미 가입된 이메일입니다.", 409)

        # 비밀번호 유효성 검사
        validate_password(data.password, data.email)

        # 사용자 생성
        user = User(
            email=data.email,
            password_hash=get_password_hash(data.password),
            name=data.name,
            phone=data.phone,
        )
        self.db.add(user)
        await self.db.flush()

        # 토큰 생성
        tokens = await self._create_tokens(user)

        await self.db.commit()

        return LoginResponse(
            user=self._to_user_response(user, is_new_user=True),
            tokens=tokens,
        )

    async def login(self, data: LoginRequest) -> LoginResponse:
        """로그인"""
        # 사용자 조회 (탈퇴 사용자 포함하여 조회 후 탈퇴 여부 별도 체크)
        user = await self._get_user_by_email(data.email, include_deleted=True)
        if not user:
            raise AuthError("AUTH_001", "이메일 또는 비밀번호가 올바르지 않습니다.", 401)

        # 탈퇴 여부 확인
        if user.is_deleted:
            raise AuthError("AUTH_010", "탈퇴한 계정입니다.", 403)

        # 비밀번호 검증 (소셜 로그인 사용자는 비밀번호 없음)
        if user.is_social_user or not verify_password(data.password, user.password_hash):
            raise AuthError("AUTH_001", "이메일 또는 비밀번호가 올바르지 않습니다.", 401)

        # 로그인 시간 갱신
        user.last_login_at = datetime.now(timezone.utc)

        # 토큰 생성
        tokens = await self._create_tokens(user)

        await self.db.commit()

        return LoginResponse(
            user=self._to_user_response(user),
            tokens=tokens,
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """토큰 갱신"""
        # 먼저 토큰 해시로 DB 조회 (revoke 여부 우선 확인)
        token_hash = self._hash_token(refresh_token)
        stored_token = await self._get_refresh_token_by_hash(token_hash)

        if stored_token and stored_token.is_revoked:
            # 명시적으로 폐기된 토큰 (로그아웃 또는 보안상 폐기)
            raise AuthError("AUTH_005", "로그아웃된 토큰입니다.", 401)

        # 토큰 디코딩 (만료 여부 확인)
        try:
            payload = decode_token(refresh_token)
        except AuthError:
            raise AuthError("AUTH_006", "리프레시 토큰이 유효하지 않습니다.", 401)

        user_id = payload.get("sub")
        jti = payload.get("jti")

        if not user_id or not jti:
            raise AuthError("AUTH_006", "리프레시 토큰이 유효하지 않습니다.", 401)

        if not stored_token:
            raise AuthError("AUTH_006", "리프레시 토큰이 유효하지 않습니다.", 401)

        if stored_token.is_expired():
            raise AuthError("AUTH_006", "리프레시 토큰이 유효하지 않습니다.", 401)

        # 기존 토큰 폐기
        stored_token.is_revoked = True

        # 사용자 조회
        user = await self._get_user_by_id(UUID(user_id))
        if not user or user.is_deleted:
            raise AuthError("AUTH_006", "리프레시 토큰이 유효하지 않습니다.", 401)

        # 새 토큰 생성
        tokens = await self._create_tokens(user)

        await self.db.commit()

        return tokens

    async def logout(self, user_id: Optional[UUID], refresh_token: str) -> None:
        """로그아웃"""
        # 토큰 해시로 DB 조회 (user_id는 사용 안 함, 멱등성 보장)
        token_hash = self._hash_token(refresh_token)
        stored_token = await self._get_refresh_token_by_hash(token_hash)

        if stored_token:
            stored_token.is_revoked = True

        await self.db.commit()

    async def get_current_user(self, user_id: UUID) -> UserResponse:
        """현재 사용자 조회"""
        user = await self._get_user_by_id(user_id)
        if not user:
            raise AuthError("AUTH_004", "유효하지 않은 토큰입니다.", 401)

        if user.is_deleted:
            raise AuthError("AUTH_010", "탈퇴한 계정입니다.", 403)

        return self._to_user_response(user)

    async def update_user(self, user_id: UUID, data: UpdateUserRequest) -> UserResponse:
        """사용자 정보 수정"""
        user = await self._get_user_by_id(user_id)
        if not user:
            raise AuthError("AUTH_004", "유효하지 않은 토큰입니다.", 401)

        if data.name is not None:
            user.name = data.name
        if data.phone is not None:
            user.phone = data.phone

        user.updated_at = datetime.now(timezone.utc)

        await self.db.commit()
        await self.db.refresh(user)

        return self._to_user_response(user)

    async def change_password(self, user_id: UUID, data: ChangePasswordRequest) -> None:
        """비밀번호 변경"""
        user = await self._get_user_by_id(user_id)
        if not user:
            raise AuthError("AUTH_004", "유효하지 않은 토큰입니다.", 401)

        # 소셜 로그인 사용자는 비밀번호 변경 불가
        if user.is_social_user:
            raise AuthError("AUTH_001", "소셜 로그인 사용자는 비밀번호를 변경할 수 없습니다.", 400)

        # 현재 비밀번호 검증
        if not verify_password(data.current_password, user.password_hash):
            raise AuthError("AUTH_001", "이메일 또는 비밀번호가 올바르지 않습니다.", 401)

        # 이전 비밀번호 재사용 방지
        if verify_password(data.new_password, user.password_hash):
            raise AuthError("AUTH_008", "비밀번호 재사용이 제한됩니다.", 400)

        # 비밀번호 유효성 검사
        validate_password(data.new_password, user.email)

        # 비밀번호 변경
        user.password_hash = get_password_hash(data.new_password)
        user.updated_at = datetime.now(timezone.utc)

        # 모든 리프레시 토큰 폐기 (보안)
        await self._revoke_all_user_tokens(user_id)

        await self.db.commit()

    async def delete_account(self, user_id: UUID, data: DeleteAccountRequest) -> None:
        """계정 탈퇴 (Soft Delete)"""
        user = await self._get_user_by_id(user_id)
        if not user:
            raise AuthError("AUTH_004", "유효하지 않은 토큰입니다.", 401)

        # 소셜 로그인 사용자가 아닌 경우 비밀번호 검증
        if not user.is_social_user:
            if not verify_password(data.password, user.password_hash):
                raise AuthError("AUTH_001", "이메일 또는 비밀번호가 올바르지 않습니다.", 401)

        # Soft Delete
        user.deleted_at = datetime.now(timezone.utc)

        # 모든 리프레시 토큰 폐기
        await self._revoke_all_user_tokens(user_id)

        await self.db.commit()

    async def forgot_password(self, email: str) -> str:
        """비밀번호 찾기 (재설정 토큰 생성)"""
        user = await self._get_user_by_email(email)

        # 사용자가 없어도 동일한 성공 응답 (보안)
        if not user or user.is_deleted:
            return "비밀번호 재설정 링크를 이메일로 발송했습니다."

        # 기존 미사용 토큰 폐기
        await self._invalidate_unused_reset_tokens(user.id)

        # 새 토큰 생성
        token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(token)

        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        self.db.add(reset_token)

        await self.db.commit()

        # TODO: 이메일 발송 (실제 구현 시)
        # await email_service.send_password_reset_email(user.email, token)

        return "비밀번호 재설정 링크를 이메일로 발송했습니다."

    async def reset_password(self, token: str, new_password: str) -> None:
        """비밀번호 재설정"""
        token_hash = self._hash_token(token)
        reset_token = await self._get_password_reset_token_by_hash(token_hash)

        if not reset_token:
            raise AuthError("AUTH_013", "이미 사용된 재설정 토큰입니다.", 400)

        if reset_token.is_expired():
            raise AuthError("AUTH_012", "만료된 재설정 토큰입니다.", 400)

        if reset_token.is_used():
            raise AuthError("AUTH_013", "이미 사용된 재설정 토큰입니다.", 400)

        # 사용자 조회
        user = await self._get_user_by_id(reset_token.user_id)
        if not user or user.is_deleted:
            raise AuthError("AUTH_013", "이미 사용된 재설정 토큰입니다.", 400)

        # 비밀번호 유효성 검사
        validate_password(new_password, user.email)

        # 비밀번호 변경
        user.password_hash = get_password_hash(new_password)
        user.updated_at = datetime.now(timezone.utc)

        # 토큰 사용 처리
        reset_token.used_at = datetime.now(timezone.utc)

        # 모든 리프레시 토큰 폐기
        await self._revoke_all_user_tokens(user.id)

        await self.db.commit()

    # === 내부 메서드 ===

    async def _get_user_by_email(self, email: str, include_deleted: bool = False) -> Optional[User]:
        """이메일로 사용자 조회"""
        conditions = [User.email == email]
        if not include_deleted:
            conditions.append(User.deleted_at.is_(None))
        result = await self.db.execute(select(User).where(and_(*conditions)))
        return result.scalar_one_or_none()

    async def _get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """ID로 사용자 조회"""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def _get_refresh_token_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """해시로 리프레시 토큰 조회"""
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def _get_password_reset_token_by_hash(self, token_hash: str) -> Optional[PasswordResetToken]:
        """해시로 비밀번호 재설정 토큰 조회"""
        result = await self.db.execute(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def _create_tokens(self, user: User) -> TokenResponse:
        """액세스/리프레시 토큰 생성"""
        # 액세스 토큰 생성
        access_token = create_access_token(
            user.id,
            extra_data={
                "email": user.email,
                "role": user.role,
                "companyId": str(user.company_id) if user.company_id else None,
            }
        )

        # 리프레시 토큰 생성
        refresh_token = create_refresh_token(user.id)

        # 리프레시 토큰 DB 저장
        token_hash = self._hash_token(refresh_token)
        stored_token = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days),
        )
        self.db.add(stored_token)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def _revoke_all_user_tokens(self, user_id: UUID) -> None:
        """사용자의 모든 리프레시 토큰 폐기"""
        result = await self.db.execute(
            select(RefreshToken).where(
                and_(RefreshToken.user_id == user_id, RefreshToken.is_revoked == False)
            )
        )
        tokens = result.scalars().all()
        for token in tokens:
            token.is_revoked = True

    async def _invalidate_unused_reset_tokens(self, user_id: UUID) -> None:
        """미사용 비밀번호 재설정 토큰 무효화"""
        result = await self.db.execute(
            select(PasswordResetToken).where(
                and_(
                    PasswordResetToken.user_id == user_id,
                    PasswordResetToken.used_at.is_(None),
                )
            )
        )
        tokens = result.scalars().all()
        for token in tokens:
            token.used_at = datetime.now(timezone.utc)

    def _hash_token(self, token: str) -> str:
        """토큰 해시 생성"""
        return hashlib.sha256(token.encode()).hexdigest()

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
