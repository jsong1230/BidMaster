"""알림 설정 모델 (F-10)"""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class NotificationSetting(Base):
    """알림 설정 모델"""
    __tablename__ = "notification_settings"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    kakao_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    push_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # 관계
    user: Mapped["User"] = relationship("User", backref="notification_settings")

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "notification_type",
            name="uq_notification_settings_user_type",
        ),
    )

    def __repr__(self) -> str:
        return f"<NotificationSetting user={self.user_id} type={self.notification_type}>"


# Any 타입 힌트용 (순환 참조 방지)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.user import User
