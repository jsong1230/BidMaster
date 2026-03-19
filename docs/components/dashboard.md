# F-06 대시보드 컴포넌트 문서

## 개요

F-06 입찰 현황 대시보드 기능의 프론트엔드 컴포넌트 문서입니다.

---

## 파일 구조

```
frontend/src/
├── types/dashboard.ts              — 타입 정의
├── lib/api/dashboard.ts            — API 클라이언트
├── lib/stores/dashboard-store.ts   — Zustand 스토어
├── lib/utils/format.ts             — 포맷 유틸리티
└── components/dashboard/
    ├── KpiCard.tsx                 — KPI 카드
    ├── PipelineBoard.tsx           — 칸반 보드
    ├── PipelineColumn.tsx          — 칸반 컬럼
    ├── PipelineCard.tsx            — 칸반 카드
    ├── DeadlineWidget.tsx          — 마감 임박 위젯
    ├── WinRateTrend.tsx            — 낙찰률 추이 차트
    └── StatisticsChart.tsx         — 월별 통계 차트
```

---

## KpiCard

**경로**: `frontend/src/components/dashboard/KpiCard.tsx`

### Props

| 이름 | 타입 | 필수 | 설명 |
|------|------|------|------|
| icon | ReactNode | O | 아이콘 요소 |
| value | string | O | 표시할 숫자/값 |
| label | string | O | 카드 라벨 |
| subText | string | X | 보조 텍스트 (예: 금액) |
| iconBgClass | string | O | 아이콘 배경 Tailwind 클래스 |
| iconColorClass | string | O | 아이콘 색상 Tailwind 클래스 |
| onClick | () => void | X | 클릭 핸들러 (지정 시 버튼 역할) |
| isLoading | boolean | X | 스켈레톤 로딩 상태 |

### 사용 예시

```tsx
<KpiCard
  icon={<TrophyIcon className="w-5 h-5" />}
  value="3"
  label="낙찰"
  subText="15억원"
  iconBgClass="bg-green-50"
  iconColorClass="text-green-500"
  onClick={() => router.push('/bids/wins')}
  isLoading={isLoadingSummary}
/>
```

---

## PipelineBoard

**경로**: `frontend/src/components/dashboard/PipelineBoard.tsx`

5열 칸반 보드. 데스크톱에서는 5열 가로 배치, 모바일에서는 탭 전환.

### Props

| 이름 | 타입 | 필수 | 설명 |
|------|------|------|------|
| pipeline | PipelineData \| null | O | 파이프라인 데이터 |
| isLoading | boolean | O | 로딩 상태 |
| onStatusChange | (bidId, newStatus) => Promise<void> | X | 상태 변경 핸들러 |

---

## PipelineCard

**경로**: `frontend/src/components/dashboard/PipelineCard.tsx`

칸반 카드. 공고명/기관/예산/마감일/매칭점수/상태 드롭다운 포함.

### Props

| 이름 | 타입 | 필수 | 설명 |
|------|------|------|------|
| item | PipelineItem | O | 파이프라인 아이템 |
| currentStatus | TrackingStatusType | O | 현재 상태 |
| onStatusChange | (bidId, newStatus) => Promise<void> | X | 상태 변경 핸들러 |
| isLost | boolean | X | lost 상태 (흐린 색상 처리) |

---

## DeadlineWidget

**경로**: `frontend/src/components/dashboard/DeadlineWidget.tsx`

마감 임박 공고 목록. D-3 이하는 error 색상, D-4~7은 warning 색상.

### Props

| 이름 | 타입 | 필수 | 설명 |
|------|------|------|------|
| deadlines | UpcomingDeadline[] | O | 마감 임박 공고 목록 |
| isLoading | boolean | X | 로딩 상태 |

---

## WinRateTrend

**경로**: `frontend/src/components/dashboard/WinRateTrend.tsx`

월별 낙찰률 추이 AreaChart (Recharts). SSR 비활성화 동적 임포트.

### Props

| 이름 | 타입 | 필수 | 설명 |
|------|------|------|------|
| data | MonthlyStat[] | O | 월별 통계 데이터 |
| isLoading | boolean | X | 로딩 상태 |

---

## StatisticsChart

**경로**: `frontend/src/components/dashboard/StatisticsChart.tsx`

월별 참여/낙찰 건수 BarChart (Recharts). SSR 비활성화 동적 임포트.

### Props

| 이름 | 타입 | 필수 | 설명 |
|------|------|------|------|
| data | MonthlyStat[] | O | 월별 통계 데이터 |
| isLoading | boolean | X | 로딩 상태 |

---

## 스토어 (dashboard-store.ts)

**경로**: `frontend/src/lib/stores/dashboard-store.ts`

### 상태

| 이름 | 타입 | 설명 |
|------|------|------|
| summary | DashboardSummary \| null | KPI 요약 |
| pipeline | PipelineData \| null | 파이프라인 데이터 |
| statistics | StatisticsData \| null | 통계 데이터 |
| isLoadingSummary | boolean | KPI 로딩 중 |
| isLoadingPipeline | boolean | 파이프라인 로딩 중 |
| isLoadingStats | boolean | 통계 로딩 중 |
| selectedPeriod | string | 선택된 기간 |

### 액션

| 이름 | 설명 |
|------|------|
| fetchSummary(period?) | KPI 요약 조회 |
| fetchPipeline() | 파이프라인 조회 |
| fetchStatistics(months?) | 통계 조회 |
| fetchAll(period?) | 3개 API 병렬 호출 |
| updateTrackingStatus(bidId, data) | 낙관적 업데이트 + API 호출 |
| setPeriod(period) | 기간 변경 + summary 재조회 |
| startPolling() | 30초 폴링 시작 (탭 비활성 시 중지) |
| stopPolling() | 폴링 중지 |

---

## 페이지

| 경로 | 파일 | 설명 |
|------|------|------|
| /dashboard | `app/(main)/(dashboard)/dashboard/page.tsx` | 대시보드 홈 |
| /pipeline | `app/(main)/(dashboard)/pipeline/page.tsx` | 파이프라인 칸반 |
| /bids/wins | `app/(main)/(dashboard)/bids/wins/page.tsx` | 낙찰 이력 |

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-03-19 | F-06 프론트엔드 구현 완료 |
