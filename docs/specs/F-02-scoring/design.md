# F-02 낙찰 가능성 스코어링 -- 변경 설계서

## 1. 참조
- 인수조건: docs/project/features.md #F-02
- 시스템 분석: docs/system/system-analysis.md
- ERD: docs/system/erd.md (user_bid_matches, bid_win_history, bids, companies, performances, certifications)
- API 컨벤션: docs/system/api-conventions.md
- F-01 설계: docs/specs/F-01-bid-collection/design.md (BidMatchService, user_bid_matches 테이블)

---

## 2. 변경 범위

- **변경 유형**: 기존 코드 수정 + 신규 추가
- **영향 받는 모듈**:
  - BidMatchService (competition_score, capability_score, market_score 채우기)
  - user_bid_matches 테이블 (recommendation 값 확장)
  - bids API 라우터 (scoring 엔드포인트 추가)
  - models/__init__.py (BidWinHistory 등록)
  - schemas/ (scoring 관련 스키마 추가)

---

## 3. 영향 분석

### 기존 API 변경

| API | 현재 | 변경 후 | 하위 호환성 |
|-----|------|---------|-------------|
| GET /api/v1/bids/{id}/matches | competition/capability/market_score 항상 0 | 실제 점수 채움 | O (필드 타입 동일) |

### 기존 DB 변경

| 테이블 | 변경 내용 | 마이그레이션 전략 |
|--------|----------|------------------|
| user_bid_matches | recommendation 값에 "strongly_recommended", "not_recommended_with_reason" 추가 (CHECK 제약 확장) | ALTER CHECK |
| bid_win_history | 신규 테이블 생성 | 신규 마이그레이션 |

### 사이드 이펙트
- F-01의 `analyze_match()` 결과가 더 정확해짐 (competition/capability/market 점수 반영)
- F-01의 `analyze_new_bids_for_all_users()` 내부에서 호출하는 `analyze_match()`도 자동 갱신
- 기존 매칭 결과(competition/capability/market=0)는 재분석 시 갱신됨

---

## 4. 아키텍처 결정

### 결정 1: 스코어링 모델 방식
- **선택지**: A) ML 모델 (학습 기반) / B) 가중치 기반 규칙 엔진 / C) 하이브리드
- **결정**: B) 가중치 기반 규칙 엔진
- **근거**:
  - MVP 수준에서 과도한 ML 불필요
  - 학습 데이터 부족 (초기 서비스)
  - 가중치 조정만으로 빠르게 개선 가능
  - 추후 ML 모델로 전환 시 서비스 인터페이스 유지

### 결정 2: 과거 낙찰 데이터 소스
- **선택지**: A) 실시간 크롤링 / B) DB 정적 데이터 + 샘플 / C) 외부 API
- **결정**: B) DB 정적 데이터 + 샘플
- **근거**:
  - bid_win_history 테이블에 과거 데이터 저장 (ERD 기정의)
  - 초기에는 샘플 시드 데이터로 대체
  - 향후 나라장터 낙찰결과 API 연동으로 실데이터 확보

### 결정 3: 경쟁 강도 산출 방식
- **선택지**: A) 같은 카테고리 공고 참여 업체 수 기반 / B) 유사 공고 낙찰 이력 분석
- **결정**: B) 유사 공고 낙찰 이력 분석
- **근거**:
  - 같은 organization + category + bid_type 조합의 과거 낙찰 건수로 경쟁 강도 추정
  - 참여 업체 수 데이터는 개찰 전까지 확보 불가

### 결정 4: recommendation 확장
- **선택지**: A) 기존 3단계 유지 / B) 4단계로 확장 (강력추천/추천/보류/비추천)
- **결정**: B) 4단계로 확장
- **근거**:
  - 인수조건 명시: "강력추천/추천/보류/비추천" 4단계
  - 기존 `recommended/neutral/not_recommended`에 `strongly_recommended` 추가

---

## 5. 스코어링 모델 설계

### 5.1 점수 구성 (가중치)

| 항목 | 가중치 | 산출 방식 | 범위 |
|------|--------|----------|------|
| 적합도 (suitability) | 30% | TF-IDF 코사인 유사도 (기존 F-01) | 0~100 |
| 경쟁 강도 (competition) | 25% | 유사 공고 낙찰 이력 기반 역점수 | 0~100 |
| 역량 (capability) | 30% | 회사 실적/인증/규모 기반 | 0~100 |
| 시장 환경 (market) | 15% | 예산 규모/계약 방식/시기 기반 | 0~100 |

