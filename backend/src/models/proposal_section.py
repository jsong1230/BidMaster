"""제안서 섹션 모델 (F-03)"""
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base


# 섹션 정의
SECTION_DEFINITIONS = {
    "overview": {"title": "사업 개요", "order": 1},
    "technical": {"title": "기술 제안", "order": 2},
    "methodology": {"title": "수행 방법론", "order": 3},
    "schedule": {"title": "추진 일정", "order": 4},
    "organization": {"title": "조직 구성", "order": 5},
    "budget": {"title": "예산", "order": 6},
}


class ProposalSection(Base):
    """제안서 섹션 모델"""
    __tablename__ = "proposal_sections"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    proposal_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("proposals.id", ondelete="CASCADE"),
        nullable=False,
    )
    section_key: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    section_metadata: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    is_ai_generated: Mapped[bool] = mapped_column(Boolean, default=True)
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
    proposal: Mapped["Proposal"] = relationship("Proposal", back_populates="sections")

    __table_args__ = (
        UniqueConstraint("proposal_id", "section_key", name="uq_proposal_sections_key"),
        Index("idx_proposal_sections_proposal", "proposal_id"),
    )

    def __repr__(self) -> str:
        return f"<ProposalSection {self.section_key} proposal={self.proposal_id}>"

    @property
    def word_count(self) -> int:
        """글자 수 계산"""
        if not self.content:
            return 0
        return len(self.content)


# 순환 참조 방지
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.models.proposal import Proposal
