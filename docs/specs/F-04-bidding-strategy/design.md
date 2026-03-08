# F-04 낙찰가 예측 및 투찰 전략 -- 변경 설계서

## 1. 참조
- 인수조건: docs/project/features.md #F-04
- 시스템 분석: docs/system/system-analysis.md
- ERD: docs/system/erd.md (bids, bid_win_history, user_bid_tracking)
- API 컨벤션: docs/system/api-conventions.md
- F-01 설계: docs/specs/F-01-bid-collection/design.md
- F-02 설계: docs/specs/F-02-scoring/design.md (bid_win_history, ScoringService)

---

## 2. 변경 범위

- **변경 유형**: 신규 추가 (F-02의 bid_win_history 테이블/서비스 활용)
- **영향 받는 모듈**:
  - bids API 라우터 (strategy 엔드포인트 추가)
  - schemas/ (strategy 관련 스키마 추가)
  - 신규 BiddingStrategyService

---

## 3. 영향 분석

### 기존 API 변경

| API | 현재 | 변경 후 | 하위 호환성 |
|-----|------|---------|-------------|
| (없음) | - | 신규 API 추가 | 해당 없음 |

### 기존 DB 변경

| 테이블 | 변경 내용 | 마이그레이션 전략 |
|--------|----------|------------------|
| bid_win_history | 변경 없음 (F-02에서 생성) | - |
| user_bid_tracking | 기존 ERD 정의 그대로 신규 생성 (시뮬레이션 기록용) | 신규 마이그레이션 |

### 사이드 이펙트
- F-02의 bid_win_history 데이터를 공유 사용 (읽기 전용)
- F-02의 ScoringService._get_win_history() 메서드 재사용 가능
- bids 테이블의 contract_method, budget, estimated_price 컬럼 적극 활용

---

## 4. 아키텍처 결정

### 결정 1: 낙찰가 예측 방식
- **선택지**: A) 회귀 모델 (sklearn LinearRegression) / B) 통계 기반 (평균, 분위수) / C) 하이브리드
- **결정**: B) 통계 기반 (numpy 활용)
- **근거**:
  - MVP 수준에서 단순 통계가 충분
  - 데이터 부족 시 회귀 모델은 과적합 위험
  - 평균/표준편차/분위수로 직관적 결과 제공
  - numpy만 사용하여 의존성 최소화 (sklearn은 F-02에서 이미 추가됨)

### 결정 2: 투찰가 전략 차별화
- **선택지**: A) 단일 전략 / B) 낙찰 방식별 전략 분리
- **결정**: B) 낙찰 방식별 전략 분리
- **근거**:
  - 인수조건 명시: 적격심사 vs 최저가 별도 전략
  - 적격심사: 예정가격 대비 88~95% 구간이 유리
  - 최저가: 경쟁사 최저가 예측 포함
  - contract_method 컬럼으로 분기

### 결정 3: 시뮬레이션 결과 저장
- **선택지**: A) user_bid_tracking에 저장 / B) 별도 시뮬레이션 테이블 / C) 저장 안 함 (무상태)
- **결정**: C) 저장 안 함 (무상태, 실시간 계산)
- **근거**:
  - 시뮬레이션은 일회성 조회, 저장 불필요
  - 낙찰가 입력 시 user_bid_tracking은 별도 기능(F-06)에서 사용
  - MVP 단순성 유지

---

## 5. 투찰 전략 모델 설계

### 5.1 낙찰가율 분포 분석

유사 공고의 bid_win_history에서 bid_rate 분포를 분석.

```
유사 공고 조건:
  - 동일 organization OR category
  - 동일 contract_method (적격심사/최저가)
  - 최근 1년 이내 낙찰 건

분석 지표:
  - mean: 평균 낙찰가율
  - std: 표준편차
  - median: 중앙값
  - q25, q75: 25%, 75% 분위수
  - min_rate, max_rate: 최소/최대 낙찰가율
  - sample_count: 분석 대상 건수
```

### 5.2 추천 투찰가 범위 (3단계 리스크)

| 리스크 | 낙찰가율 구간 | 설명 |
|--------|-------------|------|
| 낮은 리스크 (safe) | median ~ q75 | 안전 구간, 낙찰 가능성 높으나 수익 보통 |
| 중간 리스크 (moderate) | q25 ~ median | 적정 구간, 낙찰 가능성/수익 균형 |
| 높은 리스크 (aggressive) | min_rate ~ q25 | 공격적 구간, 수익 높으나 낙찰 가능성 낮음 |

