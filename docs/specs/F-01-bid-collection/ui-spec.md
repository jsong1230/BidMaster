# F-01 공고 자동 수집 및 매칭 — UI 설계서

## 화면 목록

| 화면명 | 경로 | 설명 |
|--------|------|------|
| 공고 목록 | `/bids` | 수집된 전체 공고. 키워드 검색 + 다중 필터(업종/마감일/상태/예산) + 정렬. 매칭 점수 배지 표시 |
| 공고 상세 | `/bids/[bidId]` | 공고 기본 정보, 첨부파일 목록, 매칭 분석 결과(점수 + 추천 사유) |
| 매칭 공고 | `/bids/matched` | 내 회사와 매칭된 공고만 표시. totalScore 내림차순 정렬. 추천 등급 필터 |

---

## 디자인 방향

- **톤앤매너**: 절제된 전문 B2B 업무 도구. 정보 밀도 높은 리스트 + 분석 결과의 명료한 시각화
- **색상**: design-system.md 토큰 그대로 사용. primary-600(`#486581`) 지배색 + secondary-500(`#0F9D58`) 포인트 (매칭 성공, 추천). 매칭 점수 시각화는 스코어링 색상 테이블 준수
- **타이포그래피**: `Noto Sans KR` 단일 패밀리. 공고 제목 weight-600, 기관명/메타 weight-400, 점수 숫자 weight-700
- **레이아웃 패턴**: 글로벌 셸(사이드바 240px + 메인 영역) 위에 페이지 구성. 공고 목록은 필터 사이드바 없이 상단 필터 바 + 테이블/카드 형식. 공고 상세는 2컬럼(메인 2/3 + 사이드 1/3) 레이아웃
- **반응형**: 모바일(375px) 카드형 1열 / 데스크톱(1024px+) 테이블형 또는 카드 2열

---

## 컴포넌트 계층

### 공고 목록 (`/bids`)

- `BidsPage`
  - `PageHeader` (페이지 제목 + 공고 건수 표시)
  - `BidsFilterBar` (상단 필터 + 검색 영역)
    - `SearchInput` (공고명/기관명 검색)
    - `StatusFilter` (드롭다운: 전체/모집중/마감/완료)
    - `CategoryFilter` (드롭다운: 분류)
    - `BudgetFilter` (드롭다운: 예산 범위)
    - `SortControl` (드롭다운: 마감일순/공고일순/예산순)
    - `FilterResetButton`
  - `BidListContent`
    - `BidSkeletonList` (로딩 상태)
    - `BidEmptyState` (빈 상태)
    - `BidTable` (데스크톱 테이블뷰)
      - `BidTableRow`
        - `BidStatusBadge` (open/closed/awarded/cancelled)
        - `DeadlineBadge` (D-3 이하: 빨간 배지)
        - `MatchScoreBadge` (70+: 초록, 50~70: 노랑, 50 미만: 회색)
    - `BidCardList` (모바일 카드뷰)
      - `BidCard`
  - `Pagination`

### 공고 상세 (`/bids/[bidId]`)

- `BidDetailPage`
  - `Breadcrumb` (대시보드 > 공고 > 공고 목록 > [공고명])
  - `BidDetailHeader`
    - `BidStatusBadge`
    - `DeadlineBadge`
    - `ActionButtons` (나라장터 원문 보기 / 제안서 생성)
  - `BidDetailLayout` (2컬럼)
    - **[좌 메인]** `BidInfoSection`
      - `BidBasicInfoCard` (기본 정보: 기관명, 분류, 예산, 일정)
      - `BidDescriptionCard` (공고 내용)
      - `BidAttachmentCard` (첨부파일 목록)
        - `AttachmentItem`
          - `FileTypeIcon` (PDF/HWP/DOC)
          - `ParseStatusBadge` (텍스트 추출 완료/미완료)
    - **[우 사이드]** `BidMatchSection`
      - `MatchScoreCard` (매칭 점수 요약)
        - `ScoreGauge` (원형 또는 반원형 게이지)
        - `RecommendationBadge` (추천/보통/비추천)
        - `ScoreBreakdown` (적합도/경쟁/역량/시장 세부 점수)
      - `MatchReasonCard` (추천 사유 텍스트)
      - `NoCompanyProfileCard` (회사 프로필 미등록 시 안내)

