"""입찰 추적 모델 (user_bid_tracking 테이블)"""
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    Text,
    UniqueConstraint,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from src.core.database import Base


class UserBidTracking(Base):
    """사용자별 입찰 추적 테이블"""

    __tablename__ = "user_bid_tracking"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    bid_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("bids.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(String(20), nullable=False, default="interested")
    my_bid_price = Column(Numeric(15, 0), nullable=True)
    is_winner = Column(Boolean, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    result_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # 관계
    user = relationship("User", back_populates="bid_trackings")
    bid = relationship("Bid", back_populates="trackings")

    __table_args__ = (
        # 유니크 제약: (user_id, bid_id) 쌍은 유일
        UniqueConstraint("user_id", "bid_id", name="uq_user_bid_tracking"),
        # Check 제약: 허용된 상태값
        CheckConstraint(
            "status IN ('interested', 'participating', 'submitted', 'won', 'lost')",
            name="chk_tracking_status",
        ),
        # 인덱스 (성능 최적화)
        Index("idx_user_bid_tracking_user", "user_id"),
        Index("idx_user_bid_tracking_user_status", "user_id", "status"),
        Index("idx_user_bid_tracking_result_at", "user_id", "result_at"),
        Index("idx_user_bid_tracking_created", "user_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<UserBidTracking user={self.user_id} bid={self.bid_id} status={self.status}>"
