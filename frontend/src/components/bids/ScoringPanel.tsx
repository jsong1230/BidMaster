/**
 * F-02 낙찰 가능성 스코어링 패널
 * 4개 항목(적합도/경쟁강도/역량/시장환경) 게이지 바 + 상세 factors 표시
 */
'use client';

import type { ScoringResult, Recommendation } from '@/types/scoring';

// ----------------------------------------------------------------
// 추천 등급 배지
// ----------------------------------------------------------------

const RECOMMENDATION_CONFIG: Record<
  Recommendation,
  { label: string; bgClass: string; textClass: string; borderClass: string }
> = {
  strongly_recommended: {
    label: '강력추천',
    bgClass: 'bg-green-50',
    textClass: 'text-green-700',
    borderClass: 'border-green-200',
  },
  recommended: {
    label: '추천',
    bgClass: 'bg-blue-50',
    textClass: 'text-blue-700',
    borderClass: 'border-blue-200',
  },
  neutral: {
    label: '보류',
    bgClass: 'bg-yellow-50',
    textClass: 'text-yellow-700',
    borderClass: 'border-yellow-200',
  },
  not_recommended: {
    label: '비추천',
    bgClass: 'bg-neutral-100',
    textClass: 'text-neutral-500',
    borderClass: 'border-neutral-200',
  },
};

