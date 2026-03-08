"""공고 매칭 관련 Pydantic 스키마"""
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class UserBidMatchResponse(BaseModel):
    """사용자-공고 매칭 결과 응답 스키마"""
    id: str
    bid_id: str
    user_id: str
    suitability_score: Optional[Decimal] = None
    competition_score: Decimal = Decimal("0")
    capability_score: Decimal = Decimal("0")
    market_score: Decimal = Decimal("0")
    total_score: Decimal
    recommendation: Optional[str] = None
    recommendation_reason: Optional[str] = None
    is_notified: bool
    analyzed_at: Optional[datetime] = None


class MatchedBidInfo(BaseModel):
    """매칭된 공고 기본 정보"""
    id: str
    bid_number: str
    title: str
    organization: str
    budget: Optional[Decimal] = None
    deadline: datetime
    status: str


class MatchedBidListItem(BaseModel):
    """매칭 공고 목록 아이템"""
    id: str
    bid: MatchedBidInfo
    total_score: Decimal
    recommendation: Optional[str] = None
    recommendation_reason: Optional[str] = None
    analyzed_at: Optional[datetime] = None


class MatchedBidListResponse(BaseModel):
    """매칭 공고 목록 응답"""
    items: list[MatchedBidListItem]


class MatchedBidQuery(BaseModel):
    """매칭 공고 조회 파라미터"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    min_score: Decimal = Decimal("0")
    recommendation: Optional[str] = None
    sort_by: str = "totalScore"
    sort_order: str = "desc"
