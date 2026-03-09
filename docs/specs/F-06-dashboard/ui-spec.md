# F-06 입찰 현황 대시보드 -- UI 설계서

## 화면 목록

| 화면명 | 경로 | 설명 |
|--------|------|------|
| 대시보드 홈 | `/dashboard` | KPI 카드 + 파이프라인 미니뷰 + 마감 임박 + 월별 트렌드 차트 |
| 입찰 파이프라인 | `/pipeline` | 칸반 보드 형태 전체 파이프라인 (상태별 컬럼) |
| 낙찰 이력 | `/bids/wins` | 낙찰 이력 목록 + ROI 요약 |

---

## 디자인 방향

- **톤앤매너**: 정보 밀도 높은 데이터 대시보드. Monday.com/Linear 스타일의 깔끔한 위젯 레이아웃
- **색상**: design-system.md 토큰 그대로 사용. KPI 카드는 semantic 색상(success, info, warning) 활용. 파이프라인 컬럼 헤더에 상태별 색상 적용
- **타이포그래피**: KPI 숫자는 weight-700 + font-size 32px. 카드 제목 weight-600, 보조 텍스트 weight-400
- **레이아웃 패턴**: 글로벌 셸(사이드바 240px + 메인 영역) 위에 위젯 그리드 구성. 대시보드는 4열 KPI + 2행 콘텐츠 레이아웃
- **반응형**: 모바일(375px) 1열 스택 / 태블릿(768px) 2열 / 데스크톱(1024px+) 4열 KPI + 2열 콘텐츠

---

## 컴포넌트 계층

### 대시보드 홈 (`/dashboard`)

- `DashboardPage`
  - `PageHeader` (페이지 제목 "대시보드" + 기간 선택 드롭다운)
  - `KpiSection` (상단 KPI 카드 그리드)
    - `KpiCard` (참여 공고)
      - 아이콘: FileText (Lucide)
      - 숫자: participationCount
      - 라벨: "이번 달 참여"
      - 색상: info
    - `KpiCard` (제출 완료)
      - 아이콘: Send (Lucide)
      - 숫자: submissionCount
      - 라벨: "제출 완료"
      - 색상: primary
    - `KpiCard` (낙찰)
      - 아이콘: Trophy (Lucide)
      - 숫자: wonCount
      - 라벨: "낙찰"
      - 서브: totalWonAmount (금액 포맷)
      - 색상: success
    - `KpiCard` (낙찰률)
      - 아이콘: TrendingUp (Lucide)
      - 숫자: winRate + "%"
      - 라벨: "낙찰률"
      - 색상: secondary
  - `ContentGrid` (2열 콘텐츠 영역)
    - **[좌측]** `PipelineMiniView`
      - `SectionHeader` ("입찰 파이프라인" + "전체보기" 링크)
      - `PipelineSummaryBar` (상태별 가로 막대형 카운트)
        - 5단계 가로 바 (interested/participating/submitted/won/lost)
        - 각 바에 카운트 숫자 표시
      - `PipelineRecentItems` (최근 변경된 3건)
        - `PipelineItemRow` (공고명 + 상태 배지 + 마감일)
    - **[우측]** `RightPanel`
      - `DeadlineWidget`
        - `SectionHeader` ("마감 임박" + 알림 아이콘)
        - `DeadlineList`
          - `DeadlineItem` (공고명 + D-day 배지 + 상태)
            - D-3 이하: error 색상 배지
            - D-4~D-7: warning 색상 배지
      - `WinRateTrendChart`
        - `SectionHeader` ("월별 낙찰률 추이")
        - `LineChart` (Recharts) (x: 월, y: 낙찰률 %)
          - 라인: secondary-500 색상
          - 영역: secondary-50 채우기
          - 데이터 포인트 hover 시 tooltip

### 입찰 파이프라인 (`/pipeline`)

