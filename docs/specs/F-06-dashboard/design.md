# F-06 입찰 현황 대시보드 -- 변경 설계서

## 1. 참조
- 인수조건: docs/project/features.md #F-06
- ERD: docs/system/erd.md (user_bid_tracking, bids, user_bid_matches)
- API 컨벤션: docs/system/api-conventions.md
- 디자인 시스템: docs/system/design-system.md
- 네비게이션: docs/system/navigation.md
- F-01 설계: docs/specs/F-01-bid-collection/design.md

---

## 2. 변경 범위

- **변경 유형**: 신규 추가
- **영향 받는 모듈**:
  - Backend: 신규 dashboard API 라우터, user_bid_tracking 모델, DashboardService
  - Frontend: 대시보드 페이지, 파이프라인 페이지, 낙찰 이력 페이지
  - 기존 bids 라우터 (tracking 엔드포인트 추가)

---

## 3. 영향 분석

### 기존 API 변경

| API | 현재 | 변경 후 | 하위 호환성 |
|-----|------|---------|-------------|
| GET /api/v1/bids | 공고 목록 조회 | 변경 없음 | 유지 |
| GET /api/v1/bids/{id} | 공고 상세 조회 | tracking 상태 필드 추가 (선택적) | 유지 (추가 필드) |

### 기존 DB 변경

| 테이블 | 변경 내용 | 마이그레이션 전략 |
|--------|----------|------------------|
| (없음) | user_bid_tracking 신규 생성 | 신규 마이그레이션 파일 |

### 사이드 이펙트
- bids 테이블의 status 값(awarded)과 user_bid_tracking의 is_winner가 연관되나, 각각 독립적으로 관리
- user_bid_matches 테이블의 데이터를 대시보드 통계에 활용 (읽기 전용)
- F-01에서 생성된 인메모리 샘플 데이터 패턴 유지 (MVP)

---

## 4. 아키텍처 결정

### 결정 1: 대시보드 API 구조
- **선택지**: A) 단일 대시보드 API (모든 위젯 데이터 한 번에) / B) 위젯별 개별 API
- **결정**: B) 위젯별 개별 API
- **근거**:
  - 각 위젯이 독립적으로 로딩/갱신 가능
  - 프론트엔드에서 병렬 호출로 초기 로딩 최적화
  - 특정 위젯만 폴링할 수 있어 네트워크 효율적
  - 추후 위젯 추가/제거 시 API 변경 범위 최소화

### 결정 2: 통계 집계 방식
- **선택지**: A) 실시간 집계 쿼리 / B) Materialized View / C) Redis 캐싱
- **결정**: A) 실시간 집계 쿼리 + Redis 캐싱 (30초 TTL)
- **근거**:
  - MVP 단계에서 데이터 규모가 작아 실시간 쿼리 부담 낮음
  - Redis 캐싱(30초)으로 반복 요청 최적화 (폴링 주기와 동일)
  - 추후 데이터 증가 시 Materialized View로 전환 가능

### 결정 3: 폴링 방식
- **선택지**: A) 전체 대시보드 폴링 / B) 위젯별 선택적 폴링 / C) WebSocket
- **결정**: B) 위젯별 선택적 폴링 (30초 간격)
- **근거**:
  - 인수조건에서 실시간 업데이트는 폴링 방식 명시
  - 파이프라인/KPI 위젯만 폴링, 통계 차트는 수동 새로고침
  - WebSocket은 과도한 인프라 복잡성 (MVP 부적합)

### 결정 4: 차트 라이브러리
- **선택지**: A) Recharts / B) Chart.js (react-chartjs-2) / C) D3.js
- **결정**: A) Recharts
- **근거**:
  - React 네이티브 컴포넌트로 RSC/SSR 호환성 우수
  - 선언적 API로 코드 간결
  - Tailwind CSS와 통합 용이
  - 번들 크기 최적화 (트리 쉐이킹 지원)

