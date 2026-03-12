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

    # 나라장터 API (F-01)
    nara_api_key: str = ""  # 환경변수: NARA_API_KEY
    nara_api_base_url: str = "https://apis.data.go.kr/1230000/BidPublicInfoService04"

    # 스케줄러 (F-01)
    scheduler_enabled: bool = True  # 테스트 시 비활성화
    collection_schedule_hours: str = "6,12,18"  # KST 수집 시각

    # 수집 설정 (F-01)
    collection_retry_max: int = 3
    collection_retry_base_delay: float = 2.0
    collection_page_size: int = 100
    collection_initial_days: int = 7  # 초기 수집 범위 (일)

    # 이메일 설정 (F-10)
    smtp_host: str = ""  # 환경변수: SMTP_HOST
    smtp_port: int = 587  # 환경변수: SMTP_PORT
    smtp_user: str = ""  # 환경변수: SMTP_USER
    smtp_password: str = ""  # 환경변수: SMTP_PASSWORD
    smtp_from_email: str = "noreply@bidmaster.kr"
    smtp_from_name: str = "BidMaster"
    email_enabled: bool = True  # 이메일 발송 활성화 여부

    # 카카오 알림톡 설정 (F-10, 선택사항)
    kakao_alimtalk_enabled: bool = False  # 기본 비활성
    kakao_alimtalk_api_key: str = ""
    kakao_alimtalk_sender_key: str = ""

    # 알림 스케줄러 설정 (F-10)
    deadline_notification_hour: int = 9  # KST 마감 임박 알림 시각
    deadline_notification_days: str = "3,1"  # D-3, D-1

    # 프론트엔드 URL (F-10 이메일 링크용)
    frontend_url: str = "http://localhost:3000"

    # GLM API 설정 (F-03 제안서 생성)
    glm_api_key: str = ""  # 환경변수: GLM_API_KEY
    glm_model: str = "glm-4-plus"  # 기본 모델
    glm_max_tokens: int = 4096
    glm_temperature: float = 0.7

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    """설정 인스턴스 반환 (캐싱)"""
    return Settings()