- `PipelinePage`
  - `PageHeader` ("입찰 파이프라인" + 총 건수)
  - `PipelineBoard` (칸반 보드)
    - `PipelineColumn` (interested: "관심")
      - `ColumnHeader` (라벨 + 카운트 배지)
        - 색상: info-500 상단 보더
      - `PipelineCard` (반복)
        - `CardHeader` (공고명 1줄 ellipsis)
        - `CardMeta` (기관명 + 예산)
        - `DeadlineBadge` (마감일 D-day)
        - `MatchScoreBadge` (매칭 점수, 있는 경우)
        - `StatusDropdown` (상태 변경 드롭다운)
        - `CardFooter` (최종 업데이트 시간)
    - `PipelineColumn` (participating: "참여")
      - 색상: primary-500 상단 보더
      - ... (동일 구조)
    - `PipelineColumn` (submitted: "제출")
      - 색상: warning-500 상단 보더
      - `PipelineCard` (+ myBidPrice 표시)
    - `PipelineColumn` (won: "낙찰")
      - 색상: success-500 상단 보더
      - `PipelineCard` (+ 낙찰가 표시)
    - `PipelineColumn` (lost: "실패")
      - 색상: error-500 상단 보더
      - `PipelineCard` (흐린 색상 처리)

### 낙찰 이력 (`/bids/wins`)

- `WinsPage`
  - `PageHeader` ("낙찰 이력" + 총 건수)
  - `WinsSummaryCards` (요약 KPI)
    - `KpiCard` (총 낙찰 건수)
    - `KpiCard` (총 낙찰 금액)
    - `KpiCard` (평균 낙찰가)
    - `KpiCard` (평균 낙찰률)
  - `WinsFilterBar`
    - `DateRangeFilter` (시작일/종료일)
    - `SortControl` (결과일순/금액순)
  - `WinsTable` (데스크톱 테이블)
    - `WinsTableRow`
      - 공고명 (링크 -> 공고 상세)
      - 발주기관
      - 추정가격
      - 투찰가
      - 낙찰률 (투찰가/추정가)
      - 결과일
  - `WinsCardList` (모바일 카드)
    - `WinCard`
  - `Pagination`

---

## 상태 명세

### 대시보드 홈

| 컴포넌트 | 상태 | 타입 | 설명 |
|----------|------|------|------|
| `DashboardPage` | `summary` | `DashboardSummary \| null` | KPI 요약 데이터 |
| `DashboardPage` | `pipeline` | `PipelineData \| null` | 파이프라인 데이터 |
| `DashboardPage` | `statistics` | `StatisticsData \| null` | 통계 데이터 |
| `DashboardPage` | `isLoadingSummary` | `boolean` | KPI 로딩 중 |
| `DashboardPage` | `isLoadingPipeline` | `boolean` | 파이프라인 로딩 중 |
| `DashboardPage` | `isLoadingStats` | `boolean` | 통계 로딩 중 |
| `PageHeader` | `period` | `string` | 선택된 기간 |

### 파이프라인

| 컴포넌트 | 상태 | 타입 | 설명 |
|----------|------|------|------|
| `PipelinePage` | `pipeline` | `PipelineData \| null` | 파이프라인 전체 데이터 |
| `PipelinePage` | `isLoading` | `boolean` | 로딩 중 |
| `PipelineCard` | `isUpdating` | `boolean` | 상태 변경 중 (낙관적 업데이트) |
| `StatusDropdown` | `selectedStatus` | `string` | 선택된 상태 |

### 낙찰 이력

| 컴포넌트 | 상태 | 타입 | 설명 |
|----------|------|------|------|
| `WinsPage` | `wins` | `WinItem[]` | 낙찰 목록 |
| `WinsPage` | `isLoading` | `boolean` | 로딩 중 |
| `WinsPage` | `pagination` | `PaginationMeta` | 페이지 정보 |
| `WinsFilterBar` | `startDate` | `string \| null` | 시작일 |
| `WinsFilterBar` | `endDate` | `string \| null` | 종료일 |
| `WinsFilterBar` | `sortBy` | `string` | 정렬 기준 |
| `WinsFilterBar` | `sortOrder` | `'asc' \| 'desc'` | 정렬 방향 |