### 매칭 공고 (`/bids/matched`)

- `MatchedBidsPage`
  - `PageHeader` (매칭 공고 제목 + 매칭 건수)
  - `CompanyProfileMissingBanner` (회사 프로필 미등록 시 전체 영역 안내)
  - `MatchedFilterBar`
    - `RecommendationFilter` (전체/추천/보통/비추천 탭)
    - `MinScoreFilter` (최소 점수 입력)
    - `SortControl` (점수순/마감일순)
  - `MatchedBidContent`
    - `MatchedBidSkeletonList` (로딩 상태)
    - `MatchedBidEmptyState` (빈 상태)
    - `MatchedBidCardList`
      - `MatchedBidCard`
        - `MatchScoreBadge` (큰 점수 표시)
        - `RecommendationBadge`
        - `BidStatusBadge`
        - `DeadlineBadge`
        - `MatchReasonSnippet` (추천 사유 한 줄 요약)
  - `Pagination`

---

## 상태 명세

### 공고 목록 페이지

| 컴포넌트 | 상태 | 타입 | 설명 |
|----------|------|------|------|
| `BidsPage` | `bids` | `BidItem[]` | 공고 목록 |
| `BidsPage` | `isLoading` | `boolean` | 목록 로딩 중 |
| `BidsPage` | `pagination` | `PaginationMeta` | 페이지 정보 |
| `BidsFilterBar` | `keyword` | `string` | 검색어 |
| `BidsFilterBar` | `status` | `string` | 상태 필터 값 |
| `BidsFilterBar` | `category` | `string` | 분류 필터 값 |
| `BidsFilterBar` | `minBudget` | `number \| null` | 최소 예산 |
| `BidsFilterBar` | `maxBudget` | `number \| null` | 최대 예산 |
| `BidsFilterBar` | `sortBy` | `string` | 정렬 기준 |
| `BidsFilterBar` | `sortOrder` | `'asc' \| 'desc'` | 정렬 방향 |

### 공고 상세 페이지

| 컴포넌트 | 상태 | 타입 | 설명 |
|----------|------|------|------|
| `BidDetailPage` | `bid` | `BidDetail \| null` | 공고 상세 데이터 |
| `BidDetailPage` | `matchResult` | `MatchResult \| null` | 매칭 분석 결과 |
| `BidDetailPage` | `isLoadingBid` | `boolean` | 공고 로딩 중 |
| `BidDetailPage` | `isLoadingMatch` | `boolean` | 매칭 결과 로딩 중 |

### 매칭 공고 페이지

| 컴포넌트 | 상태 | 타입 | 설명 |
|----------|------|------|------|
| `MatchedBidsPage` | `matches` | `MatchedBidItem[]` | 매칭 공고 목록 |
| `MatchedBidsPage` | `isLoading` | `boolean` | 로딩 중 |
| `MatchedBidsPage` | `hasCompanyProfile` | `boolean` | 회사 프로필 등록 여부 |
| `MatchedFilterBar` | `recommendation` | `'all' \| 'recommended' \| 'neutral' \| 'not_recommended'` | 추천 등급 필터 |
| `MatchedFilterBar` | `minScore` | `number` | 최소 점수 |
| `MatchedFilterBar` | `sortBy` | `string` | 정렬 기준 |

---

## 인터랙션 명세

### 공고 목록

- 검색창 입력 후 300ms 디바운스 → `GET /api/v1/bids?keyword=...` 호출 → 목록 갱신
- 필터 변경 → 즉시 쿼리 파라미터 업데이트 + API 재호출 (URL 상태 유지)
- 필터 초기화 버튼 → 모든 필터값 리셋 + URL 파라미터 제거
- 공고 행 클릭 → `/bids/[bidId]` 이동
- 페이지 변경 → 목록 상단으로 스크롤 이동

