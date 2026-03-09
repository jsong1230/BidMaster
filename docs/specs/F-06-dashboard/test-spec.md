# F-06 입찰 현황 대시보드 -- 테스트 명세

## 참조
- 설계서: docs/specs/F-06-dashboard/design.md
- 인수조건: docs/project/features.md #F-06

---

## 단위 테스트

### DashboardService

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| get_summary | 이번 달 데이터가 있는 경우 | user_id, period="current_month" | participationCount, wonCount 등 정확히 집계됨 |
| get_summary | 데이터가 없는 경우 | user_id (추적 없음), period="current_month" | 모든 카운트 0, winRate 0.0, totalWonAmount 0 |
| get_summary | 마감 임박 공고 포함 | user_id (D-3 공고 추적 중) | upcomingDeadlines에 해당 공고 포함, daysLeft 정확 |
| get_summary | ROI 계산 정확성 | won 2건 (각 500만), bid_price 합 800만 | roi = (1000-800)/800*100 = 25.0 |
| get_summary | last_3_months 기간 | user_id, period="last_3_months" | 3개월 전~오늘 데이터만 집계 |
| get_pipeline | 모든 상태에 데이터 있음 | user_id | 5개 stage 각각 count > 0, items 포함 |
| get_pipeline | 빈 파이프라인 | user_id (추적 없음) | 5개 stage 각각 count=0, items=[] |
| get_pipeline | 공고 정보 조인 | user_id | 각 item에 title, organization, budget, deadline 포함 |
| get_pipeline | 매칭 점수 조인 | user_id (매칭 결과 있음) | totalScore 값 포함 |
| get_pipeline | 단계 내 정렬 | user_id | 각 stage 내 deadline ASC 정렬 |
| get_statistics | 6개월 데이터 | user_id, months=6 | monthly 배열 6개 항목, 각 항목 정확한 집계 |
| get_statistics | 데이터 없는 월 포함 | user_id, months=6 (일부 월 데이터 없음) | 빈 월은 count 0으로 포함 |
| get_statistics | 누적 통계 정확성 | user_id | cumulative의 합계가 monthly 합과 일치 |
| get_statistics | 낙찰률 계산 | won=3, lost=7 | overallWinRate = 30.0 |
| _calculate_period_range | current_month | "current_month" | 이번 달 1일 00:00 ~ 오늘 |
| _calculate_period_range | last_year | "last_year" | 1년 전 1일 ~ 오늘 |
| _calculate_period_range | 잘못된 값 | "invalid" | ValueError 발생 |

### BidTrackingService

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| upsert_tracking | 신규 생성 (interested) | user_id, bid_id, status="interested" | 201, 새 레코드 생성 |
| upsert_tracking | 기존 업데이트 (participating) | user_id, bid_id (기존 interested), status="participating" | 200, status 변경됨 |
| upsert_tracking | submitted 상태 | status="submitted" | submitted_at 자동 설정 |
| upsert_tracking | won 상태 | status="won" | is_winner=true, result_at 자동 설정 |
| upsert_tracking | lost 상태 | status="lost" | is_winner=false, result_at 자동 설정 |
| upsert_tracking | notes 업데이트 | status="participating", notes="메모" | notes 필드 저장됨 |
| upsert_tracking | myBidPrice 설정 | status="submitted", myBidPrice=450000000 | my_bid_price 저장됨 |
| get_tracking | 존재하는 추적 | user_id, bid_id | 추적 레코드 반환 |
| get_tracking | 존재하지 않는 추적 | user_id, bid_id (없음) | None 반환 |
| get_user_trackings | 전체 조회 | user_id | 사용자의 모든 추적 레코드 |
| get_user_trackings | 상태 필터 | user_id, status="submitted" | submitted 상태만 반환 |
| get_win_history | 낙찰 이력 조회 | user_id, page=1 | is_winner=true인 레코드만 |
| get_win_history | 페이지네이션 | user_id, page=2, pageSize=5 | 올바른 offset 적용 |
| get_win_history | 날짜 범위 필터 | startDate, endDate | 범위 내 레코드만 |

---

## 통합 테스트

### Dashboard API

| API | 시나리오 | 입력 | 예상 결과 |
|-----|----------|------|-----------|
| GET /dashboard/summary | 인증된 사용자, 정상 조회 | Bearer Token, period=current_month | 200, KPI 데이터 반환 |
| GET /dashboard/summary | 인증 없음 | 토큰 없음 | 401, AUTH_002 |
| GET /dashboard/summary | 잘못된 period | period=invalid | 400, VALIDATION_001 |
| GET /dashboard/summary | 데이터 없는 사용자 | 신규 사용자 | 200, 모든 카운트 0 |
| GET /dashboard/pipeline | 인증된 사용자, 정상 조회 | Bearer Token | 200, 5개 stage 반환 |
| GET /dashboard/pipeline | 인증 없음 | 토큰 없음 | 401, AUTH_002 |
| GET /dashboard/statistics | 6개월 통계 | Bearer Token, months=6 | 200, monthly 6개 + cumulative |
| GET /dashboard/statistics | 12개월 최대 | months=12 | 200, monthly 12개 |
| GET /dashboard/statistics | months 초과 | months=13 | 400, VALIDATION_001 |

