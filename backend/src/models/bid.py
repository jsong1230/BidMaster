"""공고 모델 (bids 테이블)"""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Numeric, Date, Text, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import relationship

from src.core.database import Base


class Bid(Base):
    """공고 테이블"""
    __tablename__ = "bids"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    bid_number = Column(String(50), unique=True, nullable=False)  # 나라장터 공고번호
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    organization = Column(String(200), nullable=False)
    region = Column(String(100), nullable=True)
    category = Column(String(100), nullable=True)
    bid_type = Column(String(50), nullable=True)
    contract_method = Column(String(50), nullable=True)
    budget = Column(Numeric(15, 0), nullable=True)
    announcement_date = Column(Date, nullable=True)
    deadline = Column(DateTime, nullable=False)
    open_date = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="open")
    estimated_price = Column(Numeric(15, 0), nullable=True)
    requirements = Column(JSONB, nullable=True)  # 요구사항 목록
    scoring_criteria = Column(JSONB, nullable=True)
    crawled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # 관계
    attachments = relationship("BidAttachment", back_populates="bid", cascade="all, delete-orphan")
    user_matches = relationship("UserBidMatch", back_populates="bid", cascade="all, delete-orphan")
    trackings = relationship("UserBidTracking", back_populates="bid", cascade="all, delete-orphan")

    # 인덱스 (성능 최적화)
    __table_args__ = (
        Index("idx_bids_bid_number", "bid_number"),
        Index("idx_bids_status", "status"),
        Index("idx_bids_deadline", "deadline"),
        Index("idx_bids_organization", "organization"),
        Index("idx_bids_category", "category"),
        Index("idx_bids_status_deadline", "status", "deadline"),
    )

    def __repr__(self) -> str:
        return f"<Bid {self.bid_number}: {self.title}>"
