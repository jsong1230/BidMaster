"""사용자 모델"""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship

from src.core.database import Base


class User(Base):
    """사용자 테이블"""
    __tablename__ = "users"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)  # 소셜 로그인 시 NULL
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    kakao_id = Column(String(100), unique=True, nullable=True, index=True)
    company_id = Column(PG_UUID(as_uuid=True), ForeignKey("companies.id"), nullable=True)
    role = Column(String(20), nullable=False, default="member")  # owner, manager, member
    preferences = Column(JSONB, nullable=False, default=dict)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime, nullable=True)

    # 관계
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    bid_trackings = relationship("UserBidTracking", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"

    @property
    def is_deleted(self) -> bool:
        """탈퇴 여부 확인"""
        return self.deleted_at is not None

    @property
    def is_social_user(self) -> bool:
        """소셜 로그인 사용자 여부"""
        return self.password_hash is None