---

## 인터랙션 명세

### 대시보드 홈

- 페이지 진입 -> 3개 API 병렬 호출 (summary + pipeline + statistics)
- 기간 드롭다운 변경 -> summary API 재호출 (기간 파라미터 변경)
- KPI 카드 클릭 -> 해당 섹션 이동 (낙찰 카드 -> /bids/wins)
- "전체보기" 클릭 -> /pipeline 이동
- 마감 임박 아이템 클릭 -> /bids/[bidId] 이동
- 30초 폴링 -> summary + pipeline만 갱신 (statistics는 수동)
- 브라우저 탭 비활성 -> 폴링 중지, 활성 시 즉시 1회 호출 후 폴링 재개

### 파이프라인

- 페이지 진입 -> GET /dashboard/pipeline 호출
- 상태 드롭다운 변경 -> POST /bids/{id}/tracking 호출
  - 낙관적 업데이트: 즉시 UI 이동
  - 성공: toast "상태가 변경되었습니다"
  - 실패: 롤백 + 에러 toast
- 카드 클릭 (제목 영역) -> /bids/[bidId] 이동
- 30초 폴링 -> pipeline 데이터 갱신

### 낙찰 이력

- 페이지 진입 -> GET /bids/wins 호출
- 날짜 필터 변경 -> API 재호출
- 정렬 변경 -> API 재호출
- 공고명 클릭 -> /bids/[bidId] 이동
- 페이지 변경 -> 목록 상단으로 스크롤

---

## 레이아웃 상세

### 대시보드 홈 (데스크톱)

```
+------------------------------------------------------------+
|  헤더 (글로벌 셸)                                            |
+----------+-------------------------------------------------+
|          |  대시보드                    [이번 달 v]          |
|  사이드  +-------------------------------------------------+
|  바      |  [참여 공고]  [제출 완료]  [낙찰]   [낙찰률]      |
|          |    12          8          3          42.8%        |
|  (글로벌 |  이번 달 참여  제출 완료   15억원     +5.2%       |
|   셸)    +-------------------------------------------------+
|          |  입찰 파이프라인     [전체보기 >]  |  마감 임박    |
|          |  ------------------------------ |  -----------  |
|          |  관심 5  참여 3  제출 2  낙찰 1  실패 1  |  D-2 정보시스템... |
|          |  ==========[=====][===][=][ ]    |  D-5 AI 행정... |
|          |                                  |  D-7 클라우드... |
|          |  최근 변경                        |               |
|          |  - AI 행정 서비스 [참여] D-5      |  월별 낙찰률   |
|          |  - 데이터 분석 [제출] D-3         |  -----------  |
|          |  - 보안 시스템 [낙찰] -           |   /\    /\    |
|          |                                  |  /  \  /  \   |
|          |                                  | /    \/    \  |
+----------+-------------------------------------------------+
```

### 파이프라인 (데스크톱)

```
+------------------------------------------------------------+
|  입찰 파이프라인                          총 12건            |
+------------------------------------------------------------+
|  관심 (5)     | 참여 (3)     | 제출 (2)   | 낙찰 (1) | 실패 (1) |
|  ============ | ============ | ========== | ======== | ======== |
|  +-----------+| +-----------+| +----------+| +--------+| +--------+|
|  | AI 행정    || | 정보시스템 || | 데이터    || | 보안   || | 네트워크||
|  | 과학기술부 || | 행정안전부 || | 기상청    || | 국방부 || | 교육부  ||
|  | 2억       || | 5억       || | 1.5억    || | 3억   || | 1억    ||
|  | [D-6]     || | [D-3]     || | 투찰가   || | 4.5억 || |        ||
|  | 78.5점    || | 65.0점    || | 1.35억   || |       || |        ||
|  | [상태 v]  || | [상태 v]  || | [상태 v] || |       || |        ||
|  | 3시간 전  || | 1일 전    || | 방금 전  || |       || |        ||
|  +-----------+| +-----------+| +----------+| +--------+| +--------+|
|  +-----------+| +-----------+|            |          |          |
|  | 클라우드   || | 웹서비스   ||            |          |          |
|  | ...       || | ...       ||            |          |          |
|  +-----------+| +-----------+|            |          |          |
+------------------------------------------------------------+
```

