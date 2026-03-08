"""
인증 API 통합 테스트용 conftest
- SQLite 인메모리 DB + 실제 auth 라우터 사용
- SQLite 호환을 위해 PostgreSQL 전용 타입(JSONB, UUID) 패치
"""
import pytest
import pytest_asyncio
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from httpx import AsyncClient, ASGITransport
from sqlalchemy import Column, String, Table, text
from sqlalchemy.dialects.sqlite import base as sqlite_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# SQLite에서 PostgreSQL 전용 타입 렌더링 패치
sqlite_base.SQLiteTypeCompiler.visit_JSONB = lambda self, type_, **kw: "TEXT"
sqlite_base.SQLiteTypeCompiler.visit_UUID = lambda self, type_, **kw: "CHAR(36)"

from src.core.database import Base, get_db  # noqa: E402
from src.api.v1.auth import router as auth_router  # noqa: E402

# 테스트용 SQLite 인메모리 엔진
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


def _ensure_companies_table() -> None:
    """User.company_id FK 해결을 위해 companies 테이블을 metadata에 등록"""
    if "companies" not in Base.metadata.tables:
        Table(
            "companies",
            Base.metadata,
            Column("id", String(36), primary_key=True),
        )


@pytest_asyncio.fixture(scope="function", autouse=False)
async def init_db():
    """테스트 DB 초기화 (함수 단위 — 테스트 격리)"""
    import src.models  # noqa: F401  — 테이블 등록 목적
    _ensure_companies_table()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
        # SQLite FK 활성화
        await conn.execute(text("PRAGMA foreign_keys=OFF"))
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def create_auth_test_app() -> FastAPI:
    """auth 라우터만 포함한 테스트용 FastAPI 앱"""
    from fastapi import HTTPException as FastAPIHTTPException
    from fastapi import Request

    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")

    @app.exception_handler(FastAPIHTTPException)
    async def http_exception_handler(request: Request, exc: FastAPIHTTPException) -> JSONResponse:
        """HTTPException의 detail을 그대로 응답 바디로 반환"""
        detail = exc.detail
        if isinstance(detail, dict) and "success" in detail:
            # 이미 우리 형식인 경우 그대로 반환
            return JSONResponse(status_code=exc.status_code, content=detail)
        # 그 외 (FastAPI 기본 에러 등)
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": {"code": "HTTP_ERROR", "message": str(detail)}},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Pydantic 422 검증 에러를 400으로 변환"""
        errors = exc.errors()
        # 누락된 필드인지 확인
        first_error = errors[0] if errors else {}
        error_type = first_error.get("type", "")
        if error_type == "missing":
            code = "VALIDATION_002"
            message = "필수 입력값이 누락되었습니다."
        else:
            code = "VALIDATION_001"
            message = "입력값 유효성 검사에 실패했습니다."
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": {"code": code, "message": message}},
        )

    return app


@pytest_asyncio.fixture(scope="function")
async def async_client(init_db) -> AsyncGenerator[AsyncClient, None]:
    """인증 테스트용 비동기 HTTP 클라이언트"""
    from datetime import datetime, timedelta, timezone
    import src.models  # noqa: F401
    from src.models.oauth_state import OAuthState

    app = create_auth_test_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    # OAuth 테스트를 위해 "valid_state"를 DB에 미리 삽입
    async with TestSessionLocal() as session:
        oauth_state = OAuthState(
            state="valid_state",
            provider="kakao",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        )
        session.add(oauth_state)
        await session.commit()

    # 카카오 API 외부 호출 mock — 인스턴스 메서드를 직접 패치
    from src.services.oauth_service import OAuthService as _OAuthService

    async def _mock_get_kakao_tokens(self, code: str) -> dict:
        return {"access_token": "mock_access_token"}

    async def _mock_get_kakao_user_info(self, access_token: str) -> dict:
        return {
            "id": 99999999,
            "kakao_account": {
                "email": "kakao_test@example.com",
                "profile": {"nickname": "카카오테스트유저"},
            },
        }

    original_get_tokens = _OAuthService._get_kakao_tokens
    original_get_user_info = _OAuthService._get_kakao_user_info
    _OAuthService._get_kakao_tokens = _mock_get_kakao_tokens  # type: ignore[method-assign]
    _OAuthService._get_kakao_user_info = _mock_get_kakao_user_info  # type: ignore[method-assign]

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
    finally:
        _OAuthService._get_kakao_tokens = original_get_tokens  # type: ignore[method-assign]
        _OAuthService._get_kakao_user_info = original_get_user_info  # type: ignore[method-assign]


