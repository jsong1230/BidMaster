# F-04 낙찰가 예측 및 투찰 전략 -- 테스트 명세

## 참조
- 설계서: docs/specs/F-04-bidding-strategy/design.md
- 인수조건: docs/project/features.md #F-04

---

## 단위 테스트

### BiddingStrategyService

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| `_calculate_distribution` | 정상 데이터 10건 | bid_rates=[0.85, 0.87, 0.88, 0.89, 0.89, 0.90, 0.91, 0.92, 0.93, 0.95] | mean~0.899, median~0.895, q25~0.88, q75~0.92, std>0, sampleCount=10 |
| `_calculate_distribution` | 단일 데이터 | bid_rates=[0.90] | mean=0.90, std=0.0, median=0.90, q25=0.90, q75=0.90, sampleCount=1 |
| `_calculate_distribution` | 빈 데이터 | bid_rates=[] | None 반환 (분포 계산 불가) |
| `_calculate_distribution` | 동일 값 | bid_rates=[0.90, 0.90, 0.90] | mean=0.90, std=0.0, median=0.90 |
| `_calculate_ranges_qualification` | 유사 공고 데이터 있음 | estimated_price=450000000, distribution 존재 | 3개 구간 모두 price > 0, safe.maxRate <= 0.95 |
| `_calculate_ranges_qualification` | 유사 공고 데이터 없음 | estimated_price=450000000, distribution=None | 기본 구간 사용 (88~95%), safe.minPrice=450M*0.92 |
| `_calculate_ranges_qualification` | estimated_price=0 | estimated_price=0 | 모든 price=0 (또는 에러 처리) |
| `_calculate_ranges_lowest_price` | 정상 분포 | estimated_price=200M, distribution(mean=0.87, std=0.04) | aggressive.minRate < moderate.minRate < safe.minRate |
| `_calculate_ranges_lowest_price` | std=0 (편차 없음) | distribution(mean=0.87, std=0.0) | 모든 구간이 mean 근처로 수렴 |
| `_estimate_win_probability` | 적격심사, 적정 구간 | bid_rate=0.91, 적격심사 분포 | 확률 50~80% |
| `_estimate_win_probability` | 적격심사, 너무 낮음 | bid_rate=0.80, 적격심사 분포 | 확률 10~30% (덤핑 의심) |
| `_estimate_win_probability` | 적격심사, 너무 높음 | bid_rate=0.99, 적격심사 분포 | 확률 20~40% (비용 초과) |
| `_estimate_win_probability` | 최저가, 매우 낮음 | bid_rate=0.82, 최저가 분포 | 확률 70~90% (유리) |
| `_estimate_win_probability` | 최저가, 높음 | bid_rate=0.95, 최저가 분포 | 확률 5~20% (불리) |
| `_estimate_win_probability` | 분포 데이터 없음 | bid_rate=0.90, distribution=None | 기본 확률 50% |
| `_determine_risk_level` | safe 구간 내 | bid_rate=0.93, ranges(safe: 0.92~0.95) | ("safe", "낮은 리스크") |
| `_determine_risk_level` | moderate 구간 내 | bid_rate=0.90, ranges(moderate: 0.89~0.92) | ("moderate", "중간 리스크") |
| `_determine_risk_level` | aggressive 구간 내 | bid_rate=0.87, ranges(aggressive: 0.86~0.89) | ("aggressive", "높은 리스크") |
| `_determine_risk_level` | 구간 외 (초과) | bid_rate=0.98, ranges | ("safe" 또는 "over_safe", 라벨) |
| `_determine_risk_level` | 구간 외 (미달) | bid_rate=0.80, ranges | ("aggressive" 또는 "extreme", 라벨) |
| `_generate_strategy_report` | 적격심사 공고 | bid(적격심사), distribution 존재 | contractMethodStrategy에 "기술"/"종합 평가" 키워드 포함 |
| `_generate_strategy_report` | 최저가 공고 | bid(최저가), distribution 존재 | contractMethodStrategy에 "가격 경쟁" 키워드 포함 |
| `_generate_strategy_report` | 유사 공고 없음 | bid, distribution=None | "데이터 부족" 문구 포함 |
| `_get_estimated_price` | estimated_price 존재 | bid(estimated_price=450M, budget=500M) | 450000000 (estimated_price 우선) |
| `_get_estimated_price` | estimated_price 없음, budget 존재 | bid(estimated_price=None, budget=500M) | 500000000 (budget 폴백) |
| `_get_estimated_price` | 둘 다 없음 | bid(estimated_price=None, budget=None) | None |

### 시뮬레이션

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| `simulate` | 정상 시뮬레이션 | bid_id=valid, bid_price=410M | bidRate > 0, winProbability 0~100, riskLevel 존재 |
| `simulate` | 예정가격 없는 공고 | bid(estimated_price=None, budget=None) | AppException(STRATEGY_002, 422) |
| `simulate` | bid_price=0 | bid_price=0 | bidRate=0, winProbability=높음(최저가) 또는 낮음(적격심사) |
| `simulate` | bid_price > estimated_price | bid_price=500M, estimated=450M | bidRate > 1.0, winProbability 매우 낮음 |
| `simulate` | comparisonWithRecommended | 유효한 입력 | safe/moderate/aggressive 각각 비교 문구 포함 |

---

## 통합 테스트

