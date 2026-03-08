# F-01 공고 컴포넌트 문서

## 컴포넌트 목록

| 컴포넌트 | 경로 | 유형 | 설명 |
|----------|------|------|------|
| `MatchScoreBadge` | `components/bids/MatchScoreBadge.tsx` | Server Component | 매칭 점수 배지 |
| `DeadlineBadge` | `components/bids/DeadlineBadge.tsx` | Server Component | 마감일 임박 배지 |
| `BidStatusBadge` | `components/bids/BidStatusBadge.tsx` | Server Component | 공고 상태 배지 |
| `RecommendationBadge` | `components/bids/RecommendationBadge.tsx` | Server Component | 추천 등급 배지 |
| `BidCard` | `components/bids/BidCard.tsx` | Server Component | 공고 카드 (모바일) |
| `BidFilterBar` | `components/bids/BidFilterBar.tsx` | Client Component | 필터/검색 바 |
| `BidAttachmentList` | `components/bids/BidAttachmentList.tsx` | Server Component | 첨부파일 목록 |
| `BidMatchBadge` | `components/bids/BidMatchBadge.tsx` | Server Component | 점수+추천 통합 배지 |

---

## MatchScoreBadge

매칭 점수를 색상으로 시각화하는 배지 컴포넌트.

### Props

| Prop | Type | Default | 설명 |
|------|------|---------|------|
| `score` | `number` | 필수 | 매칭 점수 (0~100) |
| `size` | `'sm' \| 'md' \| 'lg'` | `'sm'` | 배지 크기 |

### 색상 기준 (F-01 기준: 70/50 분기)

| 점수 범위 | 배경 | 텍스트 |
|----------|------|--------|
| 70점 이상 | `#E8F5E9` | `#2E7D32` (초록) |
| 50~69점 | `#FFF8E1` | `#F57C00` (노랑) |
| 50점 미만 | `#F5F5F5` | `#616161` (회색) |

### 사용 예시

```tsx
<MatchScoreBadge score={78.5} />
<MatchScoreBadge score={65.0} size="md" />
<MatchScoreBadge score={42.0} size="lg" />
```

---

## DeadlineBadge

마감일 임박 여부를 표시하는 배지 컴포넌트.

### Props

| Prop | Type | 설명 |
|------|------|------|
| `deadline` | `string` | ISO 날짜 문자열 (공고 마감일시) |

### 표시 기준

| D-day | 배경 | 텍스트 | 표시 여부 |
|-------|------|--------|----------|
| D-3 이하 | `#FFEBEE` | `#C62828` (빨강) | 표시 |
| D-4~D-7 | `#FFF8E1` | `#F57C00` (노랑) | 표시 |
| D-8 이상 | - | - | 미표시 (null 반환) |

---

## BidStatusBadge

공고 상태를 점+텍스트 형태의 배지로 표시하는 컴포넌트.

### Props

| Prop | Type | 설명 |
|------|------|------|
| `status` | `BidStatus` | `'open' \| 'closed' \| 'awarded' \| 'cancelled'` |

### 상태별 색상

| status | 라벨 | 색상 |
|--------|------|------|
| `open` | 모집중 | 파랑 (`#E3F2FD` / `#1565C0`) |
| `closed` | 마감 | 중성 (회색) |
| `awarded` | 낙찰 | 초록 |
| `cancelled` | 취소 | 빨강 |

---

## BidFilterBar

공고 목록 검색/필터 바 컴포넌트 (Client Component).

### Props

| Prop | Type | 설명 |
|------|------|------|
| `keyword` | `string` | 현재 검색어 |
| `status` | `string` | 상태 필터 값 |
| `category` | `string` | 분류 필터 값 |
| `sortBy` | `string` | 정렬 기준 |
| `sortOrder` | `string` | 정렬 방향 |
| `onKeywordChange` | `(v: string) => void` | 검색어 변경 콜백 (300ms 디바운스) |
| `onStatusChange` | `(v: string) => void` | 상태 필터 변경 콜백 |
| `onCategoryChange` | `(v: string) => void` | 분류 필터 변경 콜백 |
| `onSortChange` | `(sortBy: string, sortOrder: string) => void` | 정렬 변경 콜백 |
| `onReset` | `() => void` | 필터 초기화 콜백 |
| `totalCount?` | `number` | 검색 결과 건수 (선택) |

### 인터랙션

- 검색창: 입력 후 300ms 디바운스 후 `onKeywordChange` 호출
- 필터 변경: 즉시 콜백 호출
- 초기화 버튼: 활성 필터가 있을 때만 표시

---

## BidAttachmentList

공고 첨부파일 목록을 렌더링하는 컴포넌트.

### Props

| Prop | Type | 설명 |
|------|------|------|
| `attachments` | `BidAttachment[]` | 첨부파일 배열 |

### 파일 타입별 아이콘

| 파일 타입 | 아이콘 배경 | 텍스트 색 |
|----------|-----------|---------|
| PDF | `#FFEBEE` | `#C62828` |
| HWP | `neutral-100` | `neutral-500` |
| 기타 | `blue-50` | `blue-600` |

### 텍스트 추출 상태

- `hasExtractedText: true` → 초록 체크 + "텍스트 추출 완료"
- `hasExtractedText: false` → 회색 경고 + "텍스트 추출 불가 ({fileType})"

---

## 페이지

### 공고 목록 (`/bids`)

- **파일**: `app/(main)/(dashboard)/bids/page.tsx`
- **유형**: Client Component (Zustand 스토어 연동)
- **스토어**: `useBidStore`
- **반응형**: 데스크톱 테이블 / 모바일 카드 자동 전환 (Tailwind md: breakpoint)
- **상태**: 로딩(스켈레톤 8행) / 빈 상태 / 에러 배너 / 정상 목록

### 공고 상세 (`/bids/[id]`)

- **파일**: `app/(main)/(dashboard)/bids/[id]/page.tsx`
- **유형**: Client Component
- **API 호출**: `getBid(id)` + `getBidMatches(id)` 병렬 실행
- **레이아웃**: 2컬럼 (좌 2/3: 기본정보+내용+첨부파일 / 우 1/3: 매칭 결과)
- **매칭 섹션 상태**: 회사 미등록 안내 / 분석 중(스피너) / 정상 점수 표시

### 매칭 공고 (`/bids/matched`)

- **파일**: `app/(main)/(dashboard)/bids/matched/page.tsx`
- **유형**: Client Component (Zustand 스토어 연동)
- **스토어**: `useMatchedBidStore`
- **상태**: 회사 미등록 전체 안내 / 로딩 스켈레톤 / 빈 상태 / 정상 카드 그리드

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-03-08 | F-01 공고 컴포넌트 초안 작성 |
