# F-06 입찰 현황 대시보드 -- 구현 계획서

## 참조
- 설계서: docs/specs/F-06-dashboard/design.md
- UI 설계서: docs/specs/F-06-dashboard/ui-spec.md
- 인수조건: docs/project/features.md #F-06
- 테스트 명세: docs/specs/F-06-dashboard/test-spec.md

---

## 태스크 목록

### Phase 1: 백엔드 구현

#### T1: 모델
- [ ] [backend] `backend/src/models/user_bid_tracking.py` — UserBidTracking 모델 (user_bid_tracking 테이블)
- [ ] [backend] `backend/src/models/__init__.py` — UserBidTracking import 추가

| 태스크 | 설명 | 파일 |
|--------|------|------|
| T1-1 | UserBidTracking SQLAlchemy 모델 | backend/src/models/user_bid_tracking.py |
| T1-2 | 모델 __init__ 등록 | backend/src/models/__init__.py |

#### T2: Pydantic 스키마
- [ ] [backend] `backend/src/schemas/dashboard.py` — 대시보드 관련 스키마 (KPI, 파이프라인, 통계)
- [ ] [backend] `backend/src/schemas/tracking.py` — 입찰 추적 관련 스키마

| 태스크 | 설명 | 파일 |
|--------|------|------|
| T2-1 | 대시보드 Pydantic 스키마 | backend/src/schemas/dashboard.py |
| T2-2 | 추적 Pydantic 스키마 | backend/src/schemas/tracking.py |

#### T3: 서비스 계층
- [ ] [backend] `backend/src/services/bid_tracking_service.py` — BidTrackingService (CRUD)
- [ ] [backend] `backend/src/services/dashboard_service.py` — DashboardService (집계/통계)

| 태스크 | 설명 | 파일 |
|--------|------|------|
| T3-1 | BidTrackingService 구현 | backend/src/services/bid_tracking_service.py |
| T3-2 | DashboardService 구현 | backend/src/services/dashboard_service.py |

#### T4: API 라우터
- [ ] [backend] `backend/src/api/v1/dashboard.py` — 대시보드 API (summary, pipeline, statistics)
- [ ] [backend] `backend/src/api/v1/bids.py` — tracking 엔드포인트 추가 (POST/GET /{bid_id}/tracking, GET /wins)
- [ ] [backend] `backend/src/api/v1/router.py` — dashboard 라우터 include 추가

| 태스크 | 설명 | 파일 |
|--------|------|------|
| T4-1 | 대시보드 API 엔드포인트 | backend/src/api/v1/dashboard.py |
| T4-2 | bids.py에 tracking/wins 엔드포인트 추가 | backend/src/api/v1/bids.py |
| T4-3 | router.py에 dashboard 라우터 등록 | backend/src/api/v1/router.py |

---

### Phase 2: 프론트엔드 구현

#### T5: 타입 정의 + API 클라이언트
- [ ] [frontend] `frontend/src/types/dashboard.ts` — Dashboard 관련 TypeScript 타입
- [ ] [frontend] `frontend/src/lib/api/dashboard.ts` — 대시보드 API 클라이언트

| 태스크 | 설명 | 파일 |
|--------|------|------|
| T5-1 | 대시보드 TypeScript 타입 | frontend/src/types/dashboard.ts |
| T5-2 | 대시보드 API 클라이언트 | frontend/src/lib/api/dashboard.ts |

#### T6: 상태 관리
- [ ] [frontend] `frontend/src/lib/stores/dashboard-store.ts` — 대시보드 Zustand 스토어

| 태스크 | 설명 | 파일 |
|--------|------|------|
| T6-1 | 대시보드 Zustand 스토어 | frontend/src/lib/stores/dashboard-store.ts |

#### T7: UI 컴포넌트 + 페이지
- [ ] [frontend] `frontend/src/components/dashboard/KpiCard.tsx` — KPI 카드
- [ ] [frontend] `frontend/src/components/dashboard/PipelineBoard.tsx` — 칸반 보드
- [ ] [frontend] `frontend/src/components/dashboard/PipelineColumn.tsx` — 칸반 컬럼
- [ ] [frontend] `frontend/src/components/dashboard/PipelineCard.tsx` — 칸반 카드
- [ ] [frontend] `frontend/src/components/dashboard/StatisticsChart.tsx` — 통계 차트
- [ ] [frontend] `frontend/src/components/dashboard/WinRateTrend.tsx` — 낙찰률 트렌드
- [ ] [frontend] `frontend/src/components/dashboard/DeadlineWidget.tsx` — 마감 임박 위젯
- [ ] [frontend] `frontend/src/app/(main)/(dashboard)/dashboard/page.tsx` — 대시보드 메인
- [ ] [frontend] `frontend/src/app/(main)/(dashboard)/pipeline/page.tsx` — 파이프라인
- [ ] [frontend] `frontend/src/app/(main)/(dashboard)/bids/wins/page.tsx` — 낙찰 이력

| 태스크 | 설명 | 파일 |
|--------|------|------|
| T7-1 | KpiCard 컴포넌트 | frontend/src/components/dashboard/KpiCard.tsx |
| T7-2 | PipelineBoard 컴포넌트 | frontend/src/components/dashboard/PipelineBoard.tsx |
| T7-3 | PipelineColumn 컴포넌트 | frontend/src/components/dashboard/PipelineColumn.tsx |
| T7-4 | PipelineCard 컴포넌트 | frontend/src/components/dashboard/PipelineCard.tsx |
| T7-5 | StatisticsChart 컴포넌트 | frontend/src/components/dashboard/StatisticsChart.tsx |
| T7-6 | WinRateTrend 컴포넌트 | frontend/src/components/dashboard/WinRateTrend.tsx |
| T7-7 | DeadlineWidget 컴포넌트 | frontend/src/components/dashboard/DeadlineWidget.tsx |
| T7-8 | 대시보드 메인 페이지 | frontend/src/app/(main)/(dashboard)/dashboard/page.tsx |
| T7-9 | 파이프라인 페이지 | frontend/src/app/(main)/(dashboard)/pipeline/page.tsx |
| T7-10 | 낙찰 이력 페이지 | frontend/src/app/(main)/(dashboard)/bids/wins/page.tsx |

#### T8: 프론트엔드 의존성
- [ ] [frontend] `recharts` 패키지 설치

---

### Phase 3: 검증
- [ ] [shared] 통합 테스트 실행
- [ ] [shared] quality-gate 검증

---

## 태스크 의존성

```
T1 (모델) → T2 (스키마) → T3 (서비스) → T4 (API) → Phase 3
T5 (타입/API) → T6 (스토어) → T7 (컴포넌트/페이지) → Phase 3
T8 (recharts 설치) → T7 (차트 컴포넌트)
Phase 1 + Phase 2 → Phase 3
```

## 병렬 실행 판단

- Agent Team 권장: Yes
- 근거: 백엔드(T1~T4)와 프론트엔드(T5~T8)는 API 스키마가 design.md에 확정되어 독립 개발 가능