### 공고 상세

- 페이지 진입 → `GET /api/v1/bids/{id}` + `GET /api/v1/bids/{id}/matches` 병렬 호출
- 회사 프로필 미등록 시 → 매칭 섹션에 "회사 프로필 등록 필요" 안내 카드 표시
- 첨부파일 다운로드 → `file_url` 새 탭 열기
- 나라장터 원문 → 외부 링크 새 탭 열기
- 제안서 생성 → `/proposals/new?bidId={id}` 이동 (공고 마감 시 비활성화)

### 매칭 공고

- 페이지 진입 → `GET /api/v1/bids/matched` 호출
- 회사 프로필 미등록 시 (COMPANY_001) → 전체 영역에 안내 배너 표시 + 프로필 등록 CTA
- 추천 필터 탭 클릭 → 즉시 필터 적용 + API 재호출
- 매칭 공고 카드 클릭 → `/bids/[bidId]` 이동

---

## 매칭 점수 시각화 규칙

design-system.md의 스코어링 색상 테이블 기준 적용:

| totalScore | 배지 색상 | 배지 텍스트 색 | 의미 |
|-----------|---------|-------------|------|
| 70 이상 | `#E8F5E9` (bg) | `#2E7D32` (text) | 높은 매칭 |
| 50~69 | `#FFF8E1` (bg) | `#F57C00` (text) | 보통 매칭 |
| 50 미만 | `#F5F5F5` (bg) | `#616161` (text) | 낮은 매칭 |

요구사항에서 70/50 기준으로 색상 분기 (design-system의 80/60 기준 대신 F-01 인수조건 우선 적용)

### 마감일 임박 배지

- deadline 기준 D-day 계산
- D-3 이하 (3일 이내): `bg-error-50 text-error-700` + "D-{n}" 텍스트
- D-4 ~ D-7: `bg-warning-50 text-warning-700` + "D-{n}" 텍스트
- D-8 이상: 배지 미표시 또는 중성 색상

### recommendation 배지

| recommendation | 배지 | 색상 |
|--------------|------|------|
| recommended | 추천 | success |
| neutral | 보통 | warning |
| not_recommended | 비추천 | neutral |

---

## 레이아웃 상세

### 공고 목록 (데스크톱)

```
┌────────────────────────────────────────────────────────┐
│  헤더 (글로벌 셸)                                       │
├──────────┬─────────────────────────────────────────────┤
│          │  공고 목록                    (페이지 제목) │
│  사이드  │  총 150건                                    │
│  바      ├─────────────────────────────────────────────┤
│          │  [검색창         ] [상태▾] [분류▾] [예산▾]  │
│  (글로벌 │                                [정렬▾] [초기화]│
│   셸)    ├─────────────────────────────────────────────┤
│          │  공고번호  공고명  기관  분류  예산  마감일  │
│          │  ────────────────────────────────────────── │
│          │  20260308  2026년…  행정안전부  …  5억  [D-2]│
│          │  20260305  AI 기반…  과학기술부  …  2억  …   │
│          │  …                                          │
│          ├─────────────────────────────────────────────┤
│          │           [1] [2] [3] ... [8]               │
└──────────┴─────────────────────────────────────────────┘
```

### 공고 상세 (데스크톱)

