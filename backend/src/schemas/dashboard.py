"""대시보드 관련 스키마 (F-06)"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CamelCaseModel(BaseModel):
    """camelCase JSON 응답 기본 클래스"""
    model_config = ConfigDict(
        alias_generator=lambda x: "".join(
            word.capitalize() if i > 0 else word.lower()
            for i, word in enumerate(x.split("_"))
        ),
        populate_by_name=True,
    )


class UpcomingDeadline(CamelCaseModel):
    """마감 임박 공고 항목"""

    bid_id: UUID
    title: str
    deadline: datetime
    days_left: int
    tracking_status: str


class DashboardSummaryResponse(CamelCaseModel):
    """대시보드 KPI 요약 응답"""

    period: str
    participation_count: int
    submission_count: int
    won_count: int
    lost_count: int
    pending_count: int
    total_won_amount: int
    win_rate: float
    average_won_amount: float
    roi: float
    upcoming_deadlines: list[UpcomingDeadline]


class PipelineItemResponse(CamelCaseModel):
    """파이프라인 항목"""

    tracking_id: UUID
    bid_id: UUID
    title: str
    organization: str
    budget: Optional[int] = None
    deadline: Optional[datetime] = None
    days_left: Optional[int] = None
    total_score: Optional[float] = None
    updated_at: datetime


class PipelineStageResponse(CamelCaseModel):
    """파이프라인 단계"""

    status: str
    label: str
    count: int
    items: list[PipelineItemResponse]


class PipelineResponse(CamelCaseModel):
    """파이프라인 전체 응답"""

    stages: list[PipelineStageResponse]


class MonthlyStatResponse(CamelCaseModel):
    """월별 통계 항목"""

    month: str
    participation_count: int
    submission_count: int
    won_count: int
    lost_count: int
    win_rate: float
    total_won_amount: int
    average_bid_rate: Optional[float] = None


class CumulativeStatResponse(CamelCaseModel):
    """누적 통계"""

    total_participation: int
    total_submission: int
    total_won: int
    total_lost: int
    overall_win_rate: float
    total_won_amount: int
    average_won_amount: float
    overall_roi: float


class StatisticsResponse(CamelCaseModel):
    """성과 통계 전체 응답"""

    monthly: list[MonthlyStatResponse]
    cumulative: CumulativeStatResponse
