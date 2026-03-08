/**
 * 공고 필터 바 컴포넌트
 */
'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

interface BidFilterBarProps {
  keyword: string;
  status: string;
  category: string;
  sortBy: string;
  sortOrder: string;
  onKeywordChange: (value: string) => void;
  onStatusChange: (value: string) => void;
  onCategoryChange: (value: string) => void;
  onSortChange: (sortBy: string, sortOrder: string) => void;
  onReset: () => void;
  totalCount?: number;
}

const STATUS_OPTIONS = [
  { value: '', label: '전체 상태' },
  { value: 'open', label: '모집중' },
  { value: 'closed', label: '마감' },
  { value: 'awarded', label: '낙찰' },
  { value: 'cancelled', label: '취소' },
];

const SORT_OPTIONS = [
  { value: 'deadline:asc', label: '마감일순' },
  { value: 'announcementDate:desc', label: '최신 공고순' },
  { value: 'budget:desc', label: '예산 높은순' },
  { value: 'budget:asc', label: '예산 낮은순' },
];

export function BidFilterBar({
  keyword,
  status,
  category,
  sortBy,
  sortOrder,
  onKeywordChange,
  onStatusChange,
  onCategoryChange,
  onSortChange,
  onReset,
  totalCount,
}: BidFilterBarProps) {
  const [localKeyword, setLocalKeyword] = useState(keyword);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // 외부 keyword 변경 시 로컬 상태 동기화
  useEffect(() => {
    setLocalKeyword(keyword);
  }, [keyword]);

  const handleKeywordChange = useCallback(
    (value: string) => {
      setLocalKeyword(value);
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        onKeywordChange(value);
      }, 300);
    },
    [onKeywordChange]
  );

  const currentSort = `${sortBy}:${sortOrder}`;
  const hasActiveFilters = keyword || status || category;

  return (
    <div className="bg-white border border-neutral-200 rounded-lg p-4 space-y-3">
      <div className="flex flex-wrap items-center gap-3">
        {/* 검색창 */}
        <div className="relative flex-1 min-w-[200px]">
          <svg
            className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0"
            />
          </svg>
          <input
            type="text"
            placeholder="공고명, 기관명 검색"
            value={localKeyword}
            onChange={(e) => handleKeywordChange(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-sm border border-neutral-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-300 focus:border-primary-400"
          />
        </div>

        {/* 상태 필터 */}
        <select
          value={status}
          onChange={(e) => onStatusChange(e.target.value)}
          className="py-2 pl-3 pr-8 text-sm border border-neutral-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-300 bg-white text-neutral-700"
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        {/* 분류 필터 */}
        <select
          value={category}
          onChange={(e) => onCategoryChange(e.target.value)}
          className="py-2 pl-3 pr-8 text-sm border border-neutral-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-300 bg-white text-neutral-700"
        >
          <option value="">전체 분류</option>
          <option value="용역">용역</option>
          <option value="물품">물품</option>
          <option value="공사">공사</option>
          <option value="기타">기타</option>
        </select>

        {/* 정렬 */}
        <select
          value={currentSort}
          onChange={(e) => {
            const [newSortBy, newSortOrder] = e.target.value.split(':');
            onSortChange(newSortBy, newSortOrder);
          }}
          className="py-2 pl-3 pr-8 text-sm border border-neutral-200 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-300 bg-white text-neutral-700"
        >
          {SORT_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        {/* 초기화 버튼 */}
        {hasActiveFilters && (
          <button
            onClick={onReset}
            className="flex items-center gap-1.5 px-3 py-2 text-sm text-neutral-500 hover:text-neutral-700 border border-neutral-200 rounded-md hover:bg-neutral-50 transition-colors"
          >
            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
            초기화
          </button>
        )}
      </div>

      {/* 결과 건수 */}
      {totalCount !== undefined && (
        <div className="text-xs text-neutral-400">
          총 <span className="font-semibold text-neutral-700">{totalCount.toLocaleString()}</span>건
          {hasActiveFilters && (
            <span className="ml-2 text-primary-600">필터 적용 중</span>
          )}
        </div>
      )}
    </div>
  );
}