### Tracking API

| API | 시나리오 | 입력 | 예상 결과 |
|-----|----------|------|-----------|
| POST /bids/{id}/tracking | 최초 관심 등록 | status="interested" | 201, 추적 생성 |
| POST /bids/{id}/tracking | 상태 변경 | status="participating" (기존 interested) | 200, 상태 업데이트 |
| POST /bids/{id}/tracking | 낙찰 처리 | status="won", myBidPrice=450000000 | 200, is_winner=true |
| POST /bids/{id}/tracking | 탈락 처리 | status="lost" | 200, is_winner=false |
| POST /bids/{id}/tracking | 인증 없음 | 토큰 없음 | 401, AUTH_002 |
| POST /bids/{id}/tracking | 존재하지 않는 공고 | 잘못된 bid_id | 404, BID_001 |
| POST /bids/{id}/tracking | 잘못된 status | status="invalid" | 400, VALIDATION_001 |
| GET /bids/{id}/tracking | 추적 존재 | 정상 bid_id | 200, 추적 데이터 |
| GET /bids/{id}/tracking | 추적 없음 | 추적 미등록 bid_id | 404, DASHBOARD_001 |
| GET /bids/wins | 낙찰 이력 조회 | Bearer Token | 200, 낙찰 목록 |
| GET /bids/wins | 페이지네이션 | page=2, pageSize=5 | 200, meta 정확 |
| GET /bids/wins | 날짜 필터 | startDate=2026-01-01 | 200, 필터된 목록 |

---

## 경계 조건 / 에러 케이스

### 데이터 경계
- 추적 레코드 0건일 때 KPI 카드: 모든 수치 0, winRate 0.0 (0으로 나누기 방지)
- 낙찰 0건, 탈락 0건일 때 낙찰률: 0.0 (not NaN)
- myBidPrice가 null인 상태에서 ROI 계산: 해당 건 제외
- budget이 0인 공고의 bidRate 계산: null 반환
- 동일 공고에 대해 중복 tracking POST: upsert 동작 (에러 아님)
- 매우 긴 notes (10000자): 정상 저장 (TEXT 타입)

### 상태 전이 경계
- interested -> won (참여/제출 건너뛰기): 허용 (비즈니스 규칙상 자유 전이)
- won -> participating (역전이): 허용 (잘못된 입력 수정 가능)
- submitted -> submitted (동일 상태): 정상 처리, submitted_at 갱신

### 성능 경계
- 추적 레코드 1000건 이상 사용자: 파이프라인 응답 2초 이내
- 통계 12개월 집계: 응답 3초 이내
- 동시 폴링 100명: Redis 캐싱으로 DB 부하 분산

### 프론트엔드 경계
- 폴링 중 네트워크 오류: 에러 무시, 다음 폴링 정상 실행
- 낙관적 업데이트 후 서버 실패: 롤백하여 이전 상태 복원
- 브라우저 비활성 탭: 폴링 중지 (visibilitychange 이벤트)

---

## 회귀 테스트

| 기존 기능 | 영향 여부 | 검증 방법 |
|-----------|-----------|-----------|
| F-01 공고 목록 조회 (GET /bids) | 영향 없음 | 기존 테스트 통과 확인 |
| F-01 공고 상세 조회 (GET /bids/{id}) | 영향 없음 | 기존 테스트 통과 확인 |
| F-01 매칭 결과 조회 (GET /bids/{id}/matches) | 영향 없음 | 기존 테스트 통과 확인 |
| F-02 스코어링 조회 (GET /bids/{id}/scoring) | 영향 없음 | 기존 테스트 통과 확인 |
| F-04 투찰 전략 (GET /bids/{id}/strategy) | 영향 없음 | 기존 테스트 통과 확인 |
| F-07 인증 (JWT 토큰 검증) | 영향 없음 (재사용) | 인증 미들웨어 동일 패턴 |
| models/__init__.py | UserBidTracking 추가 | 기존 모델 import 에러 없음 확인 |
| api/v1/router.py | dashboard 라우터 추가 | 기존 라우트 충돌 없음 확인 |

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-03-08 | F-06 테스트 명세 초안 작성 |
