/**
 * 공고 상세 페이지
 * GET /bids/[id]
 */
'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { bidsApi } from '@/lib/api/bids';
import { HttpError } from '@/lib/api/client';
import type { BidDetail } from '@/types/bid';
import type { BidMatchResult } from '@/types/bid-match';
import type { ScoringResult } from '@/types/scoring';
import type { StrategyResult } from '@/types/strategy';
import { BidStatusBadge } from '@/components/bids/BidStatusBadge';
import { DeadlineBadge } from '@/components/bids/DeadlineBadge';
import { RecommendationBadge } from '@/components/bids/RecommendationBadge';
import { BidAttachmentList } from '@/components/bids/BidAttachmentList';
import { ScoringPanel, ScoringPanelSkeleton } from '@/components/bids/ScoringPanel';
import { StrategyPanel } from '@/components/bids/StrategyPanel';

function formatBudget(budget?: number): string {
  if (!budget) return '-';
  if (budget >= 100_000_000) return `${(budget / 100_000_000).toFixed(0)}억원 (${budget.toLocaleString()}원)`;
  if (budget >= 10_000) return `${(budget / 10_000).toFixed(0)}만원`;
  return `${budget.toLocaleString()}원`;
}

function formatDateTime(dateStr?: string): string {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleDateString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }) + ' ' + date.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
}

// 로딩 스켈레톤
function BidDetailSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <div className="flex gap-2">
            <div className="h-5 w-16 bg-neutral-200 rounded-full" />
            <div className="h-5 w-12 bg-neutral-200 rounded" />
          </div>
          <div className="h-7 w-96 bg-neutral-200 rounded" />
        </div>
        <div className="flex gap-2">
          <div className="h-9 w-32 bg-neutral-200 rounded-md" />
          <div className="h-9 w-28 bg-neutral-200 rounded-md" />
        </div>
      </div>
      <div className="grid grid-cols-3 gap-5 mt-6">
        <div className="col-span-2 space-y-4">
          <div className="bg-white border border-neutral-200 rounded-lg p-5 space-y-3">
            <div className="h-5 w-24 bg-neutral-200 rounded" />
            <div className="grid grid-cols-2 gap-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-4 bg-neutral-200 rounded" />
              ))}
            </div>
          </div>
        </div>
        <div>
          <div className="bg-white border border-neutral-200 rounded-lg p-5 space-y-4">
            <div className="h-5 w-24 bg-neutral-200 rounded" />
            <div className="flex justify-center">
              <div className="w-28 h-28 rounded-full bg-neutral-200" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// 매칭 점수 게이지 (SVG 원형)