```
┌────────────────────────────────────────────────────────────────┐
│  대시보드 > 공고 > 공고 목록 > 2026년 정보시스템 고도화 사업    │
├────────────────────────────────────────────────────────────────┤
│  2026년 정보시스템 고도화 사업                                  │
│  [모집중] [D-14]           [나라장터 원문] [제안서 생성]        │
├──────────────────────────────┬─────────────────────────────────┤
│  기본 정보                   │  매칭 분석 결과                  │
│  ──────────────              │  ────────────────               │
│  발주기관   행정안전부         │     78.5점                     │
│  분류       용역              │   [추천] 높은 매칭               │
│  예산       5억원             │                                 │
│  공고일     2026-03-08        │  적합도  ████████░░  78.5       │
│  마감일     2026-03-22        │  경쟁도  ─────────  0 (분석 예정)│
│  개찰일     2026-03-23        │  역량    ─────────  0 (분석 예정)│
│  입찰유형   일반경쟁          │  시장    ─────────  0 (분석 예정)│
│  계약방식   적격심사          │                                 │
│  평가기준   기술 80 / 가격 20 │  추천 사유                      │
│                              │  회사 업종(소프트웨어 개발업)이  │
│  공고 내용                   │  공고 분야와 높은 적합도...      │
│  ──────────────              │                                 │
│  [설명 텍스트]               │                                 │
│                              │                                 │
│  첨부파일 (3건)              │                                 │
│  ──────────────              │                                 │
│  PDF  제안요청서.pdf  [텍스트추출완료]  [다운로드]              │
│  HWP  과업지시서.hwp  [텍스트추출불가] [다운로드]              │
└──────────────────────────────┴─────────────────────────────────┘
```

### 매칭 공고 (데스크톱)

```
┌────────────────────────────────────────────────────────┐
│  매칭 공고                                              │
│  총 35건 | 내 회사와 매칭된 공고                        │
├────────────────────────────────────────────────────────┤
│  [전체] [추천] [보통] [비추천]      최소점수: [70] [정렬▾]│
├────────────────────────────────────────────────────────┤
│  ┌──────────────────────────┐  ┌──────────────────────┐│
│  │ 78.5점 [추천]  [D-14]    │  │ 65.0점 [보통]  [D-7] ││
│  │ [모집중]                 │  │ [모집중]              ││
│  │ 2026년 정보시스템 고도화  │  │ AI 기반 행정 서비스…  ││
│  │ 행정안전부 / 용역 / 5억  │  │ 과학기술부 / 용역 / 2억││
│  │ 마감 2026-03-22          │  │ 마감 2026-03-25       ││
│  │ 회사 업종이 공고 분야와… │  │ 유사 분야 실적 1건…   ││
│  └──────────────────────────┘  └──────────────────────┘│
│  …                                                      │
└────────────────────────────────────────────────────────┘
```

---

## 화면별 상태 시나리오

### 공고 목록

| 시나리오 | UI 표현 |
|----------|---------|
| 로딩 중 | 테이블 행 8개 스켈레톤 (`animate-pulse`, bg-neutral-200) |
| 검색 결과 없음 | 중앙 빈 상태: "검색 조건에 맞는 공고가 없습니다" + 필터 초기화 버튼 |
| 필터 적용 중 | 필터 컨트롤에 active 표시, 목록 상단에 "n개 필터 적용 중" 칩 |
| 공고 목록 정상 | 테이블형 (데스크톱) / 카드형 (모바일) |
| 매칭 점수 있음 | 공고 행/카드에 점수 배지 표시 |
| 매칭 점수 없음 (회사 미등록) | 점수 배지 자리 비어 있음 (배지 미노출) |

### 공고 상세

| 시나리오 | UI 표현 |
|----------|---------|
| 공고 로딩 중 | 헤더 + 기본정보 스켈레톤 |
| 매칭 로딩 중 | 매칭 섹션 스켈레톤 (스피너 + 텍스트: "분석 중...") |
| 매칭 정상 | 점수 + 세부 항목 + 추천 사유 |
| 회사 프로필 미등록 | 매칭 섹션에 "회사 프로필 등록 후 매칭 결과를 확인하세요" 안내 + 등록 링크 |
| 공고 마감 | "제안서 생성" 버튼 disabled + 마감 뱃지 |
| 첨부파일 없음 | "첨부파일이 없습니다" 텍스트 |
| 404 | "공고를 찾을 수 없습니다" 에러 상태 |

