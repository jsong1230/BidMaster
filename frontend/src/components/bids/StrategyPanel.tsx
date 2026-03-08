/**
 * F-04 낙찰가 예측 및 투찰 전략 패널
 * - 낙찰가율 분포 시각화 (히스토그램)
 * - 3단계 추천 투찰가 범위 카드
 * - 전략 리포트 (계약방식별 전략 + 시장 인사이트)
 * - 투찰가 시뮬레이션 입력 폼
 */
'use client';

import { useState } from 'react';
import { bidsApi } from '@/lib/api/bids';
import type { StrategyResult, SimulationResult, RecommendedRange } from '@/types/strategy';

// ----------------------------------------------------------------
// 유틸 함수
// ----------------------------------------------------------------

function formatPrice(price: number): string {
  if (price >= 100_000_000) {
    return `${(price / 100_000_000).toFixed(1)}억원`;
  }
  if (price >= 10_000) {
    return `${(price / 10_000).toFixed(0)}만원`;
  }
  return `${price.toLocaleString()}원`;
}

function formatRate(rate: number): string {
  return `${(rate * 100).toFixed(1)}%`;
}

// ----------------------------------------------------------------
// 서브 컴포넌트: 리스크 배지
// ----------------------------------------------------------------

interface RiskBadgeProps {
  riskLevel: string;
  riskLabel: string;
}

