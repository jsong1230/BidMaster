"""사용자-공고 매칭 모델 (user_bid_matches 테이블)"""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, ForeignKey, Numeric, Boolean, Text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from src.core.database import Base


class UserBidMatch(Base):
    """사용자-공고 매칭 결과 테이블"""
    __tablename__ = "user_bid_matches"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    bid_id = Column(PG_UUID(as_uuid=True), ForeignKey("bids.id"), nullable=False)
    status = Column(String(20), nullable=False, default="new")  # new, interested, participating, completed
    suitability_score = Column(Numeric(5, 2), nullable=True)
    competition_score = Column(Numeric(5, 2), nullable=True, default=0)
    capability_score = Column(Numeric(5, 2), nullable=True, default=0)
    market_score = Column(Numeric(5, 2), nullable=True, default=0)
    total_score = Column(Numeric(5, 2), nullable=False)
    recommendation = Column(String(20), nullable=True)  # recommended, neutral, not_recommended
    recommendation_reason = Column(Text, nullable=True)
    is_notified = Column(Boolean, nullable=False, default=False)
    analyzed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # 관계
    bid = relationship("Bid", back_populates="user_matches")

    # 인덱스 및 제약조건
    __table_args__ = (
        UniqueConstraint("user_id", "bid_id", name="idx_user_bid_matches_unique"),
        Index("idx_user_bid_matches_user_score", "user_id", "total_score"),
        Index("idx_user_bid_matches_bid", "bid_id"),
        Index("idx_user_bid_matches_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<UserBidMatch user={self.user_id} bid={self.bid_id} score={self.total_score}>"