### 낙찰 이력 (데스크톱)

```
+------------------------------------------------------------+
|  낙찰 이력                                    총 14건        |
+------------------------------------------------------------+
|  [총 14건]  [75억원]   [5.36억]    [87.5%]                   |
|  총 낙찰    총 낙찰금액 평균 낙찰가  평균 낙찰률              |
+------------------------------------------------------------+
|  [시작일          ] [종료일          ] [결과일순 v]           |
+------------------------------------------------------------+
|  공고명               기관       추정가   투찰가   낙찰률  결과일  |
|  ------------------------------------------------------------|
|  보안시스템 구축       국방부     3.5억    3.0억    85.7%  03-05  |
|  데이터센터 이전       기상청     2.0억    1.8억    90.0%  02-28  |
|  ...                                                          |
+------------------------------------------------------------+
|             [1] [2] ...                                       |
+------------------------------------------------------------+
```

---

## 화면별 상태 시나리오

### 대시보드 홈

| 시나리오 | UI 표현 |
|----------|---------|
| 초기 로딩 | KPI 카드 4개 스켈레톤 + 콘텐츠 영역 스켈레톤 |
| 데이터 없음 (신규 사용자) | KPI 모두 0 표시 + 파이프라인 빈 상태 안내 "공고에 관심을 표시하면 파이프라인이 시작됩니다" |
| 정상 데이터 | KPI 숫자 + 파이프라인 요약 + 마감 임박 목록 + 차트 |
| 폴링 갱신 | 데이터 변경 시 해당 위젯만 부드럽게 갱신 (fade transition) |
| API 에러 | 해당 위젯에 "데이터를 불러올 수 없습니다" + 재시도 버튼 |

### 파이프라인

| 시나리오 | UI 표현 |
|----------|---------|
| 로딩 중 | 5열 스켈레톤 카드 |
| 빈 파이프라인 | 5열 모두 빈 상태, 중앙 안내: "아직 추적 중인 입찰이 없습니다" + "공고 목록으로 이동" CTA |
| 정상 데이터 | 5열 칸반, 각 카드에 공고 정보 |
| 상태 변경 중 | 카드에 스피너 오버레이, 성공 시 해당 컬럼으로 이동 애니메이션 |
| 상태 변경 실패 | 에러 toast + 카드 원위치 |

### 낙찰 이력

| 시나리오 | UI 표현 |
|----------|---------|
| 로딩 중 | 요약 KPI 스켈레톤 + 테이블 행 스켈레톤 |
| 낙찰 없음 | 빈 상태: "아직 낙찰 이력이 없습니다" |
| 정상 데이터 | 요약 KPI + 테이블 |
| 필터 결과 없음 | "해당 기간에 낙찰 이력이 없습니다" + 필터 초기화 |

---

## 파이프라인 상태 색상

| 상태 | 컬럼 상단 보더 | 카운트 배지 | 의미 |
|------|---------------|------------|------|
| interested | info-500 (`#2196F3`) | info-50 bg / info-700 text | 관심 표시 |
| participating | primary-500 (`#627D98`) | primary-50 bg / primary-700 text | 참여 결정 |
| submitted | warning-500 (`#FFC107`) | warning-50 bg / warning-700 text | 제출 완료 |
| won | success-500 (`#4CAF50`) | success-50 bg / success-700 text | 낙찰 |
| lost | error-500 (`#F44336`) | error-50 bg / error-700 text | 실패 |

---

## KPI 카드 디자인

