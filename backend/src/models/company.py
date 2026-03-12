"""회사 모델 (F-08)"""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Company(Base):
    """회사 프로필 모델"""
    __tablename__ = "companies"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    business_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ceo_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    business_areas: Mapped[list | None] = mapped_column(ARRAY(String), nullable=True)
    certifications: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    established_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    employee_count: Mapped[int | None] = mapped_column(nullable=True)
    annual_revenue: Mapped[int | None] = mapped_column(nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
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
    user: Mapped["User"] = relationship("User", backref="companies")

    __table_args__ = (
        Index("idx_companies_user", "user_id"),
        Index("idx_companies_business_number", "business_number"),
    )

    def __repr__(self) -> str:
        return f"<Company {self.name}>"


# 순환 참조 방지
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.user import User
