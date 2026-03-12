"""제안서 모델 (F-03)"""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class Proposal(Base):
    """제안서 모델"""
    __tablename__ = "proposals"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    bid_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("bids.id", ondelete="RESTRICT"),
        nullable=False,
    )
    company_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    evaluation_checklist: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, default=0)
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # 관계
    user: Mapped["User"] = relationship("User", backref="proposals")
    bid: Mapped["Bid"] = relationship("Bid", backref="proposals")
    company: Mapped["Company | None"] = relationship("Company", backref="proposals")
    sections: Mapped[list["ProposalSection"]] = relationship(
        "ProposalSection", back_populates="proposal", cascade="all, delete-orphan"
    )
    versions: Mapped[list["ProposalVersion"]] = relationship(
        "ProposalVersion", back_populates="proposal", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_proposals_user", "user_id", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_proposals_bid", "bid_id", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_proposals_status", "status", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_proposals_user_updated", "user_id", "updated_at", postgresql_where=text("deleted_at IS NULL")),
    )

    def __repr__(self) -> str:
        return f"<Proposal {self.id} title={self.title} status={self.status}>"


# 순환 참조 방지
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.user import User
    from src.models.bid import Bid
    from src.models.company import Company
    from src.models.proposal_section import ProposalSection
    from src.models.proposal_version import ProposalVersion
