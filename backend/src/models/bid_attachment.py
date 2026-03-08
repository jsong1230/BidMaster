"""공고 첨부파일 모델 (bid_attachments 테이블)"""
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from src.core.database import Base


class BidAttachment(Base):
    """공고 첨부파일 테이블"""
    __tablename__ = "bid_attachments"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    bid_id = Column(PG_UUID(as_uuid=True), ForeignKey("bids.id"), nullable=False)
    filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # PDF, HWP, DOC
    file_url = Column(String(1000), nullable=False)
    extracted_text = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # 관계
    bid = relationship("Bid", back_populates="attachments")

    # 인덱스
    __table_args__ = (
        Index("idx_bid_attachments_bid", "bid_id"),
    )

    def __repr__(self) -> str:
        return f"<BidAttachment {self.filename}>"