function RiskBadge({ riskLevel, riskLabel }: RiskBadgeProps) {
  const styleMap: Record<string, string> = {
    safe: 'bg-green-100 text-green-700 border-green-200',
    moderate: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    aggressive: 'bg-red-100 text-red-700 border-red-200',
    over_safe: 'bg-blue-100 text-blue-700 border-blue-200',
    extreme: 'bg-purple-100 text-purple-700 border-purple-200',
  };
  const style = styleMap[riskLevel] ?? 'bg-neutral-100 text-neutral-700 border-neutral-200';

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold border ${style}`}>
      {riskLabel}
    </span>
  );
}

// ----------------------------------------------------------------
// 서브 컴포넌트: 낙찰가율 분포 미니 바 차트
// ----------------------------------------------------------------

interface WinRateHistogramProps {
  distribution: StrategyResult['winRateDistribution'];
}

function WinRateHistogram({ distribution }: WinRateHistogramProps) {
  const { mean, median, q25, q75, minRate, maxRate, sampleCount } = distribution;

  const stats = [
    { label: '평균', value: mean, color: 'text-blue-600' },
    { label: '중앙값', value: median, color: 'text-green-600' },
    { label: 'Q25', value: q25, color: 'text-neutral-500' },
    { label: 'Q75', value: q75, color: 'text-neutral-500' },
  ];

  // 간단한 box-plot 스타일 시각화
  const rangeWidth = maxRate - minRate;
  const q25Pct = rangeWidth > 0 ? ((q25 - minRate) / rangeWidth) * 100 : 25;
  const q75Pct = rangeWidth > 0 ? ((q75 - minRate) / rangeWidth) * 100 : 75;
  const medianPct = rangeWidth > 0 ? ((median - minRate) / rangeWidth) * 100 : 50;
  const meanPct = rangeWidth > 0 ? ((mean - minRate) / rangeWidth) * 100 : 50;

  return (
    <div className="space-y-3">
      {/* 샘플 수 안내 */}
      <div className="flex items-center justify-between text-xs text-neutral-500">
        <span>유사 공고 분석 ({sampleCount}건 기반)</span>
        <span>{formatRate(minRate)} ~ {formatRate(maxRate)}</span>
      </div>

      {/* Box Plot 시각화 */}
      <div className="relative h-10">
        {/* 배경 바 */}
        <div className="absolute inset-y-3 left-0 right-0 bg-neutral-100 rounded-full" />
        {/* IQR 박스 */}
        <div
          className="absolute inset-y-2 bg-blue-200 rounded"
          style={{ left: `${q25Pct}%`, width: `${q75Pct - q25Pct}%` }}
        />
        {/* 중앙값 선 */}
        <div
          className="absolute inset-y-0 w-0.5 bg-green-600"
          style={{ left: `${medianPct}%` }}
        />
        {/* 평균 마크 */}
        <div
          className="absolute top-2 bottom-2 w-1 bg-blue-600 rounded-full"
          style={{ left: `${meanPct}%` }}
        />
        {/* 범위 레이블 */}
        <div className="absolute bottom-0 left-0 text-xs text-neutral-400">{formatRate(minRate)}</div>
        <div className="absolute bottom-0 right-0 text-xs text-neutral-400">{formatRate(maxRate)}</div>
      </div>

      {/* 통계 수치 */}
      <div className="grid grid-cols-4 gap-2">
        {stats.map(({ label, value, color }) => (
          <div key={label} className="text-center">
            <div className={`text-sm font-semibold ${color}`}>{formatRate(value)}</div>
            <div className="text-xs text-neutral-400">{label}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ----------------------------------------------------------------
// 서브 컴포넌트: 추천 구간 카드
// ----------------------------------------------------------------

interface RangeSelectorProps {
  ranges: StrategyResult['recommendedRanges'];
  estimatedPrice: number | null;
  onSelectRange: (price: number) => void;
}

function RangeSelector({ ranges, estimatedPrice, onSelectRange }: RangeSelectorProps) {
  const levels = [
    { key: 'safe' as const, range: ranges.safe, icon: '🟢', bg: 'bg-green-50 border-green-200' },
    { key: 'moderate' as const, range: ranges.moderate, icon: '🟡', bg: 'bg-yellow-50 border-yellow-200' },
    { key: 'aggressive' as const, range: ranges.aggressive, icon: '🔴', bg: 'bg-red-50 border-red-200' },
  ];

  return (
    <div className="space-y-2">
      {levels.map(({ key, range, icon, bg }) => (
        <RangeCard
          key={key}
          range={range}
          icon={icon}
          bg={bg}
          estimatedPrice={estimatedPrice}
          onSelect={() => onSelectRange(Math.round((range.minPrice + range.maxPrice) / 2))}
        />
      ))}
    </div>
  );
}

interface RangeCardProps {
  range: RecommendedRange;
  icon: string;
  bg: string;
  estimatedPrice: number | null;
  onSelect: () => void;
}

function RangeCard({ range, icon, bg, onSelect }: RangeCardProps) {
  return (
    <div className={`border rounded-lg p-3 ${bg}`}>
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-1.5">
          <span className="text-sm">{icon}</span>
          <span className="text-xs font-semibold text-neutral-700">{range.label}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-neutral-500">낙찰 확률</span>
          <span className="text-sm font-bold text-neutral-800">{range.winProbability}%</span>
        </div>
      </div>
      <div className="flex items-center justify-between">
        <div className="text-xs text-neutral-600">
          <span className="font-medium">{formatPrice(range.minPrice)}</span>
          <span className="mx-1 text-neutral-400">~</span>
          <span className="font-medium">{formatPrice(range.maxPrice)}</span>
          <span className="ml-1 text-neutral-400">({formatRate(range.minRate)} ~ {formatRate(range.maxRate)})</span>
        </div>
        <button
          onClick={onSelect}
          className="text-xs px-2 py-1 bg-white border border-neutral-300 rounded hover:bg-neutral-50 text-neutral-600 transition-colors"
        >
          시뮬레이션
        </button>
      </div>
      <p className="text-xs text-neutral-500 mt-1">{range.description}</p>
    </div>
  );
}

// ----------------------------------------------------------------
// 서브 컴포넌트: 시뮬레이션 입력 + 결과
// ----------------------------------------------------------------

interface SimulateInputProps {
  bidId: string;
  initialPrice: number | null;
}

function SimulateInput({ bidId, initialPrice }: SimulateInputProps) {
  const [priceInput, setPriceInput] = useState<string>(
    initialPrice ? String(initialPrice) : ''
  );
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSimulate = async () => {
    const price = parseInt(priceInput.replace(/[^0-9]/g, ''), 10);
    if (isNaN(price) || price < 0) {
      setError('유효한 투찰 금액을 입력해주세요.');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await bidsApi.simulateBidStrategy(bidId, price);
      setResult(data);
    } catch {
      setError('시뮬레이션 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex gap-2">
        <div className="flex-1">
          <input
            type="text"
            value={priceInput}
            onChange={(e) => setPriceInput(e.target.value)}
            placeholder="투찰 금액 입력 (예: 410000000)"
            className="w-full px-3 py-2 text-sm border border-neutral-200 rounded-md focus:outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400"
          />
        </div>
        <button
          onClick={handleSimulate}
          disabled={isLoading}
          className="px-4 py-2 text-sm font-semibold bg-[#486581] text-white rounded-md hover:bg-[#334E68] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? '계산 중...' : '계산'}
        </button>
      </div>

      {error && (
        <p className="text-xs text-red-500">{error}</p>
      )}

      {result && (
        <SimulationResultCard result={result} />
      )}
    </div>
  );
}

// ----------------------------------------------------------------
// 서브 컴포넌트: 시뮬레이션 결과 카드
// ----------------------------------------------------------------

interface SimulationResultCardProps {
  result: SimulationResult;
}

function SimulationResultCard({ result }: SimulationResultCardProps) {
  const probabilityColor = result.winProbability >= 60
    ? 'text-green-600'
    : result.winProbability >= 40
    ? 'text-yellow-600'
    : 'text-red-600';

  return (
    <div className="bg-neutral-50 border border-neutral-200 rounded-lg p-4 space-y-3">
      {/* 결과 헤더 */}
      <div className="flex items-center justify-between">
        <div>
          <span className="text-xs text-neutral-500">투찰가율</span>
          <p className="text-lg font-bold text-neutral-800">{formatRate(result.bidRate)}</p>
        </div>
        <div className="text-center">
          <span className="text-xs text-neutral-500">낙찰 확률</span>
          <p className={`text-2xl font-bold ${probabilityColor}`}>{result.winProbability}%</p>
        </div>
        <div className="text-right">
          <span className="text-xs text-neutral-500">리스크</span>
          <div className="mt-1">
            <RiskBadge riskLevel={result.riskLevel} riskLabel={result.riskLabel} />
          </div>
        </div>
      </div>

      {/* 분석 텍스트 */}
      <p className="text-xs text-neutral-600 leading-relaxed">{result.analysis}</p>

      {/* 추천 구간 비교 */}
      <div className="space-y-1">
        <p className="text-xs font-semibold text-neutral-500">추천 구간 비교</p>
        {(['safe', 'moderate', 'aggressive'] as const).map((level) => {
          const labelMap = { safe: '낮은 리스크', moderate: '중간 리스크', aggressive: '높은 리스크' };
          const comparison = result.comparisonWithRecommended[level];
          const isIn = comparison.includes('범위 내');
          return (
            <div key={level} className="flex items-center justify-between text-xs">
              <span className="text-neutral-500">{labelMap[level]}</span>
              <span className={isIn ? 'text-green-600 font-semibold' : 'text-neutral-400'}>
                {comparison}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ----------------------------------------------------------------
// 서브 컴포넌트: 전략 리포트 카드
// ----------------------------------------------------------------

interface StrategyReportCardProps {
  report: StrategyResult['strategyReport'];
}

function StrategyReportCard({ report }: StrategyReportCardProps) {
  return (
    <div className="space-y-3">
      <div>
        <p className="text-xs font-semibold text-neutral-500 mb-1">계약 방식 전략</p>
        <p className="text-xs text-neutral-700 leading-relaxed">{report.contractMethodStrategy}</p>
      </div>
      <div>
        <p className="text-xs font-semibold text-neutral-500 mb-1">시장 인사이트</p>
        <p className="text-xs text-neutral-700 leading-relaxed">{report.marketInsight}</p>
      </div>
      {report.riskFactors.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-neutral-500 mb-1">리스크 요인</p>
          <ul className="space-y-0.5">
            {report.riskFactors.map((factor, idx) => (
              <li key={idx} className="text-xs text-neutral-700 flex items-start gap-1">
                <span className="text-neutral-400 mt-0.5">•</span>
                {factor}
              </li>
            ))}
          </ul>
        </div>
      )}
      {report.recommendations.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-neutral-500 mb-1">추천 사항</p>
          <ul className="space-y-0.5">
            {report.recommendations.map((rec, idx) => (
              <li key={idx} className="text-xs text-neutral-700 flex items-start gap-1">
                <span className="text-blue-400 mt-0.5">✓</span>
                {rec}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

// ----------------------------------------------------------------
// 메인 컴포넌트: StrategyPanel
// ----------------------------------------------------------------

interface StrategyPanelProps {
  bidId: string;
  strategyData: StrategyResult | null;
  isLoading: boolean;
  error: string | null;
}

export function StrategyPanel({ bidId, strategyData, isLoading, error }: StrategyPanelProps) {
  const [activeTab, setActiveTab] = useState<'ranges' | 'simulate' | 'report'>('ranges');
  const [simulatePrice, setSimulatePrice] = useState<number | null>(null);

  const handleSelectRangePrice = (price: number) => {
    setSimulatePrice(price);
    setActiveTab('simulate');
  };

  if (isLoading) {
    return (
      <div className="bg-white border border-neutral-200 rounded-lg p-5">
        <div className="animate-pulse space-y-3">
          <div className="h-4 w-24 bg-neutral-200 rounded" />
          <div className="h-20 bg-neutral-100 rounded" />
          <div className="h-16 bg-neutral-100 rounded" />
          <div className="h-16 bg-neutral-100 rounded" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white border border-neutral-200 rounded-lg p-5">
        <div className="text-center py-4">
          <svg className="w-8 h-8 text-neutral-300 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm text-neutral-500">{error}</p>
        </div>
      </div>
    );
  }

  if (!strategyData) {
    return null;
  }

  const estimatedPrice = strategyData.estimatedPrice ?? strategyData.budget;

  return (
    <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
      {/* 헤더 */}
      <div className="px-5 py-3.5 border-b border-neutral-100">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-neutral-700">투찰 전략 분석</h2>
          <span className="text-xs text-neutral-400">
            {strategyData.contractMethod} · {estimatedPrice ? formatPrice(estimatedPrice) : '예정가격 미확인'}
          </span>
        </div>
      </div>

      {/* 낙찰가율 분포 */}
      <div className="px-5 py-4 border-b border-neutral-50">
        <p className="text-xs font-semibold text-neutral-500 mb-3">낙찰가율 분포</p>
        <WinRateHistogram distribution={strategyData.winRateDistribution} />
      </div>

      {/* 탭 네비게이션 */}
      <div className="flex border-b border-neutral-100">
        {(['ranges', 'simulate', 'report'] as const).map((tab) => {
          const labelMap = { ranges: '추천 구간', simulate: '시뮬레이션', report: '전략 리포트' };
          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-2.5 text-xs font-medium transition-colors ${
                activeTab === tab
                  ? 'text-[#486581] border-b-2 border-[#486581] bg-blue-50/30'
                  : 'text-neutral-500 hover:text-neutral-700'
              }`}
            >
              {labelMap[tab]}
            </button>
          );
        })}
      </div>

      {/* 탭 콘텐츠 */}
      <div className="p-4">
        {activeTab === 'ranges' && (
          <RangeSelector
            ranges={strategyData.recommendedRanges}
            estimatedPrice={estimatedPrice}
            onSelectRange={handleSelectRangePrice}
          />
        )}

        {activeTab === 'simulate' && (
          <div className="space-y-3">
            <p className="text-xs text-neutral-500">
              투찰 금액을 입력하면 낙찰 확률과 리스크 레벨을 즉시 확인할 수 있습니다.
            </p>
            <SimulateInput
              bidId={bidId}
              initialPrice={simulatePrice}
            />
          </div>
        )}

        {activeTab === 'report' && (
          <StrategyReportCard report={strategyData.strategyReport} />
        )}
      </div>

      {/* 분석 시간 */}
      <div className="px-5 py-2 bg-neutral-50 border-t border-neutral-100">
        <p className="text-xs text-neutral-400 text-right">
          분석: {new Date(strategyData.analyzedAt).toLocaleDateString('ko-KR')}
        </p>
      </div>
    </div>
  );
}