**total_score = suitability * 0.30 + competition * 0.25 + capability * 0.30 + market * 0.15**

### 5.2 경쟁 강도 점수 (competition_score) 산출

```
1. 유사 공고 조건: 동일 organization OR category + 동일 bid_type
2. bid_win_history에서 해당 조건 낙찰 이력 조회
3. 경쟁 업체 수 추정 = 유사 공고의 고유 낙찰자(winner_business_number) 수
4. 경쟁 강도 raw = min(경쟁 업체 수 / 10, 1.0)  -- 10개사 이상이면 최대 경쟁
5. competition_score = (1.0 - 경쟁 강도 raw) * 100  -- 경쟁 낮을수록 점수 높음
6. 유사 공고 없으면 기본값 50 (중립)
```

### 5.3 역량 점수 (capability_score) 산출

```
1. 실적 점수 (40%):
   - 총 실적 건수 (max 10건 기준 정규화)
   - 유사 실적 존재 여부 (동일 발주기관 +20, 유사 분야 +10)
   - 대표 실적 보유 +10

2. 인증 점수 (30%):
   - 보유 인증 건수 (max 5건 기준 정규화)
   - 유효한 인증 (만료되지 않은) 비율

3. 규모 점수 (30%):
   - 회사 규모 (large: 100, medium: 70, small: 40)
   - 계약 금액 대비 회사 실적 규모 적합성
```

### 5.4 시장 환경 점수 (market_score) 산출

```
1. 예산 적합성 (50%):
   - 회사 평균 수행 금액 대비 공고 예산 비율
   - 0.5~2.0배 구간: 100점, 벗어나면 감점

2. 계약 방식 적합성 (30%):
   - 적격심사: 기본 70점 (역량 중요)
   - 최저가: 기본 50점 (가격만 중요)
   - 회사 과거 낙찰 방식과 일치하면 +30

3. 시기 점수 (20%):
   - 마감까지 남은 기간: 7일 이상 80점, 3~7일 60점, 3일 미만 40점
```

### 5.5 추천 등급 기준

| 등급 | 코드 | 점수 범위 | 설명 |
|------|------|----------|------|
| 강력추천 | strongly_recommended | 80~100 | 높은 낙찰 가능성, 적극 참여 권장 |
| 추천 | recommended | 60~79 | 참여 추천, 일부 보완 필요 |
| 보류 | neutral | 40~59 | 신중한 검토 필요 |
| 비추천 | not_recommended | 0~39 | 낮은 낙찰 가능성, 참여 비추천 |

---

## 6. API 설계

### 6.1 GET /api/v1/bids/{id}/scoring

낙찰 가능성 스코어링 결과 조회

- **목적**: 특정 공고에 대한 낙찰 가능성 상세 분석 결과 조회
- **인증**: 필요 (Bearer Token)
- **비즈니스 규칙**:
  - 사용자의 소속 회사 프로필이 등록되어 있어야 함
  - 스코어링 결과가 없으면 즉시 분석 실행 후 반환 (lazy evaluation)
  - 60초 이내 응답 (AC-01)
