# F-02 낙찰 가능성 스코어링 — 구현 계획

## 참조
- 설계서: docs/specs/F-02-scoring/design.md
- 테스트 명세: docs/specs/F-02-scoring/test-spec.md
- 인수조건: docs/project/features.md #F-02

---

## 구현 태스크

### Backend

#### T1: BidWinHistory 모델 생성
- **파일**: `backend/src/models/bid_win_history.py`
- **내용**:
  - BidWinHistory SQLAlchemy 모델 (bid_number, winner_name, winner_business_number, winning_price, bid_rate, winning_date, created_at)
  - UUID PK, 인덱스 3개 (bid_number, winner_business_number, winning_date)
  - models/__init__.py 에 BidWinHistory import 추가
- **완료 기준**: `BidWinHistory()` 인스턴스 생성 성공, id 자동 생성

#### T2: 스코어링 스키마 추가
- **파일**: `backend/src/schemas/scoring.py`
- **내용**:
  - ScoreBreakdown (score, factors)
  - ScoringScores (suitability, competition, capability, market, total)
  - ScoringWeights (suitability=0.30, competition=0.25, capability=0.30, market=0.15)
  - CompetitorStats (estimatedCompetitors, topCompetitors)
  - SimilarBidStats (totalCount, avgWinRate, avgWinningPrice)
  - ScoringResult (id, bidId, userId, scores, weights, recommendation, recommendationLabel, recommendationReason, details, competitorStats, similarBidStats, analyzedAt)
- **완료 기준**: Pydantic 스키마 직렬화/역직렬화 성공

#### T3: ScoringService 구현
- **파일**: `backend/src/services/scoring_service.py`
- **내용**:
  - WEIGHTS = {suitability: 0.30, competition: 0.25, capability: 0.30, market: 0.15}
  - RECOMMENDATION_THRESHOLDS = {strongly_recommended: 80, recommended: 60, neutral: 40}
  - `score(user_id, bid_id)` — 종합 스코어링 (lazy evaluation)
  - `_calculate_competition(bid)` — 유사 공고 낙찰 이력 기반 역점수 (없으면 50)
  - `_calculate_capability(company, performances, certifications, bid)` — 실적/인증/규모 가중합
  - `_calculate_market(bid, performances)` — 예산/계약방식/시기 점수
  - `_compute_total(scores)` — 가중합 총점
  - `_determine_recommendation(total_score, details)` — 4단계 등급 결정
  - `_get_competitor_stats(bid)` — 경쟁사 통계
  - `_get_similar_bid_stats(bid)` — 유사 공고 통계
  - `_get_win_history(organization, category, bid_type)` — 인메모리 + DB 폴백
  - `_update_match_scores(user_id, bid_id, scores, recommendation, reason)` — user_bid_matches 갱신
  - SAMPLE_WIN_HISTORY 인메모리 시드 데이터 로드
- **완료 기준**: 단위 테스트 전체 통과

#### T4: bids API 스코어링 엔드포인트 추가
- **파일**: `backend/src/api/v1/bids.py`
- **내용**:
  - `GET /api/v1/bids/{id}/scoring` 엔드포인트 추가
  - JWT 인증 확인 (AUTH_002 → 401)
  - 회사 프로필 존재 확인 (COMPANY_001 → 404)
  - 공고 존재 확인 (BID_001 → 404)
  - ScoringService.score() 호출 (SCORING_001 → 500, SCORING_002 → 504)
  - recommendation 필드 4단계 확장 (strongly_recommended 추가)
  - BidMatchService.analyze_match()에 full_scoring 옵션 추가
  - schemas/bid_match.py recommendation 값 확장
- **완료 기준**: 통합 테스트 전체 통과

---

### Frontend

#### T5: 스코어링 결과 UI 컴포넌트
- **파일**: `frontend/src/components/scoring/`
- **내용**:
  - ScoreRadarChart — 4개 항목 레이더 차트 (Recharts)
  - ScoreBreakdownCard — 항목별 상세 점수 + factors 목록
  - RecommendationBadge — 4단계 배지 (강력추천/추천/보류/비추천)
  - CompetitorList — 예상 경쟁사 목록
  - SimilarBidStats — 유사 공고 통계 요약
- **완료 기준**: Storybook에서 각 컴포넌트 렌더링 확인

#### T6: 스코어링 결과 페이지
- **파일**: `frontend/src/app/bids/[id]/scoring/page.tsx`
- **내용**:
  - `GET /api/v1/bids/{id}/scoring` API 호출
  - 로딩 상태 (스켈레톤 UI)
  - 회사 프로필 미등록 시 안내 (COMPANY_001)
  - 총점 + recommendation 강조 표시
  - 항목별 점수 breakdown
  - 경쟁사 통계 섹션
  - 유사 공고 통계 섹션
- **완료 기준**: E2E 테스트 통과 (공고 상세 → 스코어링 탭)

---

## 구현 순서

```
T1 (모델) → T2 (스키마) → T3 (서비스) → T4 (API)
                                          ↓
                               T5 (컴포넌트) → T6 (페이지)
```

T1~T4는 순차적으로 구현 (각 단계가 다음 단계에 의존).
T5~T6은 T4 완료 후 병렬 가능하나 순차 권장.

---

## 에러 코드 매핑

| 코드 | HTTP | 발생 위치 |
|------|------|----------|
| BID_001 | 404 | T4 — 공고 조회 실패 |
| COMPANY_001 | 404 | T4 — 회사 프로필 없음 |
| AUTH_002 | 401 | T4 — JWT 토큰 없음 |
| SCORING_001 | 500 | T3/T4 — 스코어링 내부 오류 |
| SCORING_002 | 504 | T3/T4 — 60초 타임아웃 |

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-03-08 | 초기 작성 |
