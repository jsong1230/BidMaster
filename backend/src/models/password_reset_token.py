"""비밀번호 재설정 토큰 모델"""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from src.core.database import Base


class PasswordResetToken(Base):
    """비밀번호 재설정 토큰 테이블"""
    __tablename__ = "password_reset_tokens"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<PasswordResetToken {self.id}>"

    def is_expired(self) -> bool:
        """만료 여부 확인"""
        return datetime.now(timezone.utc) > self.expires_at

    def is_used(self) -> bool:
        """사용 여부 확인"""
        return self.used_at is not None

    def is_valid(self) -> bool:
        """유효 여부 확인"""
        return not self.is_used() and not self.is_expired()
