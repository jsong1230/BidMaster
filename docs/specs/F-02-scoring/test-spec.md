# F-02 낙찰 가능성 스코어링 -- 테스트 명세

## 참조
- 설계서: docs/specs/F-02-scoring/design.md
- 인수조건: docs/project/features.md #F-02

---

## 단위 테스트

### ScoringService

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| `_calculate_competition` | 유사 공고 낙찰 이력 5건, 고유 업체 3개 | bid(org=행정안전부, cat=정보화, type=일반경쟁) | 점수 70.0 (경쟁 낮음), factors에 "추정 경쟁 업체 수: 3개사" 포함 |
| `_calculate_competition` | 유사 공고 없음 | bid(org=미등록기관) | 점수 50.0 (기본값), factors에 "유사 공고 데이터 없음" |
| `_calculate_competition` | 유사 공고 10건 이상, 고유 업체 10개+ | bid(경쟁 과열 분야) | 점수 0~20 (경쟁 매우 높음) |
| `_calculate_capability` | 실적 7건, 인증 2건, 규모 medium | company + performances + certifications | 점수 60~80, factors에 실적/인증/규모 상세 포함 |
| `_calculate_capability` | 실적 0건, 인증 0건, 규모 small | 빈 company | 점수 0~30 (역량 부족) |
| `_calculate_capability` | 대표실적 포함, 동일 발주기관 실적 존재 | performances에 is_representative=True + 동일 기관 | 보너스 반영된 점수 (기본 대비 +20~30) |
| `_calculate_capability` | 만료된 인증만 보유 | certifications(expiry_date < 오늘) | 인증 유효율 0, 인증 점수 낮음 |
| `_calculate_market` | budget=5억, 평균 수행금액=4억, 적격심사, 마감 14일후 | bid + performances | 점수 70~90, 예산 적합, 방식 유리, 시간 충분 |
| `_calculate_market` | budget=50억, 평균 수행금액=1억, 최저가, 마감 2일후 | bid + performances | 점수 20~40, 예산 부적합, 시간 부족 |
| `_calculate_market` | 실적 없음 (평균 수행금액 계산 불가) | 빈 performances | 예산 적합성 기본 50점, 기타 요소로 산출 |
| `_compute_total` | suit=80, comp=60, cap=70, market=60 | scores dict | 80*0.3 + 60*0.25 + 70*0.3 + 60*0.15 = 69.0 |
| `_compute_total` | 모든 항목 100 | scores dict | 100.0 |
| `_compute_total` | 모든 항목 0 | scores dict | 0.0 |
| `_determine_recommendation` | total_score=85 | 85 | ("strongly_recommended", "강력추천", reason 포함) |
| `_determine_recommendation` | total_score=65 | 65 | ("recommended", "추천", reason 포함) |
| `_determine_recommendation` | total_score=45 | 45 | ("neutral", "보류", reason 포함) |
| `_determine_recommendation` | total_score=30 | 30 | ("not_recommended", "비추천", reason + 사유 포함) |
| `_determine_recommendation` | total_score=80 (경계값) | 80 | ("strongly_recommended", ...) |
| `_determine_recommendation` | total_score=60 (경계값) | 60 | ("recommended", ...) |
| `_determine_recommendation` | total_score=40 (경계값) | 40 | ("neutral", ...) |
| `_get_competitor_stats` | 유사 공고 이력 존재 | bid | estimatedCompetitors > 0, topCompetitors 리스트 |
| `_get_competitor_stats` | 이력 없음 | bid | estimatedCompetitors=0, topCompetitors=[] |
| `_get_similar_bid_stats` | 유사 공고 3건 | bid | totalCount=3, avgWinRate/avgWinningPrice 산출 |
| `_get_similar_bid_stats` | 유사 공고 없음 | bid | totalCount=0, avgWinRate=None, avgWinningPrice=None |

### BidMatchService 변경

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| `_score_to_recommendation` | 확장된 4단계 지원 | score=85 | ("strongly_recommended", ...) |
| `_score_to_recommendation` | 기존 3단계 하위 호환 | score=75 | ("recommended", ...) |
| `analyze_match(full_scoring=False)` | 기본 동작 유지 | user_id, bid_id | competition/capability/market = 0 (기존 F-01 동작) |
| `analyze_match(full_scoring=True)` | 전체 스코어링 | user_id, bid_id | 4개 항목 모두 > 0 |

### BidWinHistory 모델

