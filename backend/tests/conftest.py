"""
테스트 설정 및 공통 Fixture
"""
import pytest
from typing import AsyncGenerator
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient, ASGITransport
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

# 임시 Mock 구현 - 구현 후 실제 모듈로 교체
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

class MockApp(FastAPI):
    """임시 FastAPI 앱 Mock"""

    def __init__(self):
        super().__init__()
        # 임시 라우트 추가 (테스트 실행을 위해)
        @self.get("/")
        async def root():
            return {"message": "Mock API"}

        @self.post("/api/v1/auth/register")
        async def mock_register(request: Request):
            return JSONResponse(
                status_code=501,
                content={"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}}
            )

        @self.post("/api/v1/auth/login")
        async def mock_login(request: Request):
            return JSONResponse(
                status_code=501,
                content={"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}}
            )

        @self.post("/api/v1/auth/refresh")
        async def mock_refresh(request: Request):
            return JSONResponse(
                status_code=501,
                content={"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}}
            )

        @self.post("/api/v1/auth/logout")
        async def mock_logout(request: Request):
            return JSONResponse(
                status_code=501,
                content={"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}}
            )

        @self.get("/api/v1/auth/me")
        async def mock_me(request: Request):
            return JSONResponse(
                status_code=501,
                content={"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}}
            )

        @self.get("/api/v1/auth/oauth/kakao")
        async def mock_oauth_kakao(request: Request):
            return Response(status_code=302, headers={"location": "https://kauth.kakao.com/oauth/authorize"})

        @self.get("/api/v1/auth/oauth/kakao/callback")
        async def mock_oauth_callback(request: Request):
            return JSONResponse(
                status_code=501,
                content={"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}}
            )

        @self.post("/api/v1/auth/forgot-password")
        async def mock_forgot_password(request: Request):
            return JSONResponse(
                status_code=501,
                content={"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}}
            )

        @self.post("/api/v1/auth/reset-password")
        async def mock_reset_password(request: Request):
            return JSONResponse(
                status_code=501,
                content={"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}}
            )

        @self.post("/api/v1/auth/change-password")
        async def mock_change_password(request: Request):
            return JSONResponse(
                status_code=501,
                content={"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}}
            )

        @self.delete("/api/v1/auth/me")
        async def mock_delete_account(request: Request):
            return JSONResponse(
                status_code=501,
                content={"success": False, "error": {"code": "NOT_IMPLEMENTED", "message": "Not implemented yet"}}
            )


class MockUser:
    """사용자 Mock"""
    def __init__(self, id=None, email=None, password_hash=None, name=None, phone=None, role=None):
        self.id = id or str(uuid4())
        self.email = email or "test@example.com"
        self.password_hash = password_hash
        self.name = name or "테스트사용자"
        self.phone = phone
        self.company_id = str(uuid4())
        self.role = role or "owner"
        self.preferences: dict = {}
        self.last_login_at = None
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        self.deleted_at: datetime | None = None


class MockRefreshToken:
    """리프레시 토큰 Mock"""
    def __init__(
        self,
        id=None,
        user_id=None,
        token_hash=None,
        expires_at=None,
        is_revoked=False,
    ):
        self.id = id or str(uuid4())
        self.user_id = user_id or str(uuid4())
        self.token_hash = token_hash
        self.device_info = None
        self.ip_address = None
        self.expires_at = expires_at or datetime.now(timezone.utc) + timedelta(days=30)
        self.is_revoked = is_revoked
        self.created_at = datetime.now(timezone.utc)


class MockOAuthState:
    """OAuth State Mock"""
    def __init__(
        self,
        id=None,
        state=None,
        provider=None,
        redirect_url=None,
        expires_at=None,
    ):
        self.id = id or str(uuid4())
        self.state = state or str(uuid4())
        self.provider = provider or "kakao"
        self.redirect_url = redirect_url
        self.expires_at = expires_at or datetime.now(timezone.utc) + timedelta(minutes=10)
        self.created_at = datetime.now(timezone.utc)


class MockPasswordResetToken:
    """비밀번호 재설정 토큰 Mock"""
    def __init__(
        self,
        id=None,
        user_id=None,
        token_hash=None,
        expires_at=None,
        used_at=None,
    ):
        self.id = id or str(uuid4())
        self.user_id = user_id or str(uuid4())
        self.token_hash = token_hash
        self.expires_at = expires_at or datetime.now(timezone.utc) + timedelta(hours=1)
        self.used_at = used_at
        self.created_at = datetime.now(timezone.utc)


app = MockApp()


@pytest.fixture
def mock_app() -> FastAPI:
    """테스트용 FastAPI 앱 Fixture"""
    return app


# 에러 코드 정의
class AppError(Exception):
    """커스텀 에러 기본 클래스"""
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthError(AppError):
    """인증 관련 에러"""
    pass


class ValidationError(AppError):
    """유효성 검사 에러"""
    pass


# 에러 코드 상수
AUTH_001 = AuthError("AUTH_001", "이메일 또는 비밀번호가 올바르지 않습니다.", 401)
AUTH_002 = AuthError("AUTH_002", "인증 토큰이 필요합니다.", 401)
AUTH_003 = AuthError("AUTH_003", "토큰이 만료되었습니다.", 401)
AUTH_004 = AuthError("AUTH_004", "유효하지 않은 토큰입니다.", 401)
AUTH_005 = AuthError("AUTH_005", "로그아웃된 토큰입니다.", 401)
AUTH_006 = AuthError("AUTH_006", "리프레시 토큰이 유효하지 않습니다.", 401)
AUTH_007 = AuthError("AUTH_007", "이미 가입된 이메일입니다.", 409)
AUTH_008 = AuthError("AUTH_008", "비밀번호 재사용이 제한됩니다.", 400)
AUTH_009 = AuthError("AUTH_009", "카카오 OAuth 인증 실패", 401)
AUTH_010 = AuthError("AUTH_010", "탈퇴한 계정입니다.", 403)
AUTH_011 = AuthError("AUTH_011", "State 검증 실패 (CSRF)", 400)
AUTH_012 = AuthError("AUTH_012", "만료된 재설정 토큰입니다.", 400)
AUTH_013 = AuthError("AUTH_013", "이미 사용된 재설정 토큰입니다.", 400)

VALIDATION_001 = ValidationError("VALIDATION_001", "입력값 유효성 실패", 400)
VALIDATION_002 = ValidationError("VALIDATION_002", "필수 입력값 누락", 400)
VALIDATION_003 = ValidationError("VALIDATION_003", "입력값 길이 초과", 400)


@pytest.fixture
async def async_client(mock_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """
    테스트용 비동기 HTTP 클라이언트 Fixture
    """
    transport = ASGITransport(app=mock_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def auth_error_codes():
    """인증 에러 코드들"""
    return {
        "AUTH_001": AUTH_001,
        "AUTH_002": AUTH_002,
        "AUTH_003": AUTH_003,
        "AUTH_004": AUTH_004,
        "AUTH_005": AUTH_005,
        "AUTH_006": AUTH_006,
        "AUTH_007": AUTH_007,
        "AUTH_008": AUTH_008,
        "AUTH_009": AUTH_009,
        "AUTH_010": AUTH_010,
        "AUTH_011": AUTH_011,
        "AUTH_012": AUTH_012,
        "AUTH_013": AUTH_013,
    }


@pytest.fixture
def validation_error_codes():
    """유효성 검사 에러 코드들"""
    return {
        "VALIDATION_001": VALIDATION_001,
        "VALIDATION_002": VALIDATION_002,
        "VALIDATION_003": VALIDATION_003,
    }


@pytest.fixture
def mock_user():
    """테스트용 사용자 Mock Fixture"""
    return MockUser(
        id=str(uuid4()),
        email="test@example.com",
        name="테스트사용자",
        phone="010-1234-5678",
    )


@pytest.fixture
def mock_kakao_user():
    """테스트용 카카오 사용자 Mock Fixture"""
    return MockUser(
        id=str(uuid4()),
        email="user@kakao.com",
        name="카카오사용자",
        phone=None,
    )


@pytest.fixture
def mock_admin_user():
    """테스트용 관리자 Mock Fixture"""
    return MockUser(
        id=str(uuid4()),
        email="admin@bidmaster.kr",
        name="관리자",
        role="admin",
    )


@pytest.fixture
def mock_deleted_user():
    """테스트용 삭제된 사용자 Mock Fixture"""
    user = MockUser(
        id=str(uuid4()),
        email="deleted@example.com",
        name="삭제된사용자",
    )
    user.deleted_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def mock_refresh_token():
    """테스트용 리프레시 토큰 Mock Fixture"""
    return MockRefreshToken(
        id=str(uuid4()),
        user_id=str(uuid4()),
        token_hash="hash_" + str(uuid4()),
    )


@pytest.fixture
def mock_expired_refresh_token():
    """테스트용 만료된 리프레시 토큰 Mock Fixture"""
    return MockRefreshToken(
        id=str(uuid4()),
        user_id=str(uuid4()),
        token_hash="expired_hash_" + str(uuid4()),
        expires_at=datetime.now(timezone.utc) - timedelta(days=1),
    )


@pytest.fixture
def mock_revoked_refresh_token():
    """테스트용 폐기된 리프레시 토큰 Mock Fixture"""
    return MockRefreshToken(
        id=str(uuid4()),
        user_id=str(uuid4()),
        token_hash="revoked_hash_" + str(uuid4()),
        is_revoked=True,
    )


@pytest.fixture
def mock_oauth_state():
    """테스트용 OAuth State Mock Fixture"""
    return MockOAuthState(
        id=str(uuid4()),
        state=str(uuid4()),
        provider="kakao",
    )


@pytest.fixture
def mock_expired_oauth_state():
    """테스트용 만료된 OAuth State Mock Fixture"""
    return MockOAuthState(
        id=str(uuid4()),
        state="expired_state",
        provider="kakao",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=11),
    )


@pytest.fixture
def mock_password_reset_token():
    """테스트용 비밀번호 재설정 토큰 Mock Fixture"""
    return MockPasswordResetToken(
        id=str(uuid4()),
        user_id=str(uuid4()),
        token_hash="reset_hash_" + str(uuid4()),
    )


@pytest.fixture
def mock_expired_password_reset_token():
    """테스트용 만료된 비밀번호 재설정 토큰 Mock Fixture"""
    return MockPasswordResetToken(
        id=str(uuid4()),
        user_id=str(uuid4()),
        token_hash="expired_reset_hash_" + str(uuid4()),
        expires_at=datetime.now(timezone.utc) - timedelta(hours=2),
    )


@pytest.fixture
def mock_used_password_reset_token():
    """테스트용 사용된 비밀번호 재설정 토큰 Mock Fixture"""
    return MockPasswordResetToken(
        id=str(uuid4()),
        user_id=str(uuid4()),
        token_hash="used_reset_hash_" + str(uuid4()),
        used_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def test_user_data():
    """테스트용 사용자 데이터 Fixture"""
    return {
        "email": "test@example.com",
        "password": "SecureP@ss123",
        "name": "테스트사용자",
        "phone": "010-1234-5678",
    }


@pytest.fixture
def test_kakao_user_data():
    """테스트용 카카오 사용자 데이터 Fixture"""
    return {
        "kakao_id": "1234567890",
        "email": "user@kakao.com",
        "name": "카카오사용자",
    }


@pytest.fixture
def test_admin_data():
    """테스트용 관리자 데이터 Fixture"""
    return {
        "email": "admin@bidmaster.kr",
        "password": "AdminP@ss456",
        "name": "관리자",
        "role": "admin",
    }


@pytest.fixture
def mock_http_response():
    """테스트용 HTTP 응답 Mock Fixture"""
    def _create_response(
        status_code: int = 200,
        success: bool = True,
        data: dict | None = None,
        error: str | None = None,
    ):
        return {
            "status_code": status_code,
            "json": lambda: {
                "success": success,
                "data": data,
                "error": error,
            },
        }
    return _create_response


@pytest.fixture
def mock_auth_service():
    """AuthService Mock Fixture"""
    service = AsyncMock()
    service.register = AsyncMock()
    service.login = AsyncMock()
    service.refresh_token = AsyncMock()
    service.logout = AsyncMock()
    return service


@pytest.fixture
def mock_oauth_service():
    """OAuthService Mock Fixture"""
    service = AsyncMock()
    service.get_oauth_url = AsyncMock()
    service.handle_callback = AsyncMock()
    return service


@pytest.fixture
def mock_user_repository():
    """UserRepository Mock Fixture"""
    repo = AsyncMock()
    repo.find_by_email = AsyncMock()
    repo.find_by_kakao_id = AsyncMock()
    repo.find_by_id = AsyncMock()
    repo.create = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def mock_token_repository():
    """TokenRepository Mock Fixture"""
    repo = AsyncMock()
    repo.find_by_hash = AsyncMock()
    repo.create = AsyncMock()
    repo.revoke = AsyncMock()
    return repo
