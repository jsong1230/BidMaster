"""알림 모델 (F-10)"""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Notification(Base):
    """알림 모델"""
    __tablename__ = "notifications"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, default=dict)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False, default="in_app")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # 관계
    user: Mapped["User"] = relationship("User", backref="notifications")

    __table_args__ = (
        Index(
            "idx_notifications_user_unread",
            "user_id",
            "is_read",
            postgresql_where=text("is_read = FALSE"),
        ),
        Index(
            "idx_notifications_user_created",
            "user_id",
            created_at.desc(),
        ),
    )

    def __repr__(self) -> str:
        return f"<Notification {self.id} type={self.type} user={self.user_id}>"


# Any 타입 힌트용 (순환 참조 방지)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.user import User