| API | 시나리오 | 입력 | 예상 결과 |
|-----|----------|------|-----------|
| GET /api/v1/bids/{id}/strategy | 정상 분석 (적격심사) | 인증 토큰, 적격심사 공고 | 200, contractMethod="적격심사", recommendedRanges 3개 구간, strategyReport 포함 |
| GET /api/v1/bids/{id}/strategy | 정상 분석 (최저가) | 인증 토큰, 최저가 공고 | 200, contractMethod="최저가", recommendedRanges 3개 구간 |
| GET /api/v1/bids/{id}/strategy | 인증 없음 | Authorization 헤더 없음 | 401, AUTH_002 |
| GET /api/v1/bids/{id}/strategy | 존재하지 않는 공고 | 잘못된 bid_id | 404, BID_001 |
| GET /api/v1/bids/{id}/strategy | 공고 ID 형식 오류 | bid_id="invalid" | 422, VALIDATION_001 |
| GET /api/v1/bids/{id}/strategy | winRateDistribution 구조 | 유사 공고 이력 존재 | sampleCount > 0, mean/std/median/q25/q75 모두 존재 |
| GET /api/v1/bids/{id}/strategy | 유사 공고 데이터 없음 | 이력 없는 카테고리 | 200, 기본 분포/구간 사용, strategyReport에 "데이터 부족" 표시 |
| GET /api/v1/bids/{id}/strategy | estimatedPrice 없는 공고 | budget만 존재 | 200, estimatedPrice=budget 폴백, recommendedRanges 정상 |
| GET /api/v1/bids/{id}/strategy | budget도 없는 공고 | 둘 다 NULL | 200, recommendedRanges 내 price=null, strategyReport에 안내 |
| GET /api/v1/bids/{id}/strategy | recommendedRanges 일관성 | 정상 요청 | safe.minPrice >= moderate.maxPrice (또는 근사), moderate.minPrice >= aggressive.maxPrice |
| GET /api/v1/bids/{id}/strategy | winProbability 범위 | 정상 요청 | 모든 winProbability: 0 <= p <= 100 |
| POST /api/v1/bids/{id}/strategy/simulate | 정상 시뮬레이션 | bidPrice=410000000 | 200, bidRate > 0, winProbability 0~100, riskLevel 포함 |
| POST /api/v1/bids/{id}/strategy/simulate | 인증 없음 | Authorization 없음 | 401, AUTH_002 |
| POST /api/v1/bids/{id}/strategy/simulate | bidPrice 누락 | 빈 body | 400, VALIDATION_001 |
| POST /api/v1/bids/{id}/strategy/simulate | bidPrice 음수 | bidPrice=-100 | 400, VALIDATION_001 |
| POST /api/v1/bids/{id}/strategy/simulate | bidPrice=0 | bidPrice=0 | 200, bidRate=0, 특수 처리 |
| POST /api/v1/bids/{id}/strategy/simulate | 존재하지 않는 공고 | 잘못된 bid_id | 404, BID_001 |
| POST /api/v1/bids/{id}/strategy/simulate | comparisonWithRecommended | 유효 입력 | safe/moderate/aggressive 비교 문구 포함 |
| POST /api/v1/bids/{id}/strategy/simulate | 예정가격 없는 공고 | estimated_price=None, budget=None | 422, STRATEGY_002 |

---

## 경계 조건 / 에러 케이스

- 유사 공고 낙찰 이력 0건: 기본 분포 사용, strategyReport에 "데이터 부족" 명시
- 유사 공고 1건: 분포 계산 시 std=0, 범위가 점으로 수렴 -> 기본 구간으로 폴백
- estimated_price=0: 0으로 나누기 방지, 에러 또는 기본값 처리
- budget=0, estimated_price=None: STRATEGY_002 에러
- bid_rate > 1.0 (투찰가 > 예정가): 시뮬레이션에서 winProbability 매우 낮게 표시
- bid_rate < 0.5 (예정가의 50% 미만): 덤핑 경고 표시
- contract_method=NULL 또는 알 수 없는 방식: 적격심사를 기본으로 사용
- numpy import 실패: 순수 Python 통계 함수로 폴백 (mean, sorted percentile)
- 동시 요청 (같은 bid_id): 무상태이므로 문제 없음

---

## 회귀 테스트

| 기존 기능 | 영향 여부 | 검증 방법 |
|-----------|-----------|-----------|
| F-01 GET /bids 목록 조회 | 영향 없음 | 기존 통합 테스트 통과 확인 |
| F-01 GET /bids/{id} 상세 조회 | 영향 없음 | 기존 통합 테스트 통과 확인 |
| F-01 GET /bids/{id}/matches | 영향 없음 | 기존 통합 테스트 통과 확인 |
| F-01 GET /bids/matched | 영향 없음 | 기존 통합 테스트 통과 확인 |
| F-01 POST /bids/collect | 영향 없음 | 기존 통합 테스트 통과 확인 |
| F-02 GET /bids/{id}/scoring | 영향 없음 (독립 엔드포인트) | F-02 통합 테스트 통과 확인 |
| F-02 bid_win_history 데이터 | 읽기 전용 사용 (쓰기 안 함) | F-02 데이터 무결성 확인 |
| bids API 라우터 | 신규 엔드포인트 추가 | 기존 엔드포인트 URL 충돌 없음 확인 |