### 5.3 적격심사 전략 (contract_method = "적격심사")

```
기본 가정:
  - 적격심사는 기술 + 가격 종합 평가
  - 예정가격(estimated_price 또는 budget) 대비 88~95%가 유리 구간
  - 너무 낮은 가격은 덤핑 의심으로 감점

추천:
  safe:       estimated_price * 0.92 ~ 0.95
  moderate:   estimated_price * 0.89 ~ 0.92
  aggressive: estimated_price * 0.86 ~ 0.89

조건: 유사 공고 데이터 있으면 실데이터 기반으로 덮어씀
```

### 5.4 최저가 전략 (contract_method = "최저가")

```
기본 가정:
  - 최저가 낙찰은 순수 가격 경쟁
  - 유사 공고 최저 낙찰가율 기반 예측

추천:
  safe:       mean - 0.5 * std ~ mean
  moderate:   mean - 1.0 * std ~ mean - 0.5 * std
  aggressive: min_rate ~ mean - 1.0 * std

경쟁사 최저가 예측:
  - 유사 공고 최저 낙찰가율의 하위 10% 기준
  - estimated_competitor_min = estimated_price * percentile(bid_rates, 10)
```

### 5.5 투찰가 시뮬레이션

사용자가 특정 금액 입력 시 낙찰 확률 추정:

```
입력: my_bid_price
계산:
  1. my_bid_rate = my_bid_price / estimated_price
  2. 유사 공고 bid_rate 분포에서 my_bid_rate의 백분위 계산
  3. win_probability = percentile_rank(my_bid_rate in bid_rates)
     - 최저가: 낮을수록 유리 -> win_probability = 100 - percentile_rank
     - 적격심사: 적정 구간일수록 유리 -> 정규분포 확률밀도 기반
```

---

## 6. API 설계

### 6.1 GET /api/v1/bids/{id}/strategy

투찰 전략 분석 결과 조회

- **목적**: 특정 공고에 대한 낙찰가 분석 및 최적 투찰가 추천
- **인증**: 필요 (Bearer Token)
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "bidId": "uuid",
    "bidTitle": "2026년 정보시스템 고도화 사업",
    "contractMethod": "적격심사",
    "estimatedPrice": 450000000,
    "budget": 500000000,
    "winRateDistribution": {
      "mean": 0.8920,
      "std": 0.0350,
      "median": 0.8900,
      "q25": 0.8650,
      "q75": 0.9100,
      "minRate": 0.8200,
      "maxRate": 0.9500,
      "sampleCount": 12
    },
    "recommendedRanges": {
      "safe": {
        "label": "낮은 리스크 (안전)",
        "minPrice": 400500000,
        "maxPrice": 427500000,
        "minRate": 0.8900,
        "maxRate": 0.9500,
        "winProbability": 75,
        "description": "안전한 구간으로 낙찰 가능성이 높습니다."
      },
      "moderate": {
        "label": "중간 리스크 (적정)",
        "minPrice": 389250000,
        "maxPrice": 400500000,
        "minRate": 0.8650,
        "maxRate": 0.8900,
        "winProbability": 55,
        "description": "적정 구간으로 수익과 낙찰 가능성의 균형입니다."
      },
      "aggressive": {
        "label": "높은 리스크 (공격적)",
        "minPrice": 369000000,
        "maxPrice": 389250000,
        "minRate": 0.8200,
        "maxRate": 0.8650,
        "winProbability": 30,
        "description": "공격적 구간으로 수익은 높지만 낙찰 가능성이 낮습니다."
      }
    },
    "strategyReport": {
      "contractMethodStrategy": "적격심사 방식으로 기술력과 가격의 종합 평가가 이루어집니다. 예정가격 대비 89~95% 구간이 유리합니다.",
      "marketInsight": "유사 공고 12건 분석 결과 평균 낙찰가율 89.2%입니다. 최근 낙찰가율이 하락 추세입니다.",
      "riskFactors": [
        "경쟁 업체 수 5개사 추정 (보통 수준)",
        "예산 규모 대비 회사 실적 적합"
      ],
      "recommendations": [
        "기술 제안서 품질에 집중하여 기술 점수를 극대화하세요.",
        "투찰가는 예정가격의 90~93% 구간을 권장합니다."
      ]
    },
    "analyzedAt": "2026-03-08T10:00:00Z"
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | BID_001 | 404 | 공고를 찾을 수 없음 |
  | AUTH_002 | 401 | 인증 토큰 없음 |
  | STRATEGY_001 | 500 | 전략 분석 중 오류 |