- **Response** (200 OK):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "bidId": "uuid",
    "userId": "uuid",
    "scores": {
      "suitability": 82.5,
      "competition": 65.0,
      "capability": 78.0,
      "market": 70.0,
      "total": 74.88
    },
    "weights": {
      "suitability": 0.30,
      "competition": 0.25,
      "capability": 0.30,
      "market": 0.15
    },
    "recommendation": "recommended",
    "recommendationLabel": "추천",
    "recommendationReason": "회사 역량과 공고 분야가 잘 일치하며, 경쟁 강도가 보통 수준입니다. 참여를 추천합니다.",
    "details": {
      "suitability": {
        "score": 82.5,
        "factors": [
          "업종 키워드 일치도: 높음",
          "유사 실적 보유: 3건"
        ]
      },
      "competition": {
        "score": 65.0,
        "factors": [
          "유사 공고 낙찰 이력: 8건",
          "추정 경쟁 업체 수: 5개사",
          "경쟁 강도: 보통"
        ]
      },
      "capability": {
        "score": 78.0,
        "factors": [
          "수행 실적: 7건 (양호)",
          "보유 인증: GS인증, ISO 9001",
          "회사 규모: 중견기업"
        ]
      },
      "market": {
        "score": 70.0,
        "factors": [
          "예산 적합성: 적정 (회사 평균 수행금액 대비 1.2배)",
          "계약 방식: 적격심사 (유리)",
          "마감 여유: 14일"
        ]
      }
    },
    "competitorStats": {
      "estimatedCompetitors": 5,
      "topCompetitors": [
        {"name": "(주)가나다소프트", "winCount": 3},
        {"name": "(주)라마바시스템", "winCount": 2}
      ]
    },
    "similarBidStats": {
      "totalCount": 12,
      "avgWinRate": 0.892,
      "avgWinningPrice": 420000000
    },
    "analyzedAt": "2026-03-08T06:05:00Z"
  }
}
```
- **에러 케이스**:
  | 코드 | HTTP Status | 상황 |
  |------|-------------|------|
  | BID_001 | 404 | 공고를 찾을 수 없음 |
  | COMPANY_001 | 404 | 소속 회사 없음 |
  | SCORING_001 | 500 | 스코어링 분석 중 오류 |
  | SCORING_002 | 504 | 스코어링 분석 시간 초과 (60초) |

---

## 7. DB 설계

### 7.1 신규 테이블: bid_win_history

ERD에 정의된 테이블 그대로 사용. 신규 모델 파일 생성.

| 컬럼 | 타입 | 제약조건 | 설명 |
|------|------|----------|------|
| id | UUID | PK, DEFAULT gen_random_uuid() | 이력 ID |
| bid_number | VARCHAR(50) | NOT NULL | 공고번호 |
| winner_name | VARCHAR(200) | NOT NULL | 낙찰자명 |
| winner_business_number | VARCHAR(10) | | 낙찰자 사업자번호 |
| winning_price | DECIMAL(15,0) | NOT NULL | 낙찰 금액 |
| bid_rate | DECIMAL(5,4) | | 낙찰율 (낙찰가/추정가) |
| winning_date | DATE | | 낙찰일 |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 생성 시간 |

**인덱스**:
```sql
CREATE INDEX idx_bid_win_history_bid_number ON bid_win_history(bid_number);
CREATE INDEX idx_bid_win_history_winner ON bid_win_history(winner_business_number);
CREATE INDEX idx_bid_win_history_date ON bid_win_history(winning_date);
```

### 7.2 user_bid_matches 변경

recommendation 컬럼의 CHECK 제약 확장:

```sql
-- 기존 CHECK 삭제 후 새로 생성
ALTER TABLE user_bid_matches
    DROP CONSTRAINT IF EXISTS chk_recommendation;

ALTER TABLE user_bid_matches
    ADD CONSTRAINT chk_recommendation
    CHECK (recommendation IS NULL OR recommendation IN (
        'strongly_recommended', 'recommended', 'neutral', 'not_recommended'
    ));
```

### 7.3 인메모리 store 확장

F-01 패턴과 동일하게, MVP 단계에서는 인메모리 store로 bid_win_history 샘플 데이터를 제공.

```python
# 인메모리 낙찰 이력 저장소
_BID_WIN_HISTORY: list[dict] = []