@pytest.fixture
def test_user_data():
    """테스트용 사용자 데이터"""
    return {
        "email": "test@example.com",
        "password": "SecureP@ss123",
        "name": "테스트사용자",
        "phone": "010-1234-5678",
    }


@pytest_asyncio.fixture
async def mock_deleted_user(init_db):
    """실제 DB에 탈퇴(soft-delete)된 사용자 생성"""
    from datetime import datetime, timezone
    import src.models  # noqa: F401
    from src.models.user import User
    from src.core.security import get_password_hash

    async with TestSessionLocal() as session:
        user = User(
            email="deleted@example.com",
            name="탈퇴한사용자",
            password_hash=get_password_hash("SecureP@ss123"),
            deleted_at=datetime.now(timezone.utc),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest_asyncio.fixture
async def mock_expired_refresh_token(init_db):
    """실제 DB에 만료된 리프레시 토큰 생성"""
    from datetime import datetime, timedelta, timezone
    import hashlib
    import src.models  # noqa: F401
    from src.models.user import User
    from src.models.refresh_token import RefreshToken
    from src.core.security import get_password_hash

    async with TestSessionLocal() as session:
        user = User(
            email="expired_token_user@example.com",
            name="만료토큰사용자",
            password_hash=get_password_hash("SecureP@ss123"),
        )
        session.add(user)
        await session.flush()

        token_hash = hashlib.sha256("expired_token_value".encode()).hexdigest()
        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        session.add(refresh_token)
        await session.commit()
        return refresh_token


@pytest_asyncio.fixture
async def mock_revoked_refresh_token(init_db):
    """실제 DB에 폐기된(is_revoked=True) 리프레시 토큰 생성"""
    import hashlib
    import src.models  # noqa: F401
    from datetime import datetime, timedelta, timezone
    from src.models.user import User
    from src.models.refresh_token import RefreshToken
    from src.core.security import get_password_hash

    async with TestSessionLocal() as session:
        user = User(
            email="revoked_token_user@example.com",
            name="폐기토큰사용자",
            password_hash=get_password_hash("SecureP@ss123"),
        )
        session.add(user)
        await session.flush()

        token_hash = hashlib.sha256("revoked_token_value".encode()).hexdigest()
        refresh_token = RefreshToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_revoked=True,
        )
        session.add(refresh_token)
        await session.commit()
        return refresh_token


@pytest_asyncio.fixture
async def mock_password_reset_token(init_db):
    """실제 DB에 유효한 비밀번호 재설정 토큰 생성"""
    import hashlib
    import src.models  # noqa: F401
    from datetime import datetime, timedelta, timezone
    from src.models.user import User
    from src.models.password_reset_token import PasswordResetToken
    from src.core.security import get_password_hash

    async with TestSessionLocal() as session:
        user = User(
            email="reset_user@example.com",
            name="재설정토큰사용자",
            password_hash=get_password_hash("SecureP@ss123"),
        )
        session.add(user)
        await session.flush()

        token_hash = hashlib.sha256("valid_reset_token".encode()).hexdigest()
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        session.add(reset_token)
        await session.commit()
        return reset_token


@pytest_asyncio.fixture
async def mock_expired_password_reset_token(init_db):
    """실제 DB에 만료된 비밀번호 재설정 토큰 생성"""
    import hashlib
    import src.models  # noqa: F401
    from datetime import datetime, timedelta, timezone
    from src.models.user import User
    from src.models.password_reset_token import PasswordResetToken
    from src.core.security import get_password_hash

    async with TestSessionLocal() as session:
        user = User(
            email="expired_reset_user@example.com",
            name="만료재설정토큰사용자",
            password_hash=get_password_hash("SecureP@ss123"),
        )
        session.add(user)
        await session.flush()

        token_hash = hashlib.sha256("expired_reset_token".encode()).hexdigest()
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=2),
        )
        session.add(reset_token)
        await session.commit()
        return reset_token


@pytest_asyncio.fixture
async def mock_used_password_reset_token(init_db):
    """실제 DB에 이미 사용된 비밀번호 재설정 토큰 생성"""
    import hashlib
    import src.models  # noqa: F401
    from datetime import datetime, timedelta, timezone
    from src.models.user import User
    from src.models.password_reset_token import PasswordResetToken
    from src.core.security import get_password_hash

    async with TestSessionLocal() as session:
        user = User(
            email="used_reset_user@example.com",
            name="사용된재설정토큰사용자",
            password_hash=get_password_hash("SecureP@ss123"),
        )
        session.add(user)
        await session.flush()

        token_hash = hashlib.sha256("used_reset_token".encode()).hexdigest()
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            used_at=datetime.now(timezone.utc),
        )
        session.add(reset_token)
        await session.commit()
        return reset_token