### 6.2 POST /api/v1/bids/{id}/strategy/simulate

투찰가 시뮬레이션

- **목적**: 사용자 입력 금액의 낙찰 확률 계산
- **인증**: 필요 (Bearer Token)
- **Request Body**:
```json
{
  "bidPrice": 410000000
}
```
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "bidId": "uuid",
    "inputPrice": 410000000,
    "bidRate": 0.9111,
    "winProbability": 68,
    "riskLevel": "safe",
    "riskLabel": "낮은 리스크",
    "analysis": "입력 금액은 예정가격의 91.1%로, 유사 공고 평균(89.2%) 대비 높은 수준입니다. 낙찰 가능성은 약 68%로 추정됩니다.",
    "comparisonWithRecommended": {
      "safe": "추천 범위 내 (상한 근처)",
      "moderate": "추천 범위 초과",
      "aggressive": "추천 범위 초과"
    }
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | BID_001 | 404 | 공고를 찾을 수 없음 |
  | AUTH_002 | 401 | 인증 토큰 없음 |
  | VALIDATION_001 | 400 | bidPrice 누락 또는 음수 |
  | STRATEGY_001 | 500 | 시뮬레이션 중 오류 |

---

## 7. DB 설계

### 7.1 bid_win_history (F-02에서 생성, 공유 사용)

F-02 설계서 참조. 추가 변경 없음.

### 7.2 user_bid_tracking (신규, 향후 F-06용)

ERD에 정의된 테이블. F-04에서는 사용하지 않지만, 관련성이 높으므로 이 시점에서 모델만 생성.

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK | 추적 ID |
| user_id | UUID | FK -> users.id, NOT NULL | 사용자 ID |
| bid_id | UUID | FK -> bids.id, NOT NULL | 공고 ID |
| status | VARCHAR(20) | NOT NULL | 상태 (interested, participating, submitted, won, lost) |
| my_bid_price | DECIMAL(15,0) | | 투찰 금액 |
| is_winner | BOOLEAN | | 낙찰 여부 |
| submitted_at | TIMESTAMP | | 제출 시간 |
| result_at | TIMESTAMP | | 결과 확인 시간 |
| notes | TEXT | | 메모 |
| created_at | TIMESTAMP | NOT NULL | 생성 시간 |
| updated_at | TIMESTAMP | NOT NULL | 수정 시간 |

**Unique Constraint**: (user_id, bid_id)

**비고**: F-04에서는 이 테이블에 쓰기하지 않음. F-06 대시보드에서 활용 예정.

---

## 8. 서비스 설계

### 8.1 BiddingStrategyService -- 투찰 전략 서비스

**책임**: 낙찰가 분포 분석, 투찰가 추천, 시뮬레이션

