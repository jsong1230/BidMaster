"""
테스트 설정 및 공통 Fixture
"""
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# TODO: 구현 후 import 수정
# from src.main import app
# from src.core.security import create_access_token, create_refresh_token
# from src.models.user import User
# from src.models.refresh_token import RefreshToken


# 임시 fixture - 구현 후 실제 모듈로 교체
class MockApp:
    """임시 FastAPI 앱 Mock"""
    pass


app = MockApp()


@pytest.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    테스트용 비동기 DB 세션 Fixture
    """
    # TODO: testcontainers로 실제 PostgreSQL 연결
    engine = create_async_engine(
        "postgresql+asyncpg://test:test@localhost:5432/test",
        echo=False,
    )
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_maker() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def async_client(async_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    테스트용 비동기 HTTP 클라이언트 Fixture
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_user_data():
    """
    테스트용 사용자 데이터 Fixture
    """
    return {
        "email": "test@example.com",
        "password": "SecureP@ss123",
        "name": "테스트사용자",
        "phone": "010-1234-5678",
    }


@pytest.fixture
def test_kakao_user_data():
    """
    테스트용 카카오 사용자 데이터 Fixture
    """
    return {
        "kakao_id": "1234567890",
        "email": "user@kakao.com",
        "name": "카카오사용자",
    }


@pytest.fixture
def test_admin_data():
    """
    테스트용 관리자 데이터 Fixture
    """
    return {
        "email": "admin@bidmaster.kr",
        "password": "AdminP@ss456",
        "name": "관리자",
        "role": "admin",
    }