function ScoringRecommendationBadge({ recommendation }: { recommendation: Recommendation }) {
  const config = RECOMMENDATION_CONFIG[recommendation] ?? RECOMMENDATION_CONFIG.neutral;
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${config.bgClass} ${config.textClass} ${config.borderClass}`}
    >
      {config.label}
    </span>
  );
}

// ----------------------------------------------------------------
// 점수 게이지 바 (가로형)
// ----------------------------------------------------------------

const SCORE_LABEL_MAP: Record<string, string> = {
  suitability: '적합도',
  competition: '경쟁 강도',
  capability: '역량',
  market: '시장 환경',
};

const WEIGHT_MAP: Record<string, number> = {
  suitability: 0.30,
  competition: 0.25,
  capability: 0.30,
  market: 0.15,
};

function getScoreColor(score: number): string {
  if (score >= 70) return 'bg-green-500';
  if (score >= 50) return 'bg-yellow-400';
  return 'bg-neutral-400';
}

function ScoreGaugeBar({
  category,
  score,
  weight,
}: {
  category: string;
  score: number;
  weight: number;
}) {
  const label = SCORE_LABEL_MAP[category] ?? category;
  const colorClass = getScoreColor(score);
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-neutral-600 font-medium">{label}</span>
          <span className="text-xs text-neutral-400">({Math.round(weight * 100)}%)</span>
        </div>
        <span className="text-xs font-semibold text-neutral-700">{score.toFixed(1)}</span>
      </div>
      <div className="w-full bg-neutral-100 rounded-full h-2">
        <div
          className={`h-2 rounded-full transition-all duration-500 ${colorClass}`}
          style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
        />
      </div>
    </div>
  );
}

// ----------------------------------------------------------------
// 총점 원형 게이지 (SVG)
// ----------------------------------------------------------------

function TotalScoreCircle({ score }: { score: number }) {
  const radius = 15.9;
  const circumference = 2 * Math.PI * radius;
  const dasharray = `${(score / 100) * circumference} ${circumference}`;
  const strokeColor = score >= 70 ? '#22C55E' : score >= 50 ? '#EAB308' : '#9CA3AF';

  return (
    <div className="relative w-28 h-28">
      <svg
        className="w-full h-full"
        viewBox="0 0 36 36"
        style={{ transform: 'rotate(-90deg)' }}
      >
        <circle cx="18" cy="18" r={radius} fill="none" stroke="#E5E7EB" strokeWidth="2.5" />
        <circle
          cx="18"
          cy="18"
          r={radius}
          fill="none"
          stroke={strokeColor}
          strokeWidth="2.5"
          strokeDasharray={dasharray}
          strokeLinecap="round"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold text-neutral-800">{score.toFixed(1)}</span>
        <span className="text-xs text-neutral-400">/ 100</span>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------
// 스코어링 패널 로딩 스켈레톤
// ----------------------------------------------------------------

export function ScoringPanelSkeleton() {
  return (
    <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden animate-pulse">
      <div className="px-5 py-3.5 border-b border-neutral-100">
        <div className="h-4 w-32 bg-neutral-200 rounded" />
      </div>
      <div className="p-5 space-y-4">
        <div className="flex flex-col items-center">
          <div className="w-28 h-28 rounded-full bg-neutral-200" />
          <div className="mt-2 h-5 w-16 bg-neutral-200 rounded-full" />
        </div>
        <div className="space-y-3">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="space-y-1">
              <div className="flex justify-between">
                <div className="h-3 w-20 bg-neutral-200 rounded" />
                <div className="h-3 w-8 bg-neutral-200 rounded" />
              </div>
              <div className="h-2 bg-neutral-200 rounded-full" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ----------------------------------------------------------------
// 항목별 상세 카드
// ----------------------------------------------------------------

function ScoreDetailCard({
  category,
  score,
  factors,
}: {
  category: string;
  score: number;
  factors: string[];
}) {
  const label = SCORE_LABEL_MAP[category] ?? category;
  return (
    <div className="bg-neutral-50 rounded-lg p-3.5">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-semibold text-neutral-700">{label}</span>
        <span
          className={`text-xs font-bold ${
            score >= 70 ? 'text-green-600' : score >= 50 ? 'text-yellow-600' : 'text-neutral-500'
          }`}
        >
          {score.toFixed(1)}점
        </span>
      </div>
      <ul className="space-y-1">
        {factors.map((factor, idx) => (
          <li key={idx} className="flex items-start gap-1.5">
            <span className="mt-0.5 text-neutral-400 flex-shrink-0">•</span>
            <span className="text-xs text-neutral-600 leading-relaxed">{factor}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

// ----------------------------------------------------------------
// 메인 ScoringPanel 컴포넌트
// ----------------------------------------------------------------

interface ScoringPanelProps {
  scoring: ScoringResult;
}

export function ScoringPanel({ scoring }: ScoringPanelProps) {
  const { scores, weights, recommendation, recommendationReason, details, competitorStats, similarBidStats, analyzedAt } = scoring;
  const categories = ['suitability', 'competition', 'capability', 'market'] as const;

  return (
    <div className="space-y-4">
      {/* 총점 + 추천 등급 */}
      <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
        <div className="px-5 py-3.5 border-b border-neutral-100">
          <h2 className="text-sm font-semibold text-neutral-700">낙찰 가능성 스코어링</h2>
        </div>
        <div className="p-5">
          {/* 총점 게이지 */}
          <div className="flex flex-col items-center mb-5">
            <TotalScoreCircle score={scores.total} />
            <div className="mt-2">
              <ScoringRecommendationBadge recommendation={recommendation} />
            </div>
          </div>

          {/* 4개 항목 게이지 바 */}
          <div className="space-y-2.5">
            {categories.map((cat) => (
              <ScoreGaugeBar
                key={cat}
                category={cat}
                score={scores[cat]}
                weight={weights[cat]}
              />
            ))}
          </div>

          {/* 분석 일시 */}
          <p className="text-xs text-neutral-300 text-right mt-3">
            분석 {new Date(analyzedAt).toLocaleDateString('ko-KR')}{' '}
            {new Date(analyzedAt).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
          </p>
        </div>
      </div>

      {/* 추천 사유 */}
      {recommendationReason && (
        <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
          <div className="px-5 py-3.5 border-b border-neutral-100">
            <h2 className="text-sm font-semibold text-neutral-700">스코어링 사유</h2>
          </div>
          <div className="p-5">
            <p className="text-sm text-neutral-700 leading-relaxed">{recommendationReason}</p>
          </div>
        </div>
      )}

      {/* 항목별 상세 */}
      <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
        <div className="px-5 py-3.5 border-b border-neutral-100">
          <h2 className="text-sm font-semibold text-neutral-700">항목별 상세 분석</h2>
        </div>
        <div className="p-5 space-y-3">
          {categories.map((cat) => (
            <ScoreDetailCard
              key={cat}
              category={cat}
              score={details[cat].score}
              factors={details[cat].factors}
            />
          ))}
        </div>
      </div>

      {/* 경쟁사 통계 */}
      {competitorStats.estimatedCompetitors > 0 && (
        <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
          <div className="px-5 py-3.5 border-b border-neutral-100">
            <h2 className="text-sm font-semibold text-neutral-700">예상 경쟁사</h2>
          </div>
          <div className="p-5">
            <div className="flex items-center gap-2 mb-3">
              <span className="text-sm text-neutral-500">추정 경쟁 업체 수:</span>
              <span className="text-sm font-bold text-neutral-800">
                {competitorStats.estimatedCompetitors}개사
              </span>
            </div>
            {competitorStats.topCompetitors.length > 0 && (
              <div className="space-y-1.5">
                {competitorStats.topCompetitors.map((comp, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between py-1 border-b border-neutral-100 last:border-0"
                  >
                    <span className="text-xs text-neutral-700">{comp.name}</span>
                    <span className="text-xs text-neutral-400">낙찰 {comp.winCount}건</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 유사 공고 통계 */}
      {similarBidStats.totalCount > 0 && (
        <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
          <div className="px-5 py-3.5 border-b border-neutral-100">
            <h2 className="text-sm font-semibold text-neutral-700">유사 공고 낙찰 통계</h2>
          </div>
          <div className="p-5 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs text-neutral-500">유사 공고 수</span>
              <span className="text-xs font-semibold text-neutral-700">
                {similarBidStats.totalCount}건
              </span>
            </div>
            {similarBidStats.avgWinRate !== null && (
              <div className="flex items-center justify-between">
                <span className="text-xs text-neutral-500">평균 낙찰율</span>
                <span className="text-xs font-semibold text-neutral-700">
                  {(similarBidStats.avgWinRate * 100).toFixed(1)}%
                </span>
              </div>
            )}
            {similarBidStats.avgWinningPrice !== null && (
              <div className="flex items-center justify-between">
                <span className="text-xs text-neutral-500">평균 낙찰가</span>
                <span className="text-xs font-semibold text-neutral-700">
                  {(similarBidStats.avgWinningPrice / 100_000_000).toFixed(1)}억원
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