### 결정 5: 칸반 보드 구현
- **선택지**: A) dnd-kit 라이브러리 / B) react-beautiful-dnd / C) 커스텀 구현 (읽기 전용)
- **결정**: C) 커스텀 구현 (읽기 전용 칸반 + 상태 변경 드롭다운)
- **근거**:
  - 인수조건에서 드래그 앤 드롭이 아닌 "단계별 카운트 조회 + 상태 변경" 요구
  - 상태 변경은 카드 내 드롭다운으로 충분
  - 외부 라이브러리 의존성 제거로 번들 최소화

---

## 5. API 설계

### 5.1 GET /api/v1/dashboard/summary
대시보드 KPI 요약

- **목적**: 이번 달 주요 지표 조회
- **인증**: 필요 (Bearer Token)
- **Query Parameters**:
  | Parameter | Type | Default | 설명 |
  |-----------|------|---------|------|
  | period | string | current_month | 기간: current_month, last_month, last_3_months, last_6_months, last_year |
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "period": "2026-03",
    "participationCount": 12,
    "submissionCount": 8,
    "wonCount": 3,
    "lostCount": 4,
    "pendingCount": 1,
    "totalWonAmount": 1500000000,
    "winRate": 42.86,
    "averageWonAmount": 500000000,
    "roi": 350.0,
    "upcomingDeadlines": [
      {
        "bidId": "uuid",
        "title": "2026년 정보시스템 고도화 사업",
        "deadline": "2026-03-22T17:00:00Z",
        "daysLeft": 3,
        "trackingStatus": "participating"
      }
    ]
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | AUTH_002 | 401 | 인증 토큰 없음 |
  | VALIDATION_001 | 400 | 잘못된 period 값 |

### 5.2 GET /api/v1/dashboard/pipeline
파이프라인 단계별 현황

- **목적**: 칸반 형식의 입찰 파이프라인 데이터 조회
- **인증**: 필요 (Bearer Token)
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "stages": [
      {
        "status": "interested",
        "label": "관심",
        "count": 5,
        "items": [
          {
            "trackingId": "uuid",
            "bidId": "uuid",
            "title": "AI 기반 행정 서비스 구축",
            "organization": "과학기술부",
            "budget": 200000000,
            "deadline": "2026-03-25T17:00:00Z",
            "daysLeft": 6,
            "totalScore": 78.5,
            "updatedAt": "2026-03-08T10:00:00Z"
          }
        ]
      },
      {
        "status": "participating",
        "label": "참여",
        "count": 3,
        "items": [...]
      },
      {
        "status": "submitted",
        "label": "제출",
        "count": 2,
        "items": [...]
      },
      {
        "status": "won",
        "label": "낙찰",
        "count": 1,
        "items": [...]
      },
      {
        "status": "lost",
        "label": "실패",
        "count": 1,
        "items": [...]
      }
    ]
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | AUTH_002 | 401 | 인증 토큰 없음 |

### 5.3 GET /api/v1/dashboard/statistics
성과 통계 (월별 트렌드)

- **목적**: 기간별 낙찰률, 참여 트렌드, ROI 분석 데이터
- **인증**: 필요 (Bearer Token)
- **Query Parameters**:
  | Parameter | Type | Default | 설명 |
  |-----------|------|---------|------|
  | months | int | 6 | 최근 N개월 데이터 (최대 12) |
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "monthly": [
      {
        "month": "2025-10",
        "participationCount": 8,
        "submissionCount": 5,
        "wonCount": 2,
        "lostCount": 3,
        "winRate": 40.0,
        "totalWonAmount": 800000000,
        "averageBidRate": 0.8745
      },
      {
        "month": "2025-11",
        "participationCount": 10,
        "submissionCount": 7,
        "wonCount": 3,
        "lostCount": 3,
        "winRate": 50.0,
        "totalWonAmount": 1200000000,
        "averageBidRate": 0.8812
      }
    ],
    "cumulative": {
      "totalParticipation": 52,
      "totalSubmission": 35,
      "totalWon": 14,
      "totalLost": 18,
      "overallWinRate": 43.75,
      "totalWonAmount": 7500000000,
      "averageWonAmount": 535714285,
      "overallRoi": 320.5
    }
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | AUTH_002 | 401 | 인증 토큰 없음 |