function ScoreGauge({ score }: { score: number }) {
  const circumference = 2 * Math.PI * 15.9;
  const dasharray = `${(score / 100) * circumference} ${circumference}`;
  const strokeColor = score >= 70 ? '#0F9D58' : score >= 50 ? '#FFC107' : '#9E9E9E';

  return (
    <div className="relative w-32 h-32">
      <svg
        className="w-full h-full"
        viewBox="0 0 36 36"
        style={{ transform: 'rotate(-90deg)' }}
      >
        <circle
          cx="18"
          cy="18"
          r="15.9"
          fill="none"
          stroke="#E0E0E0"
          strokeWidth="2.5"
        />
        <circle
          cx="18"
          cy="18"
          r="15.9"
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

// 세부 점수 바
function ScoreBar({ label, score, note }: { label: string; score: number; note?: string }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-neutral-500">{label}</span>
        {note ? (
          <span className="text-xs text-neutral-300">{note}</span>
        ) : (
          <span className="text-xs font-semibold text-neutral-700">{score.toFixed(1)}</span>
        )}
      </div>
      <div className="w-full bg-neutral-100 rounded-full h-1.5">
        <div
          className="h-1.5 rounded-full bg-[#0F9D58]"
          style={{ width: `${score}%` }}
        />
      </div>
    </div>
  );
}

// 매칭 결과 섹션
function MatchSection({
  matchResult,
  isLoadingMatch,
  hasCompanyProfile,
}: {
  matchResult: BidMatchResult | null;
  isLoadingMatch: boolean;
  hasCompanyProfile: boolean;
}) {
  if (!hasCompanyProfile) {
    return (
      <div className="bg-neutral-50 border border-neutral-200 rounded-lg p-6 text-center">
        <svg className="w-12 h-12 text-neutral-300 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
        <p className="text-sm font-semibold text-neutral-700 mb-1">매칭 분석을 시작하려면</p>
        <p className="text-xs text-neutral-500 leading-relaxed mb-4">
          회사 프로필을 등록하면 이 공고와의<br />매칭 점수를 자동으로 분석해 드립니다.
        </p>
        <Link
          href="/settings/company"
          className="inline-block w-full px-4 py-2 text-sm font-semibold bg-[#486581] text-white rounded-md hover:bg-[#334E68] transition-colors text-center"
        >
          회사 프로필 등록하기
        </Link>
      </div>
    );
  }

  if (isLoadingMatch) {
    return (
      <div className="bg-white border border-neutral-200 rounded-lg p-8 text-center">
        <div className="w-12 h-12 mx-auto mb-4 rounded-full border-4 border-neutral-200 border-t-[#0F9D58] animate-spin" />
        <p className="text-sm font-semibold text-neutral-700">매칭 분석 중...</p>
        <p className="text-xs text-neutral-400 mt-1 leading-relaxed">
          회사 프로필과 공고 내용을<br />비교하고 있습니다.
        </p>
      </div>
    );
  }

  if (!matchResult) return null;

  return (
    <>
      <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
        <div className="px-5 py-3.5 border-b border-neutral-100">
          <h2 className="text-sm font-semibold text-neutral-700">매칭 분석 결과</h2>
        </div>
        <div className="p-5">
          {/* 점수 게이지 */}
          <div className="flex flex-col items-center mb-5">
            <ScoreGauge score={matchResult.totalScore} />
            <div className="mt-2">
              <RecommendationBadge recommendation={matchResult.recommendation} />
            </div>
          </div>

          {/* 세부 점수 */}
          <div className="space-y-2.5">
            <ScoreBar label="적합도" score={matchResult.suitabilityScore} />
            <ScoreBar
              label="경쟁 강도"
              score={matchResult.competitionScore}
              note={matchResult.competitionScore === 0 ? '분석 예정' : undefined}
            />
            <ScoreBar
              label="역량"
              score={matchResult.capabilityScore}
              note={matchResult.capabilityScore === 0 ? '분석 예정' : undefined}
            />
            <ScoreBar
              label="시장 환경"
              score={matchResult.marketScore}
              note={matchResult.marketScore === 0 ? '분석 예정' : undefined}
            />
          </div>

          {/* 분석 일시 */}
          <p className="text-xs text-neutral-300 text-right mt-3">
            분석 {new Date(matchResult.analyzedAt).toLocaleDateString('ko-KR')} {new Date(matchResult.analyzedAt).toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' })}
          </p>
        </div>
      </div>

      {/* 추천 사유 카드 */}
      {matchResult.recommendationReason && (
        <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
          <div className="px-5 py-3.5 border-b border-neutral-100">
            <h2 className="text-sm font-semibold text-neutral-700">추천 사유</h2>
          </div>
          <div className="p-5">
            <p className="text-sm text-neutral-700 leading-relaxed">
              {matchResult.recommendationReason}
            </p>
          </div>
        </div>
      )}
    </>
  );
}

export default function BidDetailPage() {
  const params = useParams();
  const bidId = params.id as string;

  const [bid, setBid] = useState<BidDetail | null>(null);
  const [matchResult, setMatchResult] = useState<BidMatchResult | null>(null);
  const [scoringResult, setScoringResult] = useState<ScoringResult | null>(null);
  const [strategyData, setStrategyData] = useState<StrategyResult | null>(null);
  const [isLoadingBid, setIsLoadingBid] = useState(true);
  const [isLoadingMatch, setIsLoadingMatch] = useState(true);
  const [isLoadingScoring, setIsLoadingScoring] = useState(true);
  const [isLoadingStrategy, setIsLoadingStrategy] = useState(true);
  const [hasCompanyProfile, setHasCompanyProfile] = useState(true);
  const [bidError, setBidError] = useState<string | null>(null);
  const [strategyError, setStrategyError] = useState<string | null>(null);

  useEffect(() => {
    if (!bidId) return;

    // 공고 상세 + 매칭 결과 + 스코어링 + 전략 분석 병렬 호출
    setIsLoadingBid(true);
    setIsLoadingMatch(true);
    setIsLoadingScoring(true);
    setIsLoadingStrategy(true);

    bidsApi.getBid(bidId)
      .then((data) => {
        setBid(data);
      })
      .catch((err: unknown) => {
        const error = err as { status?: number; message?: string };
        if (error?.status === 404) {
          setBidError('공고를 찾을 수 없습니다.');
        } else {
          setBidError(error?.message ?? '공고 정보를 불러올 수 없습니다.');
        }
      })
      .finally(() => {
        setIsLoadingBid(false);
      });

    bidsApi.getBidMatches(bidId)
      .then((data) => {
        setMatchResult(data);
        setHasCompanyProfile(true);
      })
      .catch((err: unknown) => {
        const error = err as HttpError;
        if (error?.code === 'COMPANY_001') {
          setHasCompanyProfile(false);
        }
        // 기타 오류는 매칭 없음으로 처리
      })
      .finally(() => {
        setIsLoadingMatch(false);
      });

    // 스코어링 결과 조회 (lazy evaluation)
    bidsApi.getBidScoring(bidId)
      .then((data) => {
        setScoringResult(data);
        setHasCompanyProfile(true);
      })
      .catch((err: unknown) => {
        const error = err as HttpError;
        if (error?.code === 'COMPANY_001') {
          setHasCompanyProfile(false);
        }
        // 스코어링 실패는 무시 (매칭 결과로 폴백)
      })
      .finally(() => {
        setIsLoadingScoring(false);
      });

    bidsApi.getBidStrategy(bidId)
      .then((data) => {
        setStrategyData(data);
      })
      .catch(() => {
        setStrategyError('전략 분석 정보를 불러올 수 없습니다.');
      })
      .finally(() => {
        setIsLoadingStrategy(false);
      });
  }, [bidId]);

  if (isLoadingBid) {
    return (
      <div className="p-6 max-w-screen-lg mx-auto">
        <BidDetailSkeleton />
      </div>
    );
  }

  if (bidError) {
    return (
      <div className="p-6 max-w-screen-lg mx-auto">
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <svg className="w-12 h-12 text-neutral-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-sm font-semibold text-neutral-700 mb-1">{bidError}</p>
          <Link href="/bids" className="mt-4 text-sm text-[#486581] hover:underline">
            목록으로 돌아가기
          </Link>
        </div>
      </div>
    );
  }

  if (!bid) return null;

  const isClosed = bid.status !== 'open';

  return (
    <div className="p-6 max-w-screen-lg mx-auto">
      {/* 브레드크럼 */}
      <nav className="flex items-center gap-1.5 text-xs text-neutral-400 mb-4">
        <Link href="/dashboard" className="hover:text-neutral-700 transition-colors">대시보드</Link>
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
        <Link href="/bids" className="hover:text-neutral-700 transition-colors">공고 목록</Link>
        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
        <span className="text-neutral-600 truncate max-w-xs">{bid.title}</span>
      </nav>

      {/* 마감 안내 배너 */}
      {isClosed && (
        <div className="mb-4 flex items-center gap-2 px-4 py-3 bg-neutral-100 border border-neutral-200 rounded-lg text-sm text-neutral-600">
          <svg className="w-4 h-4 text-neutral-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          이 공고는 마감되었습니다. 제안서 생성이 불가합니다.
        </div>
      )}

      {/* 상세 헤더 */}
      <div className="flex items-start justify-between gap-4 mb-5">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <BidStatusBadge status={bid.status} />
            <DeadlineBadge deadline={bid.deadline} />
            {bid.bidNumber && (
              <span className="text-xs text-neutral-400">공고번호: {bid.bidNumber}</span>
            )}
          </div>
          <h1 className={`text-xl font-bold leading-snug ${isClosed ? 'text-neutral-600' : 'text-neutral-800'}`}>
            {bid.title}
          </h1>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <a
            href={`https://www.g2b.go.kr/`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium border border-neutral-200 rounded-md text-neutral-600 bg-white hover:bg-neutral-50 transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            나라장터 원문
          </a>
          <button
            disabled={isClosed}
            className={`inline-flex items-center gap-1.5 px-4 py-2 text-sm font-semibold rounded-md transition-colors ${
              isClosed
                ? 'bg-neutral-200 text-neutral-400 cursor-not-allowed'
                : 'bg-[#486581] text-white hover:bg-[#334E68]'
            }`}
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            제안서 생성
          </button>
        </div>
      </div>

      {/* 본문 2컬럼 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* 좌: 메인 콘텐츠 (2/3) */}
        <div className="lg:col-span-2 space-y-4">
          {/* 기본 정보 카드 */}
          <div className={`bg-white border border-neutral-200 rounded-lg overflow-hidden ${isClosed ? 'opacity-80' : ''}`}>
            <div className="px-5 py-3.5 border-b border-neutral-100">
              <h2 className="text-sm font-semibold text-neutral-700">기본 정보</h2>
            </div>
            <div className="p-5">
              <div className="grid grid-cols-2 gap-x-8 gap-y-3 text-sm">
                <div className="flex gap-3">
                  <span className="text-neutral-400 w-24 flex-shrink-0">발주기관</span>
                  <span className="font-medium text-neutral-800">{bid.organization}</span>
                </div>
                {bid.region && (
                  <div className="flex gap-3">
                    <span className="text-neutral-400 w-24 flex-shrink-0">지역</span>
                    <span className="font-medium text-neutral-800">{bid.region}</span>
                  </div>
                )}
                {bid.category && (
                  <div className="flex gap-3">
                    <span className="text-neutral-400 w-24 flex-shrink-0">공고 분류</span>
                    <span className="font-medium text-neutral-800">{bid.category}</span>
                  </div>
                )}
                {bid.bidType && (
                  <div className="flex gap-3">
                    <span className="text-neutral-400 w-24 flex-shrink-0">입찰 유형</span>
                    <span className="font-medium text-neutral-800">{bid.bidType}</span>
                  </div>
                )}
                {bid.contractMethod && (
                  <div className="flex gap-3">
                    <span className="text-neutral-400 w-24 flex-shrink-0">계약 방식</span>
                    <span className="font-medium text-neutral-800">{bid.contractMethod}</span>
                  </div>
                )}
                {bid.budget && (
                  <div className="flex gap-3">
                    <span className="text-neutral-400 w-24 flex-shrink-0">추정가격</span>
                    <span className="font-medium text-neutral-800">{formatBudget(bid.budget)}</span>
                  </div>
                )}
                {bid.announcementDate && (
                  <div className="flex gap-3">
                    <span className="text-neutral-400 w-24 flex-shrink-0">공고일</span>
                    <span className="font-medium text-neutral-800">{bid.announcementDate}</span>
                  </div>
                )}
                <div className="flex gap-3">
                  <span className="text-neutral-400 w-24 flex-shrink-0">마감일시</span>
                  <span className="font-medium text-neutral-800">{formatDateTime(bid.deadline)}</span>
                </div>
                {bid.openDate && (
                  <div className="flex gap-3">
                    <span className="text-neutral-400 w-24 flex-shrink-0">개찰일시</span>
                    <span className="font-medium text-neutral-800">{formatDateTime(bid.openDate)}</span>
                  </div>
                )}
                {bid.scoringCriteria && (
                  <div className="flex gap-3">
                    <span className="text-neutral-400 w-24 flex-shrink-0">평가 기준</span>
                    <span className="font-medium text-neutral-800">
                      기술 {bid.scoringCriteria.technical ?? '-'}점 / 가격 {bid.scoringCriteria.price ?? '-'}점
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* 공고 내용 카드 */}
          {bid.description && (
            <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
              <div className="px-5 py-3.5 border-b border-neutral-100">
                <h2 className="text-sm font-semibold text-neutral-700">공고 내용</h2>
              </div>
              <div className="p-5">
                <p className="text-sm text-neutral-700 leading-relaxed whitespace-pre-wrap">
                  {bid.description}
                </p>
              </div>
            </div>
          )}

          {/* 첨부파일 카드 */}
          <div className="bg-white border border-neutral-200 rounded-lg overflow-hidden">
            <div className="px-5 py-3.5 border-b border-neutral-100 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-neutral-700">첨부파일</h2>
              {bid.attachments.length > 0 && (
                <span className="text-xs text-neutral-400">{bid.attachments.length}건</span>
              )}
            </div>
            <BidAttachmentList attachments={bid.attachments} />
          </div>
        </div>

        {/* 우: 스코어링/전략/매칭 사이드바 (1/3) */}
        <div className="space-y-4">
          {/* 낙찰 가능성 스코어링 (F-02) */}
          {hasCompanyProfile && (
            isLoadingScoring ? (
              <ScoringPanelSkeleton />
            ) : scoringResult ? (
              <ScoringPanel scoring={scoringResult} />
            ) : null
          )}

          {/* 투찰 전략 패널 (F-04) */}
          <StrategyPanel
            bidId={bidId}
            strategyData={strategyData}
            isLoading={isLoadingStrategy}
            error={strategyError}
          />

          <MatchSection
            matchResult={matchResult}
            isLoadingMatch={isLoadingMatch}
            hasCompanyProfile={hasCompanyProfile}
          />
        </div>
      </div>
    </div>
  );
}
