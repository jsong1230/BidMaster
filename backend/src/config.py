"""설정 관리"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """애플리케이션 설정"""

    # 애플리케이션
    app_name: str = "BidMaster API"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    # 데이터베이스
    database_url: str = "postgresql+asyncpg://bidmaster:bidmaster@localhost:5432/bidmaster"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # 보안
    secret_key: str = "dev-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Anthropic Claude
    anthropic_api_key: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """설정 인스턴스 반환 (캐싱)"""
    return Settings()