### 5.4 POST /api/v1/bids/{bid_id}/tracking
입찰 추적 생성/상태 변경

- **목적**: 공고의 입찰 추적 상태 관리 (관심/참여/제출/낙찰/실패)
- **인증**: 필요 (Bearer Token)
- **Request Body**:
```json
{
  "status": "participating",
  "myBidPrice": 450000000,
  "notes": "투찰가 확정, 제출 예정"
}
```
- **비즈니스 규칙**:
  - status 허용 값: interested, participating, submitted, won, lost
  - 최초 요청 시 user_bid_tracking 레코드 생성, 이후 업데이트
  - status가 won인 경우 is_winner = true 자동 설정
  - status가 lost인 경우 is_winner = false 자동 설정
  - status가 submitted인 경우 submitted_at 자동 설정
  - status가 won/lost인 경우 result_at 자동 설정
- **Response** (200 OK / 201 Created):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "bidId": "uuid",
    "userId": "uuid",
    "status": "participating",
    "myBidPrice": 450000000,
    "isWinner": null,
    "submittedAt": null,
    "resultAt": null,
    "notes": "투찰가 확정, 제출 예정",
    "createdAt": "2026-03-08T10:00:00Z",
    "updatedAt": "2026-03-08T10:00:00Z"
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | AUTH_002 | 401 | 인증 토큰 없음 |
  | BID_001 | 404 | 공고를 찾을 수 없음 |
  | VALIDATION_001 | 400 | 잘못된 status 값 |

### 5.5 GET /api/v1/bids/{bid_id}/tracking
입찰 추적 상태 조회

- **목적**: 특정 공고에 대한 현재 사용자의 추적 상태 조회
- **인증**: 필요 (Bearer Token)
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "bidId": "uuid",
    "userId": "uuid",
    "status": "participating",
    "myBidPrice": 450000000,
    "isWinner": null,
    "submittedAt": null,
    "resultAt": null,
    "notes": "투찰가 확정, 제출 예정",
    "createdAt": "2026-03-08T10:00:00Z",
    "updatedAt": "2026-03-08T10:00:00Z"
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | AUTH_002 | 401 | 인증 토큰 없음 |
  | BID_001 | 404 | 공고를 찾을 수 없음 |
  | DASHBOARD_001 | 404 | 추적 정보가 없음 |

### 5.6 GET /api/v1/bids/wins
낙찰 이력 조회

- **목적**: 사용자의 낙찰 이력 목록
- **인증**: 필요 (Bearer Token)
- **Query Parameters**:
  | Parameter | Type | Default | 설명 |
  |-----------|------|---------|------|
  | page | int | 1 | 페이지 번호 |
  | pageSize | int | 20 | 페이지당 항목 수 (최대 100) |
  | startDate | date | | 시작일 |
  | endDate | date | | 종료일 |
  | sortBy | string | resultAt | 정렬 기준: resultAt, myBidPrice |
  | sortOrder | string | desc | 정렬 방향 |
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "trackingId": "uuid",
        "bidId": "uuid",
        "title": "2026년 정보시스템 고도화 사업",
        "organization": "행정안전부",
        "budget": 500000000,
        "myBidPrice": 450000000,
        "bidRate": 0.90,
        "isWinner": true,
        "resultAt": "2026-03-25T10:00:00Z",
        "submittedAt": "2026-03-20T15:00:00Z"
      }
    ]
  },
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 14,
    "totalPages": 1
  }
}
```

---

## 6. DB 설계

ERD(docs/system/erd.md)에 정의된 user_bid_tracking 테이블을 사용합니다. 신규 테이블 생성은 없으나, 모델 코드를 새로 작성해야 합니다.

### 6.1 user_bid_tracking 테이블 (ERD 기정의, 모델 신규 구현)

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 추적 ID |
| user_id | UUID | FK -> users.id, NOT NULL | 사용자 ID |
| bid_id | UUID | FK -> bids.id, NOT NULL | 공고 ID |
| status | VARCHAR(20) | NOT NULL | 상태 (interested, participating, submitted, won, lost) |
| my_bid_price | DECIMAL(15,0) | | 나의 투찰 금액 |
| is_winner | BOOLEAN | | 낙찰 여부 |
| submitted_at | TIMESTAMP | | 제출 시간 |
| result_at | TIMESTAMP | | 결과 확인 시간 |
| notes | TEXT | | 메모 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 생성 시간 |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 수정 시간 |

**Unique Constraint**: (user_id, bid_id)

**Check Constraints**:
```sql
ALTER TABLE user_bid_tracking
    ADD CONSTRAINT chk_tracking_status
    CHECK (status IN ('interested', 'participating', 'submitted', 'won', 'lost'));
