"""Alembic 환경 설정"""
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from src.config import get_settings
from src.models import Base

settings = get_settings()

# Alembic Config 객체
config = context.config

# 설정 값 덮어쓰기
config.set_main_option("sqlalchemy.url", settings.database_url)

# Python 로깅 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 타겟 메타데이터 (자동 생성 마이그레이션에 사용)
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """오프라인 모드에서 마이그레이션 실행"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """마이그레이션 실행"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """비동기 마이그레이션 실행"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """온라인 모드에서 마이그레이션 실행"""
    import asyncio

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
