"""제안서 버전 모델 (F-03)"""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


class ProposalVersion(Base):
    """제안서 버전 스냅샷 모델"""
    __tablename__ = "proposal_versions"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    proposal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("proposals.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_by: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # 관계
    proposal: Mapped["Proposal"] = relationship("Proposal", back_populates="versions")
    creator: Mapped["User"] = relationship("User", backref="proposal_versions")

    __table_args__ = (
        Index("idx_proposal_versions_proposal", "proposal_id"),
    )

    def __repr__(self) -> str:
        return f"<ProposalVersion {self.version_number} proposal={self.proposal_id}>"


# 순환 참조 방지
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.proposal import Proposal
    from src.models.user import User