```

---

## 7. 서비스 설계

### 7.1 DashboardService -- 대시보드 서비스

**책임**: 대시보드 KPI, 파이프라인, 통계 데이터 조회 및 집계

```python
class DashboardService:
    """대시보드 서비스"""

    def __init__(self, db: AsyncSession, redis: Redis | None = None):
        self.db = db
        self.redis = redis

    async def get_summary(self, user_id: UUID, period: str) -> DashboardSummary:
        """
        KPI 요약 데이터 조회

        1. 기간 내 user_bid_tracking 집계
           - 상태별 카운트 (participating, submitted, won, lost)
           - 낙찰 금액 합계, 평균
           - 낙찰률 = won / (won + lost) * 100
        2. ROI 계산
           - ROI = (총 낙찰금액 - 총 투찰비용) / 총 투찰비용 * 100
           - MVP: 투찰비용 = my_bid_price 합계 (간소화)
        3. 마감 임박 공고 (D-7 이내, status=interested/participating)
        4. Redis 캐싱 (30초 TTL)
        """

    async def get_pipeline(self, user_id: UUID) -> PipelineData:
        """
        파이프라인 단계별 데이터 조회

        1. user_bid_tracking에서 사용자의 모든 추적 레코드 조회
        2. status별 그룹화 (interested, participating, submitted, won, lost)
        3. 각 항목에 bids 테이블의 공고 정보 조인
        4. user_bid_matches의 totalScore 조인 (있는 경우)
        5. 각 단계 내 deadline ASC 정렬
        """

    async def get_statistics(self, user_id: UUID, months: int) -> StatisticsData:
        """
        월별 성과 통계 조회

        1. 최근 N개월간 user_bid_tracking 데이터 집계
        2. 월별: 참여수, 제출수, 낙찰수, 탈락수, 낙찰률, 총 낙찰금액
        3. 누적: 전체 기간 합산 지표
        4. bid_rate = my_bid_price / bids.budget (예산 대비 투찰 비율)
        """

    def _calculate_period_range(self, period: str) -> tuple[datetime, datetime]:
        """
        기간 문자열 -> 시작일/종료일 변환

        - current_month: 이번 달 1일 ~ 오늘
        - last_month: 지난 달 1일 ~ 지난 달 말일
        - last_3_months: 3개월 전 1일 ~ 오늘
        - last_6_months: 6개월 전 1일 ~ 오늘
        - last_year: 1년 전 1일 ~ 오늘
        """

    async def _get_cached_or_query(
        self, cache_key: str, ttl: int, query_func: Callable
    ) -> Any:
        """Redis 캐시 조회, 없으면 쿼리 실행 후 캐싱"""
