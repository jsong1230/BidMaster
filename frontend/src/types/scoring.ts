/**
 * F-02 낙찰 가능성 스코어링 타입 정의
 */

export interface ScoreBreakdown {
  score: number;
  factors: string[];
}

export interface ScoringScores {
  suitability: number;
  competition: number;
  capability: number;
  market: number;
  total: number;
}

export interface ScoringWeights {
  suitability: number;
  competition: number;
  capability: number;
  market: number;
}

export interface ScoringDetails {
  suitability: ScoreBreakdown;
  competition: ScoreBreakdown;
  capability: ScoreBreakdown;
  market: ScoreBreakdown;
}

export interface TopCompetitor {
  name: string;
  winCount: number;
}

export interface CompetitorStats {
  estimatedCompetitors: number;
  topCompetitors: TopCompetitor[];
}

export interface SimilarBidStats {
  totalCount: number;
  avgWinRate: number | null;
  avgWinningPrice: number | null;
}

export type Recommendation =
  | 'strongly_recommended'
  | 'recommended'
  | 'neutral'
  | 'not_recommended';

export interface ScoringResult {
  id: string;
  bidId: string;
  userId: string;
  scores: ScoringScores;
  weights: ScoringWeights;
  recommendation: Recommendation;
  recommendationLabel: string;
  recommendationReason: string;
  details: ScoringDetails;
  competitorStats: CompetitorStats;
  similarBidStats: SimilarBidStats;
  analyzedAt: string;
}
