/**
 * F-04 낙찰가 예측 및 투찰 전략 — 타입 정의
 */

/** 낙찰가율 분포 통계 */
export interface WinRateDistribution {
  mean: number;
  std: number;
  median: number;
  q25: number;
  q75: number;
  minRate: number;
  maxRate: number;
  sampleCount: number;
}

/** 추천 투찰가 구간 */
export interface RecommendedRange {
  label: string;
  minPrice: number;
  maxPrice: number;
  minRate: number;
  maxRate: number;
  winProbability: number;
  description: string;
}

/** 3단계 리스크 추천 구간 */
export interface RecommendedRanges {
  safe: RecommendedRange;
  moderate: RecommendedRange;
  aggressive: RecommendedRange;
}

/** 전략 리포트 */
export interface StrategyReport {
  contractMethodStrategy: string;
  marketInsight: string;
  riskFactors: string[];
  recommendations: string[];
}

/** 투찰 전략 분석 결과 */
export interface StrategyResult {
  bidId: string;
  bidTitle: string;
  contractMethod: string;
  estimatedPrice: number | null;
  budget: number | null;
  winRateDistribution: WinRateDistribution;
  recommendedRanges: RecommendedRanges;
  strategyReport: StrategyReport;
  analyzedAt: string;
}

/** 투찰가 시뮬레이션 요청 */
export interface SimulateRequest {
  bidPrice: number;
}

/** 투찰가 시뮬레이션 결과 */
export interface SimulationResult {
  bidId: string;
  inputPrice: number;
  bidRate: number;
  winProbability: number;
  riskLevel: 'safe' | 'moderate' | 'aggressive' | 'over_safe' | 'extreme' | 'unknown';
  riskLabel: string;
  analysis: string;
  comparisonWithRecommended: {
    safe: string;
    moderate: string;
    aggressive: string;
  };
}