| 대상 | 시나리오 | 입력 | 예상 결과 |
|------|----------|------|-----------|
| 모델 생성 | 필수 필드 설정 | bid_number, winner_name, winning_price | 인스턴스 정상 생성, id 자동 생성 |
| bid_rate 범위 | 유효 범위 | bid_rate=0.8920 | CHECK 통과 |
| bid_rate 범위 | 범위 초과 | bid_rate=2.5 | CHECK 위반 |

---

## 통합 테스트

| API | 시나리오 | 입력 | 예상 결과 |
|-----|----------|------|-----------|
| GET /api/v1/bids/{id}/scoring | 정상 스코어링 | 유효한 bid_id, 인증 토큰, 회사 보유 사용자 | 200, scores 4개 항목 모두 > 0, recommendation 포함 |
| GET /api/v1/bids/{id}/scoring | 인증 없음 | Authorization 헤더 없음 | 401, AUTH_002 |
| GET /api/v1/bids/{id}/scoring | 회사 미등록 사용자 | 회사 없는 사용자 토큰 | 404, COMPANY_001 |
| GET /api/v1/bids/{id}/scoring | 존재하지 않는 공고 | 잘못된 bid_id | 404, BID_001 |
| GET /api/v1/bids/{id}/scoring | 공고 ID 형식 오류 | bid_id="invalid" | 422, VALIDATION_001 |
| GET /api/v1/bids/{id}/scoring | lazy evaluation | 스코어링 미수행 공고 | 200, 즉시 분석 실행 후 결과 반환 |
| GET /api/v1/bids/{id}/scoring | 이미 스코어링된 공고 | 재요청 | 200, 캐시된 결과 반환 (analyzed_at 동일) |
| GET /api/v1/bids/{id}/scoring | scores.total 범위 | 정상 요청 | total >= 0 and total <= 100 |
| GET /api/v1/bids/{id}/scoring | recommendation 값 | 정상 요청 | strongly_recommended / recommended / neutral / not_recommended 중 하나 |
| GET /api/v1/bids/{id}/scoring | competitorStats 포함 | 유사 공고 이력 존재 | estimatedCompetitors >= 0, topCompetitors 배열 |
| GET /api/v1/bids/{id}/scoring | similarBidStats 포함 | 유사 공고 이력 존재 | totalCount >= 0, avgWinRate, avgWinningPrice 포함 |
| GET /api/v1/bids/{id}/scoring | details 분해 | 정상 요청 | details.suitability, competition, capability, market 각각 score + factors 포함 |
| GET /api/v1/bids/{id}/matches | 하위 호환성 | 기존 매칭 요청 | 200, 기존 응답 구조 유지 (recommendation 값 확장될 수 있음) |

---

## 경계 조건 / 에러 케이스

- 과거 낙찰 데이터 0건 (빈 bid_win_history): competition_score=50 (기본값), 경쟁사 통계 빈 배열
- 회사 실적 0건 + 인증 0건: capability_score=0~20 (최저 수준), 역량 부족 사유 표시
- 공고 budget=NULL: market_score의 예산 적합성 부분 기본 50점
- 공고 deadline 이미 경과: market_score의 시기 점수 0, 전체 점수에 반영
- TF-IDF 계산 실패 (빈 텍스트): suitability_score=0, factors에 "텍스트 부족" 표시
- total_score 범위: 항상 0~100 (min/max 클램핑 확인)
- recommendation 4단계 경계값: 80, 60, 40 각각 정확한 등급 배정
- 동시 스코어링 요청 (같은 user+bid): 중복 실행 방지 또는 멱등 결과

---

## 회귀 테스트

| 기존 기능 | 영향 여부 | 검증 방법 |
|-----------|-----------|-----------|
| F-01 GET /bids 목록 조회 | 영향 없음 | 기존 통합 테스트 통과 확인 |
| F-01 GET /bids/{id} 상세 조회 | 영향 없음 | 기존 통합 테스트 통과 확인 |
| F-01 GET /bids/{id}/matches | recommendation 값 확장 가능 | strongly_recommended 포함 시에도 응답 구조 동일 확인 |
| F-01 GET /bids/matched | 영향 없음 | 기존 통합 테스트 통과 확인 |
| F-01 POST /bids/collect | 영향 없음 | 기존 통합 테스트 통과 확인 |
| BidMatchService.analyze_match() | full_scoring=False 기본 동작 유지 | competition/capability/market = 0 확인 |
| BidMatchService._score_to_recommendation() | 기존 3단계 점수대 동작 유지 | 70+ = recommended 유지 (80+ = strongly_recommended 추가) |