```

### 7.2 BidTrackingService -- 입찰 추적 서비스

**책임**: 입찰 추적 상태 CRUD

```python
class BidTrackingService:
    """입찰 추적 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert_tracking(
        self, user_id: UUID, bid_id: UUID, data: TrackingUpsertInput
    ) -> UserBidTracking:
        """
        추적 생성 또는 업데이트 (Upsert)

        1. user_bid_tracking에서 (user_id, bid_id) 조회
        2. 있으면 업데이트, 없으면 생성
        3. status에 따른 자동 필드 설정:
           - submitted -> submitted_at = NOW()
           - won -> is_winner = true, result_at = NOW()
           - lost -> is_winner = false, result_at = NOW()
        4. 저장 및 반환
        """

    async def get_tracking(self, user_id: UUID, bid_id: UUID) -> UserBidTracking | None:
        """추적 레코드 조회"""

    async def get_user_trackings(
        self, user_id: UUID, status: str | None = None
    ) -> list[UserBidTracking]:
        """사용자의 전체 추적 목록 조회 (상태 필터 선택)"""

    async def get_win_history(
        self, user_id: UUID, page: int, page_size: int, filters: dict
    ) -> tuple[list[dict], int]:
        """낙찰 이력 조회 (is_winner=true, 페이지네이션)"""
```

---

## 8. 시퀀스 흐름

### 8.1 대시보드 초기 로딩

```
사용자 -> Frontend -> 병렬 API 호출
    |
    | 1. GET /api/v1/dashboard/summary (KPI)
    | 2. GET /api/v1/dashboard/pipeline (파이프라인)
    | 3. GET /api/v1/dashboard/statistics?months=6 (통계)
    |
    v
Backend (각 API)
    | 4. Redis 캐시 확인 (30초 TTL)
    |    |- 캐시 히트: 즉시 반환
    |    |- 캐시 미스: DB 쿼리 실행
    | 5. user_bid_tracking + bids JOIN 집계
    | 6. 응답 반환 + Redis 캐싱
    |
    v
Frontend
    | 7. KPI 카드 렌더링
    | 8. 칸반 보드 렌더링
    | 9. 차트 렌더링
    | 10. 30초 폴링 시작 (summary + pipeline만)
```

### 8.2 입찰 상태 변경

```
사용자 -> 파이프라인 카드 -> 상태 드롭다운 선택
    |
    | 1. POST /api/v1/bids/{bid_id}/tracking { status: "submitted" }
    |
    v
BidTrackingService
    | 2. user_bid_tracking 조회 (user_id, bid_id)
    | 3. 레코드 업데이트 (status, submitted_at 자동 설정)
    | 4. DB 커밋
    | 5. Redis 캐시 무효화 (dashboard:summary:*, dashboard:pipeline:*)
    |
    v
Frontend
    | 6. 성공 toast 표시
    | 7. 파이프라인 UI 즉시 갱신 (낙관적 업데이트)
```

---

## 9. 영향 범위

### 9.1 수정 필요 파일

| 파일 | 변경 내용 |
|------|----------|
| backend/src/models/__init__.py | UserBidTracking 모델 import 추가 |
| backend/src/api/v1/router.py | dashboard 라우터 include 추가 |
| backend/src/api/v1/bids.py | tracking 관련 엔드포인트 추가 (/{bid_id}/tracking, /wins) |

### 9.2 신규 생성 파일

| 파일 | 설명 |
|------|------|
| **Backend** |
| backend/src/models/user_bid_tracking.py | UserBidTracking SQLAlchemy 모델 |
| backend/src/schemas/dashboard.py | 대시보드 관련 Pydantic 스키마 |
| backend/src/schemas/tracking.py | 추적 관련 Pydantic 스키마 |
| backend/src/services/dashboard_service.py | 대시보드 집계 서비스 |
| backend/src/services/bid_tracking_service.py | 입찰 추적 CRUD 서비스 |
| backend/src/api/v1/dashboard.py | 대시보드 API 엔드포인트 |
| **Frontend** |
| frontend/src/app/(main)/(dashboard)/dashboard/page.tsx | 대시보드 메인 페이지 |
| frontend/src/app/(main)/(dashboard)/pipeline/page.tsx | 파이프라인 페이지 |
| frontend/src/app/(main)/(dashboard)/bids/wins/page.tsx | 낙찰 이력 페이지 |
| frontend/src/components/dashboard/KpiCard.tsx | KPI 카드 컴포넌트 |
| frontend/src/components/dashboard/PipelineBoard.tsx | 칸반 보드 컴포넌트 |
| frontend/src/components/dashboard/PipelineColumn.tsx | 칸반 컬럼 컴포넌트 |
| frontend/src/components/dashboard/PipelineCard.tsx | 칸반 카드 컴포넌트 |
| frontend/src/components/dashboard/StatisticsChart.tsx | 통계 차트 컴포넌트 |
| frontend/src/components/dashboard/WinRateTrend.tsx | 낙찰률 트렌드 차트 |
| frontend/src/components/dashboard/DeadlineWidget.tsx | 마감 임박 위젯 |
| frontend/src/stores/dashboardStore.ts | 대시보드 Zustand 스토어 |
| frontend/src/lib/api/dashboard.ts | 대시보드 API 클라이언트 |

---

## 10. 성능 설계

### 10.1 인덱스 계획

```sql
-- 입찰 추적 조회 (사용자별)
CREATE INDEX idx_user_bid_tracking_user ON user_bid_tracking(user_id);
CREATE INDEX idx_user_bid_tracking_user_status ON user_bid_tracking(user_id, status);

-- 유니크 제약
CREATE UNIQUE INDEX idx_user_bid_tracking_unique ON user_bid_tracking(user_id, bid_id);

-- 낙찰 이력 조회
CREATE INDEX idx_user_bid_tracking_winner ON user_bid_tracking(user_id, is_winner)
    WHERE is_winner = TRUE;

-- 기간별 통계 쿼리
CREATE INDEX idx_user_bid_tracking_result_at ON user_bid_tracking(user_id, result_at DESC);
CREATE INDEX idx_user_bid_tracking_created ON user_bid_tracking(user_id, created_at DESC);
```

### 10.2 캐싱 전략

```
# Redis 캐싱 키
dashboard:summary:{user_id}:{period} -> {summary_data} (TTL: 30s)
dashboard:pipeline:{user_id} -> {pipeline_data} (TTL: 30s)
dashboard:statistics:{user_id}:{months} -> {stats_data} (TTL: 5min)

# 캐시 무효화 트리거
- POST /bids/{id}/tracking (상태 변경 시)
  -> dashboard:summary:{user_id}:* 삭제
  -> dashboard:pipeline:{user_id} 삭제
```

### 10.3 쿼리 최적화

통계 집계 쿼리 예시:
```sql
-- 월별 통계 집계
SELECT
    DATE_TRUNC('month', result_at) AS month,
    COUNT(*) FILTER (WHERE status IN ('participating', 'submitted', 'won', 'lost')) AS participation_count,
    COUNT(*) FILTER (WHERE status IN ('submitted', 'won', 'lost')) AS submission_count,
    COUNT(*) FILTER (WHERE is_winner = TRUE) AS won_count,
    COUNT(*) FILTER (WHERE is_winner = FALSE AND status = 'lost') AS lost_count,
    COALESCE(SUM(my_bid_price) FILTER (WHERE is_winner = TRUE), 0) AS total_won_amount
FROM user_bid_tracking
WHERE user_id = :user_id
  AND result_at >= :start_date
GROUP BY DATE_TRUNC('month', result_at)
ORDER BY month DESC;
```

---

## 11. 에러 코드

### 신규 에러 코드 (F-06 추가)

| 코드 | HTTP Status | 메시지 |
|------|-------------|--------|
| DASHBOARD_001 | 404 | 추적 정보를 찾을 수 없습니다. |
| DASHBOARD_002 | 400 | 유효하지 않은 기간 값입니다. |
| DASHBOARD_003 | 400 | 유효하지 않은 추적 상태 값입니다. |

### 기존 에러 코드 (재사용)

| 코드 | HTTP Status | 메시지 |
|------|-------------|--------|
| AUTH_002 | 401 | 인증 토큰이 필요합니다. |
| BID_001 | 404 | 공고를 찾을 수 없습니다. |
| VALIDATION_001 | 400 | 입력값이 유효하지 않습니다. |

---

## 12. 프론트엔드 의존성 추가

### package.json 추가

```json
{
  "recharts": "^2.12.0"
}
```

---

## 변경 이력

| 날짜 | 변경 내용 | 이유 |
|------|----------|------|
| 2026-03-08 | 초기 변경 설계 | F-06 기능 설계 시작 |