### 매칭 공고

| 시나리오 | UI 표현 |
|----------|---------|
| 로딩 중 | 카드 6개 스켈레톤 |
| 회사 미등록 | 전체 영역에 안내 배너 (아이콘 + 텍스트 + "회사 프로필 등록" 버튼) |
| 매칭 공고 없음 | 빈 상태: "아직 매칭된 공고가 없습니다. 공고 수집 후 자동 분석됩니다." |
| 필터 결과 없음 | "해당 조건의 매칭 공고가 없습니다" + 필터 초기화 |
| 정상 목록 | 카드 2열 그리드 (모바일 1열) |

---

## 반응형 설계

### 모바일 (375px)

- 공고 목록: 카드형 1열. 필터는 상단 드롭다운 + "필터" 버튼 탭시 필터 바 토글
- 공고 상세: 단일 컬럼. 매칭 섹션이 기본 정보 카드 아래에 위치
- 매칭 공고: 카드 1열 full-width

### 태블릿 (768px)

- 공고 목록: 카드형 2열 또는 테이블 (일부 컬럼 축약)
- 공고 상세: 2컬럼 (메인 60% + 사이드 40%)
- 매칭 공고: 카드 2열

### 데스크톱 (1024px+)

- 공고 목록: 테이블형 full-width
- 공고 상세: 2컬럼 (메인 2/3 + 사이드 1/3)
- 매칭 공고: 카드 2열 (max-width 1280px)

---

## 디자인 토큰

```css
/* design-system.md 토큰 기준 */

--color-primary: #486581;
--color-primary-light: #F0F4F8;
--color-accent: #0F9D58;

/* 매칭 점수 배지 (F-01 기준: 70/50 분기) */
--score-high-bg: #E8F5E9;      /* 70점 이상 배경 */
--score-high-text: #2E7D32;    /* 70점 이상 텍스트 */
--score-mid-bg: #FFF8E1;       /* 50~69 배경 */
--score-mid-text: #F57C00;     /* 50~69 텍스트 */
--score-low-bg: #F5F5F5;       /* 50 미만 배경 */
--score-low-text: #616161;     /* 50 미만 텍스트 */

/* 마감 임박 */
--deadline-urgent-bg: #FFEBEE;   /* D-3 이하 배경 */
--deadline-urgent-text: #C62828; /* D-3 이하 텍스트 */
--deadline-soon-bg: #FFF8E1;     /* D-4~D-7 배경 */
--deadline-soon-text: #F57C00;   /* D-4~D-7 텍스트 */

--color-bg-page: #FAFAFA;
--color-bg-card: #FFFFFF;
--color-border: #E0E0E0;
--color-text-primary: #212121;
--color-text-secondary: #757575;
--color-text-caption: #9E9E9E;

--font-sans: 'Noto Sans KR', 'Pretendard', -apple-system, sans-serif;

--radius-card: 8px;
--radius-input: 6px;
--radius-badge: 9999px;

--shadow-card: 0 1px 3px rgba(0, 0, 0, 0.04);
--shadow-card-hover: 0 4px 12px rgba(0, 0, 0, 0.08);
--transition-fast: 150ms ease;
```

---

## 에러 처리 명세

| 에러 코드 | 표시 위치 | 표시 방법 |
|----------|---------|---------|
| AUTH_002 (인증 없음) | 전체 페이지 | 로그인 페이지로 리다이렉트 |
| BID_001 (공고 없음) | 공고 상세 메인 영역 | 404 에러 카드 + "목록으로 돌아가기" |
| COMPANY_001 (회사 미등록) | 매칭 섹션 또는 매칭 공고 페이지 | 안내 카드 + 프로필 등록 CTA |
| VALIDATION_001 (필터 오류) | 필터 영역 | 인라인 에러 텍스트 |
| 네트워크/서버 오류 | 해당 섹션 | 에러 배너 + "다시 시도" 버튼 |

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-03-08 | F-01 UI 설계서 초안 작성 |
