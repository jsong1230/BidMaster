"""API 의존성"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from redis.asyncio import Redis

from src.config import get_settings

settings = get_settings()

# 비동기 엔진 생성
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True,
)

# 비동기 세션 팩토리
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Redis 클라이언트
redis_client: Redis | None = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """데이터베이스 세션 의존성"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_redis() -> Redis:
    """Redis 클라이언트 의존성"""
    global redis_client
    if redis_client is None:
        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
    return redis_client


async def close_redis() -> None:
    """Redis 연결 종료"""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
