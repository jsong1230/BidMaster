"""낙찰 가능성 스코어링 관련 Pydantic 스키마"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ScoreBreakdown(BaseModel):
    """항목별 점수 상세"""
    score: float = Field(ge=0.0, le=100.0)
    factors: list[str] = Field(default_factory=list)


class ScoringScores(BaseModel):
    """스코어링 4개 항목 점수"""
    suitability: float = Field(ge=0.0, le=100.0)
    competition: float = Field(ge=0.0, le=100.0)
    capability: float = Field(ge=0.0, le=100.0)
    market: float = Field(ge=0.0, le=100.0)
    total: float = Field(ge=0.0, le=100.0)


class ScoringWeights(BaseModel):
    """가중치 설정"""
    suitability: float = 0.30
    competition: float = 0.25
    capability: float = 0.30
    market: float = 0.15


class ScoringDetails(BaseModel):
    """항목별 상세 분석"""
    suitability: ScoreBreakdown
    competition: ScoreBreakdown
    capability: ScoreBreakdown
    market: ScoreBreakdown


class TopCompetitor(BaseModel):
    """경쟁사 정보"""
    name: str
    winCount: int


class CompetitorStats(BaseModel):
    """경쟁사 통계"""
    estimatedCompetitors: int = Field(ge=0)
    topCompetitors: list[TopCompetitor] = Field(default_factory=list)


class SimilarBidStats(BaseModel):
    """유사 공고 낙찰 통계"""
    totalCount: int = Field(ge=0)
    avgWinRate: Optional[float] = None
    avgWinningPrice: Optional[float] = None


class ScoringResult(BaseModel):
    """스코어링 결과 전체"""
    id: str
    bidId: str
    userId: str
    scores: ScoringScores
    weights: ScoringWeights
    recommendation: str
    recommendationLabel: str
    recommendationReason: str
    details: ScoringDetails
    competitorStats: CompetitorStats
    similarBidStats: SimilarBidStats
    analyzedAt: str