# 시드 데이터 (서비스 초기화 시 로드)
SAMPLE_WIN_HISTORY = [
    {
        "bid_number": "20260301001-00",
        "winner_name": "(주)가나다소프트",
        "winner_business_number": "1234567890",
        "winning_price": 420000000,
        "bid_rate": 0.8920,
        "winning_date": "2026-02-15",
        "organization": "행정안전부",
        "category": "정보화",
        "bid_type": "일반경쟁",
    },
    # ... 추가 샘플 데이터
]
```

---

## 8. 서비스 설계

### 8.1 ScoringService -- 낙찰 가능성 스코어링 서비스

**책임**: 4개 항목(적합도, 경쟁강도, 역량, 시장환경) 기반 종합 스코어링

```python
class ScoringService:
    """낙찰 가능성 스코어링 서비스"""

    # 가중치 설정
    WEIGHTS = {
        "suitability": 0.30,
        "competition": 0.25,
        "capability": 0.30,
        "market": 0.15,
    }

    # 추천 등급 기준
    RECOMMENDATION_THRESHOLDS = {
        "strongly_recommended": 80,
        "recommended": 60,
        "neutral": 40,
        # 40 미만: not_recommended
    }

    def __init__(self, db: Any):
        self.db = db
        self.bid_match_service: BidMatchService | None = None

    async def score(self, user_id: str, bid_id: str) -> ScoringResult:
        """
        종합 스코어링 실행

        1. 사용자 회사 + 공고 정보 조회
        2. 적합도 점수 (suitability) -- BidMatchService 위임
        3. 경쟁 강도 점수 (competition) -- bid_win_history 기반
        4. 역량 점수 (capability) -- 실적/인증/규모 기반
        5. 시장 환경 점수 (market) -- 예산/계약방식/시기 기반
        6. 가중합 총점 계산
        7. 추천 등급 결정
        8. user_bid_matches 갱신

        Returns: ScoringResult (전체 상세 분석 결과)
        Raises:
            AppException: COMPANY_001(404), BID_001(404), SCORING_001(500)
        """

    async def _calculate_suitability(
        self, user_id: str, bid_id: str
    ) -> tuple[float, list[str]]:
        """
        적합도 점수 산출 (TF-IDF 기반, BidMatchService 위임)

        Returns: (score, factors)
        """

    async def _calculate_competition(
        self, bid: Any
    ) -> tuple[float, list[str]]:
        """
        경쟁 강도 점수 산출

        1. 유사 공고 조건: organization + category + bid_type
        2. bid_win_history에서 낙찰 이력 조회
        3. 고유 낙찰자 수 -> 경쟁 업체 수 추정
        4. 경쟁 역점수 계산

        Returns: (score, factors)
        """

    async def _calculate_capability(
        self,
        company: Any,
        performances: list[Any],
        certifications: list[Any],
        bid: Any,
    ) -> tuple[float, list[str]]:
        """
        역량 점수 산출

        1. 실적 점수 (40%): 건수, 유사실적, 대표실적
        2. 인증 점수 (30%): 건수, 유효성
        3. 규모 점수 (30%): 기업 규모, 금액 적합성

        Returns: (score, factors)
        """

    async def _calculate_market(
        self,
        bid: Any,
        performances: list[Any],
    ) -> tuple[float, list[str]]:
        """
        시장 환경 점수 산출

        1. 예산 적합성: 회사 평균 수행금액 대비 비율
        2. 계약 방식 적합성
        3. 시기 점수: 마감까지 남은 기간

        Returns: (score, factors)
        """

    def _compute_total(self, scores: dict[str, float]) -> float:
        """가중합 총점 계산"""

    def _determine_recommendation(
        self, total_score: float, details: dict
    ) -> tuple[str, str, str]:
        """
        추천 등급 + 라벨 + 사유 결정

        Returns: (recommendation_code, label, reason)
        """

    async def _get_competitor_stats(
        self, bid: Any
    ) -> dict:
        """
        경쟁사 통계 조회

        유사 공고 낙찰 이력에서 주요 경쟁사 리스트 추출

        Returns: {estimatedCompetitors, topCompetitors}
        """

    async def _get_similar_bid_stats(
        self, bid: Any
    ) -> dict:
        """
        유사 공고 낙찰 통계

        유사 공고의 평균 낙찰율, 평균 낙찰가

        Returns: {totalCount, avgWinRate, avgWinningPrice}
        """

    async def _get_win_history(
        self,
        organization: str | None = None,
        category: str | None = None,
        bid_type: str | None = None,
    ) -> list[dict]:
        """
        bid_win_history 조회 (인메모리 + DB 폴백)

        조건에 맞는 낙찰 이력 반환
        """

    async def _update_match_scores(
        self,
        user_id: str,
        bid_id: str,
        scores: dict[str, float],
        recommendation: str,
        reason: str,
    ) -> None:
        """user_bid_matches 테이블 갱신"""
```

### 8.2 BidMatchService 변경

기존 `analyze_match()`에서 ScoringService를 호출하도록 옵션 추가:

```python
class BidMatchService:
    # 기존 코드 유지

    async def analyze_match(
        self, user_id, bid_id, *, full_scoring: bool = False
    ) -> Any:
        """
        full_scoring=True 시 ScoringService 연동하여 4개 항목 모두 채움
        full_scoring=False 시 기존 동작 (suitability만, F-01 호환)
        """
```

---

## 9. 시퀀스 흐름

### 9.1 스코어링 요청

```
사용자 -> Frontend -> GET /bids/{id}/scoring -> BidsAPI
    |
    v
BidsAPI
    | 1. JWT 인증 확인
    | 2. 회사 프로필 존재 확인
    | 3. 공고 존재 확인
    |
    v
ScoringService.score(user_id, bid_id)
    | 4. 적합도: BidMatchService._calculate_tfidf_similarity()
    | 5. 경쟁강도: bid_win_history 조회 -> 경쟁업체수 -> 역점수
    | 6. 역량: performances + certifications + company -> 가중합
    | 7. 시장환경: budget + contract_method + deadline -> 점수
    | 8. 가중합 total_score 계산
    | 9. 추천 등급 결정
    | 10. user_bid_matches 갱신
    | 11. 경쟁사 통계 조회
    | 12. 유사 공고 통계 조회
    |
    v
