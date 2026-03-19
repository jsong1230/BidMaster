"""입찰 추적 관련 스키마 (F-06)"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# 허용되는 추적 상태값
VALID_TRACKING_STATUSES = frozenset(["interested", "participating", "submitted", "won", "lost"])


class CamelCaseModel(BaseModel):
    """camelCase JSON 응답 기본 클래스"""
    model_config = ConfigDict(
        alias_generator=lambda x: "".join(
            word.capitalize() if i > 0 else word.lower()
            for i, word in enumerate(x.split("_"))
        ),
        populate_by_name=True,
    )


class TrackingUpsertRequest(BaseModel):
    """입찰 추적 생성/업데이트 요청"""

    status: str = Field(..., description="추적 상태 (interested, participating, submitted, won, lost)")
    my_bid_price: Optional[int] = Field(None, alias="myBidPrice", ge=0, description="나의 투찰 금액")
    notes: Optional[str] = Field(None, max_length=10000, description="메모")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """상태값 검증"""
        if v not in VALID_TRACKING_STATUSES:
            raise ValueError(f"유효하지 않은 추적 상태입니다: {v}. 허용값: {', '.join(sorted(VALID_TRACKING_STATUSES))}")
        return v


class TrackingResponse(CamelCaseModel):
    """입찰 추적 응답"""

    id: UUID
    bid_id: UUID
    user_id: UUID
    status: str
    my_bid_price: Optional[int] = None
    is_winner: Optional[bool] = None
    submitted_at: Optional[datetime] = None
    result_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class WinHistoryItemResponse(CamelCaseModel):
    """낙찰 이력 항목 응답"""

    tracking_id: UUID
    bid_id: UUID
    title: str
    organization: str
    budget: Optional[int] = None
    my_bid_price: Optional[int] = None
    bid_rate: Optional[float] = None
    is_winner: bool
    result_at: Optional[datetime] = None
    submitted_at: Optional[datetime] = None


class WinHistoryListResponse(CamelCaseModel):
    """낙찰 이력 목록 응답"""

    items: list[WinHistoryItemResponse]
