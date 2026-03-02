"""설정 관리"""
from pydantic_settings import BaseSettings, SettingsConfigDict
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
    access_token_expire_minutes: int = 60  # 1시간
    refresh_token_expire_days: int = 30  # 30일

    # 카카오 OAuth
    kakao_client_id: str = ""
    kakao_client_secret: str = ""
    kakao_redirect_uri: str = "http://localhost:8000/api/v1/auth/oauth/kakao/callback"

    # Anthropic Claude
    anthropic_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """설정 인스턴스 반환 (캐싱)"""
    return Settings()
