# F-04 낙찰가 예측 및 투찰 전략 — API 스펙 확정본

## 기본 정보

- **버전**: v1
- **Base URL**: `/api/v1/bids`
- **인증**: Bearer Token (JWT)
- **Content-Type**: `application/json`

---

## 엔드포인트

### 1. GET /api/v1/bids/{id}/strategy

투찰 전략 분석 결과 조회

#### 요청

| 파라미터 | 위치 | 타입 | 필수 | 설명 |
|----------|------|------|------|------|
| id | path | string (UUID) | 필수 | 공고 ID |
| Authorization | header | string | 필수 | Bearer {token} |

#### 응답 (200 OK)

```json
{
  "success": true,
  "data": {
    "bidId": "550e8400-e29b-41d4-a716-446655440000",
    "bidTitle": "2026년 정보시스템 고도화 사업",
    "contractMethod": "적격심사",
    "estimatedPrice": 450000000,
    "budget": 500000000,
    "winRateDistribution": {
      "mean": 0.899,
      "std": 0.030,
      "median": 0.895,
      "q25": 0.880,
      "q75": 0.920,
      "minRate": 0.850,
      "maxRate": 0.950,
      "sampleCount": 10
    },
    "recommendedRanges": {
      "safe": {
        "label": "낮은 리스크 (안전)",
        "minPrice": 414000000,
        "maxPrice": 427500000,
        "minRate": 0.92,
        "maxRate": 0.95,
        "winProbability": 72,
        "description": "안전한 구간으로 낙찰 가능성이 높습니다."
      },
      "moderate": {
        "label": "중간 리스크 (적정)",
        "minPrice": 400500000,
        "maxPrice": 414000000,
        "minRate": 0.89,
        "maxRate": 0.92,
        "winProbability": 85,
        "description": "적정 구간으로 수익과 낙찰 가능성의 균형입니다."
      },
      "aggressive": {
        "label": "높은 리스크 (공격적)",
        "minPrice": 387000000,
        "maxPrice": 400500000,
        "minRate": 0.86,
        "maxRate": 0.89,
        "winProbability": 60,
        "description": "공격적 구간으로 수익은 높지만 낙찰 가능성이 낮습니다."
      }
    },
    "strategyReport": {
      "contractMethodStrategy": "적격심사 방식으로 기술력과 가격의 종합 평가가 이루어집니다...",
      "marketInsight": "유사 공고 10건 분석 결과 평균 낙찰가율 89.9%입니다.",
      "riskFactors": ["경쟁 업체 수 추정 (보통 수준)"],
      "recommendations": ["투찰가는 예정가격의 89~92% 구간을 권장합니다."]
    },
    "analyzedAt": "2026-03-08T10:00:00.000000+00:00"
  }
}
```

#### 에러 응답

| 코드 | HTTP Status | 상황 |
|------|-------------|------|
| BID_001 | 404 | 공고를 찾을 수 없음 |
| AUTH_002 | 401 | 인증 토큰 없음 |
| VALIDATION_001 | 422 | 유효하지 않은 공고 ID 형식 |
| STRATEGY_001 | 500 | 전략 분석 중 내부 오류 |

---

### 2. POST /api/v1/bids/{id}/strategy/simulate

투찰가 시뮬레이션

#### 요청

| 파라미터 | 위치 | 타입 | 필수 | 설명 |
|----------|------|------|------|------|
| id | path | string (UUID) | 필수 | 공고 ID |
| Authorization | header | string | 필수 | Bearer {token} |

#### 요청 본문

```json
{
  "bidPrice": 410000000
}
```

| 필드 | 타입 | 제약 | 설명 |
|------|------|------|------|
| bidPrice | integer | >= 0 | 투찰 금액 (원) |

#### 응답 (200 OK)

```json
{
  "success": true,
  "data": {
    "bidId": "550e8400-e29b-41d4-a716-446655440000",
    "inputPrice": 410000000,
    "bidRate": 0.9111,
    "winProbability": 68,
    "riskLevel": "safe",
    "riskLabel": "낮은 리스크",
    "analysis": "입력 금액은 예정가격의 91.1%로, 유사 공고 평균(89.9%) 대비 높은 수준입니다. 낙찰 가능성은 약 68%로 추정됩니다.",
    "comparisonWithRecommended": {
      "safe": "추천 범위 내",
      "moderate": "추천 범위 초과",
      "aggressive": "추천 범위 초과"
    }
  }
}
```

#### riskLevel 값 정의

| 값 | 설명 |
|----|------|
| safe | 낮은 리스크 구간 내 |
| moderate | 중간 리스크 구간 내 |
| aggressive | 높은 리스크 구간 내 |
| over_safe | 안전 구간 초과 (너무 높음) |
| extreme | 공격적 구간 미달 (너무 낮음) |

#### 에러 응답

| 코드 | HTTP Status | 상황 |
|------|-------------|------|
| BID_001 | 404 | 공고를 찾을 수 없음 |
| AUTH_002 | 401 | 인증 토큰 없음 |
| VALIDATION_001 | 400/422 | bidPrice 누락 또는 음수 |
| STRATEGY_001 | 500 | 시뮬레이션 중 내부 오류 |
| STRATEGY_002 | 422 | 예정가격 정보 없음 |

---

## 비즈니스 로직 상세

### 낙찰가율 분포 계산

유사 공고 조건:
- 동일 `category` + `contractMethod` 매칭
- 인메모리 SAMPLE_WIN_HISTORY에서 조회
- 데이터 없으면 계약 방식별 기본 분포 사용:
  - 적격심사: mean=0.91, std=0.03
  - 최저가: mean=0.87, std=0.04

### 추천 투찰가 범위

**적격심사 기본 구간:**

| 리스크 | 비율 구간 |
|--------|----------|
| safe | 92% ~ 95% |
| moderate | 89% ~ 92% |
| aggressive | 86% ~ 89% |

유사 공고 데이터 있으면 실데이터 기반으로 조정.

**최저가 시그마 구간:**

| 리스크 | 구간 |
|--------|------|
| safe | mean - 0.5σ ~ mean |
| moderate | mean - 1.0σ ~ mean - 0.5σ |
| aggressive | mean - 2.0σ ~ mean - 1.0σ |

### 낙찰 확률 추정

- **적격심사**: 정규분포 PDF 기반. mean 주변 = 높은 확률 (최대 85%). 너무 낮거나 높으면 최소 10%.
- **최저가**: 정규분포 CDF 기반. 낮을수록 유리 (win_prob = 1 - percentile).
- **분포 없음**: 50% 반환.

---

## 변경 이력

| 날짜 | 변경 내용 |
|------|----------|
| 2026-03-08 | F-04 구현 완료, API 스펙 확정 |