```python
class BiddingStrategyService:
    """투찰 전략 분석 서비스"""

    # 적격심사 기본 구간 (예정가격 대비 비율)
    QUALIFICATION_RANGES = {
        "safe": (0.92, 0.95),
        "moderate": (0.89, 0.92),
        "aggressive": (0.86, 0.89),
    }

    # 최저가 통계 기반 시그마 계수
    LOWEST_PRICE_SIGMA = {
        "safe": (0.0, 0.5),       # mean ~ mean - 0.5*std
        "moderate": (0.5, 1.0),   # mean - 0.5*std ~ mean - 1.0*std
        "aggressive": (1.0, 2.0), # mean - 1.0*std ~ mean - 2.0*std
    }

    def __init__(self, db: Any):
        self.db = db

    async def analyze_strategy(self, bid_id: str) -> StrategyResult:
        """
        투찰 전략 분석

        1. 공고 정보 조회
        2. 유사 공고 낙찰 이력 조회
        3. 낙찰가율 분포 계산 (numpy)
        4. contract_method에 따른 추천 투찰가 범위 산출
        5. 전략 리포트 생성

        Returns: StrategyResult
        Raises:
            AppException: BID_001(404), STRATEGY_001(500)
        """

    async def simulate(
        self, bid_id: str, bid_price: int
    ) -> SimulationResult:
        """
        투찰가 시뮬레이션

        1. 공고 정보 조회 + 예정가격 확인
        2. bid_rate 계산 (bid_price / estimated_price)
        3. 유사 공고 bid_rate 분포에서 백분위 계산
        4. 낙찰 확률 추정
        5. 리스크 레벨 판정

        Returns: SimulationResult
        """

    def _calculate_distribution(
        self, bid_rates: list[float]
    ) -> dict:
        """
        numpy 기반 낙찰가율 분포 계산

        Returns: {mean, std, median, q25, q75, minRate, maxRate, sampleCount}
        """

    def _calculate_ranges_qualification(
        self,
        estimated_price: int,
        distribution: dict | None,
    ) -> dict:
        """
        적격심사 투찰가 추천 범위 계산

        - 유사 공고 데이터 있으면 실데이터 기반
        - 없으면 기본 구간 (88~95%) 사용
        """

    def _calculate_ranges_lowest_price(
        self,
        estimated_price: int,
        distribution: dict,
    ) -> dict:
        """
        최저가 투찰가 추천 범위 계산

        - 평균/표준편차 기반 시그마 구간
        """

    def _estimate_win_probability(
        self,
        bid_rate: float,
        distribution: dict,
        contract_method: str,
    ) -> int:
        """
        낙찰 확률 추정 (0~100%)

        적격심사: 정규분포 CDF 기반 (적정 구간 = 높은 확률)
        최저가: 백분위 기반 (낮을수록 유리)
        """

    def _determine_risk_level(
        self, bid_rate: float, ranges: dict
    ) -> tuple[str, str]:
        """
        리스크 레벨 판정

        Returns: (risk_level, risk_label)
        """

    def _generate_strategy_report(
        self,
        bid: Any,
        distribution: dict | None,
        ranges: dict,
    ) -> dict:
        """
        전략 리포트 생성

        - 계약 방식별 전략 설명
        - 시장 인사이트
        - 리스크 요인
        - 추천 사항
        """

    async def _get_similar_win_history(
        self, bid: Any
    ) -> list[dict]:
        """
        유사 공고 낙찰 이력 조회

        조건: 동일 category + contract_method, 최근 1년
        인메모리 store + DB 폴백
        """

    def _get_estimated_price(self, bid: Any) -> int | None:
        """
        예정가격 추출

        우선순위: estimated_price > budget
        둘 다 없으면 None
        """
```

---

## 9. 시퀀스 흐름

### 9.1 전략 분석 요청

```
사용자 -> Frontend -> GET /bids/{id}/strategy -> BidsAPI
    |
    v
BidsAPI
    | 1. JWT 인증 확인
    | 2. 공고 존재 확인
    |
    v
BiddingStrategyService.analyze_strategy(bid_id)
    | 3. 공고 정보 조회 (contract_method, estimated_price)
    | 4. 유사 공고 낙찰 이력 조회 (bid_win_history)
    | 5. numpy로 bid_rate 분포 계산
    | 6. contract_method별 추천 범위 산출
    |    |- 적격심사: 88~95% 기본 + 실데이터 보정
    |    |- 최저가: 평균/표준편차 기반 시그마 구간
    | 7. 각 구간별 낙찰 확률 추정
    | 8. 전략 리포트 생성
    |
    v
응답: StrategyResult (분포 + 추천범위 + 리포트)
```

### 9.2 시뮬레이션 요청

```
사용자 -> Frontend -> POST /bids/{id}/strategy/simulate
    |                  Body: { bidPrice: 410000000 }
    v
BidsAPI
    | 1. JWT 인증 확인
    | 2. 공고 존재 확인
    | 3. bidPrice 유효성 검사 (> 0)
    |
    v
BiddingStrategyService.simulate(bid_id, bid_price)
    | 4. estimated_price 추출
    | 5. bid_rate = bid_price / estimated_price
    | 6. 유사 공고 분포에서 백분위 계산
    | 7. 낙찰 확률 추정
    | 8. 리스크 레벨 판정
    | 9. 추천 범위 대비 비교 분석
    |
    v
응답: SimulationResult (확률 + 리스크 + 비교)
```

