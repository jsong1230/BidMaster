"""투찰 전략 관련 Pydantic 스키마"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class WinRateDistribution(BaseModel):
    """낙찰가율 분포 통계"""
    mean: float
    std: float
    median: float
    q25: float
    q75: float
    minRate: float
    maxRate: float
    sampleCount: int


class RecommendedRange(BaseModel):
    """추천 투찰가 구간"""
    label: str
    minPrice: int
    maxPrice: int
    minRate: float
    maxRate: float
    winProbability: int
    description: str


class RecommendedRanges(BaseModel):
    """3단계 리스크 추천 구간"""
    safe: RecommendedRange
    moderate: RecommendedRange
    aggressive: RecommendedRange


class StrategyReport(BaseModel):
    """전략 리포트"""
    contractMethodStrategy: str
    marketInsight: str
    riskFactors: list[str]
    recommendations: list[str]


class StrategyResult(BaseModel):
    """투찰 전략 분석 결과"""
    bidId: str
    bidTitle: str
    contractMethod: str
    estimatedPrice: Optional[int]
    budget: Optional[int]
    winRateDistribution: WinRateDistribution
    recommendedRanges: RecommendedRanges
    strategyReport: StrategyReport
    analyzedAt: str


class SimulateRequest(BaseModel):
    """시뮬레이션 요청"""
    bidPrice: int = Field(..., ge=0, description="투찰 금액 (0 이상)")


class SimulationResult(BaseModel):
    """투찰가 시뮬레이션 결과"""
    bidId: str
    inputPrice: int
    bidRate: float
    winProbability: int
    riskLevel: str
    riskLabel: str
    analysis: str
    comparisonWithRecommended: dict[str, str]
