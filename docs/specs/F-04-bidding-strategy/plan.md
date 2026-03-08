# F-04 낙찰가 예측 및 투찰 전략 — 구현 계획

## 참조
- 설계서: docs/specs/F-04-bidding-strategy/design.md
- 테스트 명세: docs/specs/F-04-bidding-strategy/test-spec.md
- 인수조건: docs/project/features.md #F-04

---

## 구현 태스크

### Backend

#### T1: 투찰 전략 스키마 추가
- **파일**: `backend/src/schemas/strategy.py`
- **내용**:
  - WinRateDistribution (mean, std, median, q25, q75, minRate, maxRate, sampleCount)
  - RecommendedRange (label, minPrice, maxPrice, minRate, maxRate, winProbability, description)
  - RecommendedRanges (safe, moderate, aggressive) — 3단계 리스크
  - StrategyReport (contractMethodStrategy, marketInsight, riskFactors, recommendations)
  - StrategyResult (bidId, bidTitle, contractMethod, estimatedPrice, budget, winRateDistribution, recommendedRanges, strategyReport, analyzedAt)
  - SimulateRequest (bidPrice: int, gt=0)
  - SimulationResult (bidId, inputPrice, bidRate, winProbability, riskLevel, riskLabel, analysis, comparisonWithRecommended)
- **완료 기준**: Pydantic 스키마 직렬화/역직렬화 성공

#### T2: BiddingStrategyService 구현
- **파일**: `backend/src/services/bidding_strategy_service.py`
- **내용**:
  - QUALIFICATION_RANGES = {safe: (0.92, 0.95), moderate: (0.89, 0.92), aggressive: (0.86, 0.89)}
  - LOWEST_PRICE_SIGMA = {safe: (0.0, 0.5), moderate: (0.5, 1.0), aggressive: (1.0, 2.0)}
  - `analyze_strategy(bid_id)` — 전략 분석 메인 (BID_001/STRATEGY_001)
  - `simulate(bid_id, bid_price)` — 투찰가 시뮬레이션 (STRATEGY_002 처리)
  - `_calculate_distribution(bid_rates)` — numpy 기반 분포 계산 (빈 배열 → None)
  - `_calculate_ranges_qualification(estimated_price, distribution)` — 적격심사 구간 (기본값/실데이터 분기)
  - `_calculate_ranges_lowest_price(estimated_price, distribution)` — 최저가 구간 (시그마 기반)
  - `_estimate_win_probability(bid_rate, distribution, contract_method)` — 낙찰 확률 (0~100)
  - `_determine_risk_level(bid_rate, ranges)` — safe/moderate/aggressive 판정
  - `_generate_strategy_report(bid, distribution, ranges)` — 계약방식별 전략 리포트
  - `_get_similar_win_history(bid)` — 유사 공고 낙찰 이력 (인메모리 + DB 폴백)
  - `_get_estimated_price(bid)` — estimated_price > budget > None 우선순위
  - F-02 SAMPLE_WIN_HISTORY + ADDITIONAL_WIN_HISTORY 공유 사용
  - contract_method=NULL 시 적격심사 기본 사용
  - estimated_price=0 시 0으로 나누기 방지 처리
- **완료 기준**: 단위 테스트 전체 통과

#### T3: bids API 전략 엔드포인트 추가
- **파일**: `backend/src/api/v1/bids.py`
- **내용**:
  - `GET /api/v1/bids/{id}/strategy` 엔드포인트 추가
    - JWT 인증 확인 (AUTH_002 → 401)
    - 공고 존재 확인 (BID_001 → 404)
    - BiddingStrategyService.analyze_strategy() 호출
  - `POST /api/v1/bids/{id}/strategy/simulate` 엔드포인트 추가
    - JWT 인증 확인 (AUTH_002 → 401)
    - 공고 존재 확인 (BID_001 → 404)
    - bidPrice 유효성 검사 (0 이하 → VALIDATION_001 → 400)
    - BiddingStrategyService.simulate() 호출 (STRATEGY_002 → 422)
- **완료 기준**: 통합 테스트 전체 통과

---

### Frontend

#### T4: 투찰 전략 UI 컴포넌트
- **파일**: `frontend/src/components/strategy/`
- **내용**:
  - WinRateHistogram — 낙찰가율 분포 막대 그래프 (Recharts)
  - RangeSelector — safe/moderate/aggressive 3단계 선택 UI
  - SimulateInput — 투찰가 입력 + 낙찰 확률 결과 표시
  - StrategyReportCard — 전략 리포트 텍스트 카드
  - RiskBadge — 리스크 레벨 배지
- **완료 기준**: Storybook에서 각 컴포넌트 렌더링 확인

#### T5: 투찰 전략 페이지
- **파일**: `frontend/src/app/bids/[id]/strategy/page.tsx`
- **내용**:
  - `GET /api/v1/bids/{id}/strategy` API 호출
  - 낙찰가율 분포 시각화 섹션
  - 3단계 추천 투찰가 범위 카드
  - 전략 리포트 섹션 (계약방식별 전략 + 시장 인사이트)
  - 투찰가 시뮬레이션 입력 폼
    - `POST /api/v1/bids/{id}/strategy/simulate` 호출
    - 낙찰 확률 + 리스크 레벨 즉시 표시
    - 추천 범위 대비 비교 표시
  - 데이터 부족 시 안내 메시지 (sampleCount=0)
- **완료 기준**: E2E 테스트 통과 (공고 상세 → 전략 탭 → 시뮬레이션)

---

## 구현 순서

```
T1 (스키마) → T2 (서비스) → T3 (API)
                              ↓
                   T4 (컴포넌트) → T5 (페이지)
```

T1~T3은 순차적으로 구현 (각 단계가 다음 단계에 의존).
T4~T5는 T3 완료 후 병렬 가능하나 순차 권장.

---

## F-02 의존성 체크리스트

- [ ] bid_win_history 인메모리 store 공유 사용 가능 (F-02 T3 완료 후)
- [ ] SAMPLE_WIN_HISTORY 임포트 경로 확인
- [ ] ScoringService._get_win_history() 재사용 여부 결정 (독립 구현 vs 위임)

> F-02 미완료 시: ADDITIONAL_WIN_HISTORY를 자체 인메모리로 사용하여 독립 구현 가능

---

## 에러 코드 매핑

| 코드 | HTTP | 발생 위치 |
|------|------|----------|
| BID_001 | 404 | T3 — 공고 조회 실패 |
| AUTH_002 | 401 | T3 — JWT 토큰 없음 |
| VALIDATION_001 | 400 | T3 — bidPrice 누락/음수 |
| STRATEGY_001 | 500 | T2/T3 — 전략 분석 내부 오류 |
| STRATEGY_002 | 422 | T2/T3 — 예정가격 정보 없음 |

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-03-08 | 초기 작성 |