---

## 10. 영향 범위

### 10.1 수정 필요 파일

| 파일 | 변경 내용 |
|------|----------|
| backend/src/api/v1/bids.py | strategy, simulate 엔드포인트 추가 |

### 10.2 신규 생성 파일

| 파일 | 설명 |
|------|------|
| backend/src/schemas/strategy.py | 투찰 전략 관련 Pydantic 스키마 |
| backend/src/services/bidding_strategy_service.py | 투찰 전략 서비스 |

### 10.3 F-02 의존성

| 의존 대상 | 의존 내용 |
|----------|----------|
| bid_win_history 테이블/모델 | F-02에서 생성, F-04에서 읽기 전용 사용 |
| 샘플 시드 데이터 | F-02에서 정의한 SAMPLE_WIN_HISTORY 공유 |

---

## 11. 성능 설계

### 11.1 인덱스 계획

```sql
-- F-02에서 생성한 인덱스 활용
-- idx_bid_win_history_bid_number
-- idx_bid_win_history_winner
-- idx_bid_win_history_date

-- 추가 인덱스 불필요 (기존 인덱스로 충분)
```

### 11.2 캐싱 전략

```
# 전략 분석 결과 캐시 (인메모리 dict, 선택적)
strategy:{bid_id} -> StrategyResult (TTL 없음, 공고 갱신 시 무효화)

# 분포 데이터 캐시 (계산 비용 절감)
distribution:{category}:{contract_method} -> dict (서비스 수명 동안 유지)
```

### 11.3 numpy 연산 성능

- 대상 데이터: 유사 공고 100건 이내 (1년 필터)
- numpy 분포 계산: <10ms
- 전체 API 응답: <500ms

---

## 12. 에러 코드

### 신규 에러 코드

| 코드 | HTTP Status | 메시지 |
|------|-------------|--------|
| STRATEGY_001 | 500 | 투찰 전략 분석 중 오류가 발생했습니다. |
| STRATEGY_002 | 422 | 예정가격 정보가 없어 투찰가를 추천할 수 없습니다. |

### 기존 에러 코드 재사용

| 코드 | HTTP Status | 메시지 |
|------|-------------|--------|
| BID_001 | 404 | 공고를 찾을 수 없습니다. |
| AUTH_002 | 401 | 인증 토큰이 필요합니다. |
| VALIDATION_001 | 400 | 입력값이 유효하지 않습니다. |

---

## 13. 샘플 데이터 활용

F-02에서 정의한 SAMPLE_WIN_HISTORY를 공유 사용합니다. 추가 샘플 데이터:

```python
# F-02 SAMPLE_WIN_HISTORY에 추가
ADDITIONAL_WIN_HISTORY = [
    {
        "bid_number": "20260120001-00",
        "winner_name": "(주)차카타소프트",
        "winner_business_number": "1111111111",
        "winning_price": 460000000,
        "bid_rate": 0.9200,
        "winning_date": "2026-01-25",
        "_organization": "행정안전부",
        "_category": "정보화",
        "_bid_type": "일반경쟁",
        "_contract_method": "적격심사",
    },
    {
        "bid_number": "20260110001-00",
        "winner_name": "(주)파하소프트",
        "winner_business_number": "2222222222",
        "winning_price": 180000000,
        "bid_rate": 0.8500,
        "winning_date": "2026-01-15",
        "_organization": "조달청",
        "_category": "정보화",
        "_bid_type": "일반경쟁",
        "_contract_method": "최저가",
    },
]
```

---

## 14. 유사 공고 데이터 부족 시 폴백

유사 공고 낙찰 이력이 0건인 경우:

1. **낙찰가율 분포**: 계약 방식별 기본 통계 사용
   - 적격심사: mean=0.91, std=0.03, median=0.91
   - 최저가: mean=0.87, std=0.04, median=0.87
2. **추천 범위**: 기본 구간 사용 (5.3, 5.4 참조)
3. **전략 리포트**: "유사 공고 데이터가 부족하여 일반적인 통계 기반으로 추천합니다." 표기
4. **시뮬레이션**: 기본 분포 기반 확률 추정

---

## 변경 이력

| 날짜 | 변경 내용 | 이유 |
|------|----------|------|
| 2026-03-08 | 초기 변경 설계 | F-04 기능 구현 시작 |
