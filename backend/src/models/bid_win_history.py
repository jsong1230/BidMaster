"""낙찰 이력 모델"""
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, Date, Index, Numeric, String, DateTime, func

from src.core.database import Base


class BidWinHistory(Base):
    """낙찰 이력 테이블 (bid_win_history)"""

    __tablename__ = "bid_win_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    bid_number = Column(String(50), nullable=False)
    winner_name = Column(String(200), nullable=False)
    winner_business_number = Column(String(10), nullable=True)
    winning_price = Column(Numeric(15, 0), nullable=False)
    bid_rate = Column(Numeric(5, 4), nullable=True)
    winning_date = Column(Date, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_bid_win_history_bid_number", "bid_number"),
        Index("idx_bid_win_history_winner", "winner_business_number"),
        Index("idx_bid_win_history_date", "winning_date"),
    )

    def __repr__(self) -> str:
        return f"<BidWinHistory bid_number={self.bid_number} winner={self.winner_name}>"