```css
.kpi-card {
  background: white;
  border: 1px solid var(--color-neutral-200);
  border-radius: 8px;
  padding: var(--space-6);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.kpi-card-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  /* 색상은 카드 유형별 */
}

.kpi-card-value {
  font-size: 2rem;         /* 32px */
  font-weight: 700;
  line-height: 1.3;
  color: var(--color-neutral-800);
}

.kpi-card-label {
  font-size: 0.875rem;     /* 14px */
  font-weight: 400;
  color: var(--color-neutral-500);
  margin-top: var(--space-1);
}

.kpi-card-sub {
  font-size: 0.75rem;      /* 12px */
  color: var(--color-neutral-400);
  margin-top: var(--space-1);
}
```

---

## 디자인 토큰

```css
/* design-system.md 토큰 기준 */

/* 파이프라인 컬럼 */
--pipeline-interested: var(--color-info-500);
--pipeline-participating: var(--color-primary-500);
--pipeline-submitted: var(--color-warning-500);
--pipeline-won: var(--color-success-500);
--pipeline-lost: var(--color-error-500);

/* KPI 아이콘 배경 */
--kpi-participation-bg: var(--color-info-50);
--kpi-participation-icon: var(--color-info-500);
--kpi-submission-bg: var(--color-primary-50);
--kpi-submission-icon: var(--color-primary-500);
--kpi-won-bg: var(--color-success-50);
--kpi-won-icon: var(--color-success-500);
--kpi-winrate-bg: var(--color-secondary-50);
--kpi-winrate-icon: var(--color-secondary-500);

/* 차트 */
--chart-line: var(--color-secondary-500);
--chart-area: var(--color-secondary-50);
--chart-grid: var(--color-neutral-200);

/* 기존 토큰 재사용 */
--color-bg-page: #FAFAFA;
--color-bg-card: #FFFFFF;
--color-border: #E0E0E0;
--color-text-primary: #212121;
--color-text-secondary: #757575;
--color-text-caption: #9E9E9E;

--font-sans: 'Noto Sans KR', 'Pretendard', -apple-system, sans-serif;

--radius-card: 8px;
--radius-badge: 9999px;

--shadow-card: 0 1px 3px rgba(0, 0, 0, 0.04);
--shadow-card-hover: 0 4px 12px rgba(0, 0, 0, 0.08);
--transition-fast: 150ms ease;
```

---

## 반응형 설계

### 모바일 (375px)

- 대시보드: KPI 2x2 그리드, 콘텐츠 1열 스택 (파이프라인 요약 -> 마감 임박 -> 차트)
- 파이프라인: 5개 컬럼 대신 탭 형식 (상태별 탭 전환), 카드 1열 full-width
- 낙찰 이력: 카드형 1열, 요약 KPI 2x2 그리드

### 태블릿 (768px)

- 대시보드: KPI 4열, 콘텐츠 2열 (파이프라인+마감 | 차트)
- 파이프라인: 5열 가로 스크롤 (각 컬럼 min-width: 240px)
- 낙찰 이력: 테이블형 (일부 컬럼 축약)

### 데스크톱 (1024px+)

- 대시보드: KPI 4열, 콘텐츠 2열 (max-width 1280px)
- 파이프라인: 5열 균등 분배 (각 컬럼 flex: 1)
- 낙찰 이력: 테이블형 full-width

---

## 에러 처리 명세

| 에러 코드 | 표시 위치 | 표시 방법 |
|----------|---------|---------|
| AUTH_002 (인증 없음) | 전체 페이지 | 로그인 페이지로 리다이렉트 |
| VALIDATION_001 (파라미터 오류) | 해당 위젯 | 인라인 에러 텍스트 |
| 네트워크/서버 오류 | 해당 위젯 | "데이터를 불러올 수 없습니다" + 재시도 버튼 |
| DASHBOARD_001 (추적 없음) | 공고 상세 tracking 영역 | 상태 없음 표시 + "관심 표시" CTA |
| BID_001 (공고 없음) | 파이프라인 카드 | 카드 비활성화 처리 |

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-03-08 | F-06 UI 설계서 초안 작성 |
