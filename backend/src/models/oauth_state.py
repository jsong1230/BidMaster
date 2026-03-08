"""OAuth State 모델"""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from src.core.database import Base


class OAuthState(Base):
    """OAuth State 테이블 (CSRF 방지)"""
    __tablename__ = "oauth_states"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    state = Column(String(100), unique=True, nullable=False, index=True)
    provider = Column(String(20), nullable=False)  # kakao, naver, google
    redirect_url = Column(String(500), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<OAuthState {self.state}>"

    def is_expired(self) -> bool:
        """만료 여부 확인 (SQLite naive datetime 호환)"""
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) > expires