응답: ScoringResult (상세 분석 + 통계)
```

---

## 10. 영향 범위

### 10.1 수정 필요 파일

| 파일 | 변경 내용 |
|------|----------|
| backend/src/models/__init__.py | BidWinHistory 모델 import 추가 |
| backend/src/api/v1/bids.py | scoring 엔드포인트 추가, recommendation 값 확장 |
| backend/src/services/bid_match_service.py | full_scoring 옵션 추가, _score_to_recommendation 확장 |
| backend/src/schemas/bid_match.py | recommendation 값에 strongly_recommended 추가 |

### 10.2 신규 생성 파일

| 파일 | 설명 |
|------|------|
| backend/src/models/bid_win_history.py | BidWinHistory 모델 |
| backend/src/schemas/scoring.py | 스코어링 관련 Pydantic 스키마 |
| backend/src/services/scoring_service.py | 스코어링 서비스 |

---

## 11. 성능 설계

### 11.1 인덱스 계획

```sql
-- bid_win_history 검색 (ERD 기정의)
CREATE INDEX idx_bid_win_history_bid_number ON bid_win_history(bid_number);
CREATE INDEX idx_bid_win_history_winner ON bid_win_history(winner_business_number);
CREATE INDEX idx_bid_win_history_date ON bid_win_history(winning_date);

-- 유사 공고 조회 최적화 (bids 테이블, 기존 인덱스 활용)
-- idx_bids_organization, idx_bids_category 이미 존재
```

### 11.2 캐싱 전략

```
# 스코어링 결과 캐시 (인메모리 dict)
scoring:{user_id}:{bid_id} -> ScoringResult (TTL 없음, 재분석 시 갱신)

# bid_win_history 유사 공고 캐시 (인메모리 dict)
win_history:{org}:{category}:{bid_type} -> list[dict] (서비스 초기화 시 로드)
```

### 11.3 60초 타임아웃 보장

- TF-IDF 계산: <1초 (문서 2개, 벡터화 캐싱)
- bid_win_history 조회: <1초 (인덱스 활용, 인메모리 폴백)
- 역량/시장 계산: <1초 (단순 산술)
- 전체 스코어링: 예상 <3초 (충분한 여유)

---

## 12. 에러 코드

### 신규 에러 코드

| 코드 | HTTP Status | 메시지 |
|------|-------------|--------|
| SCORING_001 | 500 | 스코어링 분석 중 오류가 발생했습니다. |
| SCORING_002 | 504 | 스코어링 분석 시간이 초과되었습니다. |

### 기존 에러 코드 재사용

| 코드 | HTTP Status | 메시지 |
|------|-------------|--------|
| BID_001 | 404 | 공고를 찾을 수 없습니다. |
| COMPANY_001 | 404 | 회사를 찾을 수 없습니다. |
| AUTH_002 | 401 | 인증 토큰이 필요합니다. |

---

## 13. 샘플 시드 데이터

MVP에서 과거 낙찰 데이터가 없을 경우, 서비스 초기화 시 아래 샘플 데이터를 인메모리에 로드.

```python
SAMPLE_WIN_HISTORY = [
    {
        "bid_number": "20260201001-00",
        "winner_name": "(주)가나다소프트",
        "winner_business_number": "1234567890",
        "winning_price": 420000000,
        "bid_rate": 0.8920,
        "winning_date": "2026-02-15",
        # 연관 메타 (검색용, DB 미저장)
        "_organization": "행정안전부",
        "_category": "정보화",
        "_bid_type": "일반경쟁",
    },
    {
        "bid_number": "20260201002-00",
        "winner_name": "(주)라마바시스템",
        "winner_business_number": "9876543210",
        "winning_price": 380000000,
        "bid_rate": 0.8750,
        "winning_date": "2026-02-10",
        "_organization": "행정안전부",
        "_category": "정보화",
        "_bid_type": "일반경쟁",
    },
    {
        "bid_number": "20260115001-00",
        "winner_name": "(주)사아자테크",
        "winner_business_number": "5555555555",
        "winning_price": 250000000,
        "bid_rate": 0.9100,
        "winning_date": "2026-01-20",
        "_organization": "국토교통부",
        "_category": "건설",
        "_bid_type": "제한경쟁",
    },
]
```

---

## 변경 이력

| 날짜 | 변경 내용 | 이유 |
|------|----------|------|
| 2026-03-08 | 초기 변경 설계 | F-02 기능 구현 시작 |
