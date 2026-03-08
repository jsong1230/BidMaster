# F-02 낙찰 가능성 스코어링 — API 스펙 확정본

> 구현 완료일: 2026-03-08
> 기준 브랜치: feature/F-02-scoring-dev

---

## 1. 엔드포인트 목록

| 메서드 | 경로 | 설명 | 인증 |
|--------|------|------|------|
| GET | `/api/v1/bids/{id}/scoring` | 낙찰 가능성 스코어링 조회 | Bearer JWT |

---

## 2. GET /api/v1/bids/{id}/scoring

### 개요

특정 공고에 대한 낙찰 가능성 상세 분석 결과를 반환합니다.
스코어링 결과가 없으면 즉시 분석 실행 후 반환합니다 (Lazy Evaluation).
동일 user_id + bid_id 조합은 인메모리 캐시를 통해 재요청 시 동일한 결과를 반환합니다.

### 요청

**Path Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| id | UUID | Y | 공고 ID |

**Headers**

| 헤더 | 값 | 필수 | 설명 |
|------|-----|------|------|
| Authorization | Bearer {JWT} | Y | 액세스 토큰 |

### 응답

**200 OK**

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "bidId": "550e8400-e29b-41d4-a716-446655440000",
    "userId": "user-owner-001",
    "scores": {
      "suitability": 60.0,
      "competition": 70.0,
      "capability": 48.0,
      "market": 78.0,
      "total": 62.7
    },
    "weights": {
      "suitability": 0.30,
      "competition": 0.25,
      "capability": 0.30,
      "market": 0.15
    },
    "recommendation": "recommended",
    "recommendationLabel": "추천",
    "recommendationReason": "회사 역량과 공고 분야가 잘 일치하며...",
    "details": {
      "suitability": {
        "score": 60.0,
        "factors": ["적합도 분석 기본값 적용 (60.0점)"]
      },
      "competition": {
        "score": 70.0,
        "factors": [
          "유사 공고 낙찰 이력: 2건",
          "추정 경쟁 업체 수: 3개사",
          "경쟁 강도: 낮음"
        ]
      },
      "capability": {
        "score": 48.0,
        "factors": [
          "수행 실적: 0건 (부족)",
          "보유 인증: 없음",
          "회사 규모: 중견기업"
        ]
      },
      "market": {
        "score": 78.0,
        "factors": [
          "예산 적합성: 기본값 적용 (수행 실적 없음)",
          "계약 방식: 적격심사 (유리)",
          "마감 여유: 14일 (충분)"
        ]
      }
    },
    "competitorStats": {
      "estimatedCompetitors": 3,
      "topCompetitors": [
        {"name": "(주)가나다소프트", "winCount": 1},
        {"name": "(주)라마바시스템", "winCount": 1}
      ]
    },
    "similarBidStats": {
      "totalCount": 2,
      "avgWinRate": 0.8835,
      "avgWinningPrice": 400000000.0
    },
    "analyzedAt": "2026-03-08T06:05:00Z"
  }
}
```

### 에러 코드

| 코드 | HTTP Status | 상황 |
|------|-------------|------|
| AUTH_002 | 401 | Authorization 헤더 없음 또는 유효하지 않은 토큰 |
| BID_001 | 404 | 공고를 찾을 수 없음 |
| COMPANY_001 | 404 | 소속 회사 없음 (JWT의 company_id가 없는 경우) |
| SCORING_001 | 500 | 스코어링 분석 중 오류 |
| VALIDATION_001 | 422 | bid_id가 UUID 형식이 아님 |

---

## 3. 스코어링 모델

### 3.1 가중치

| 항목 | 가중치 | 설명 |
|------|--------|------|
| 적합도 (suitability) | 30% | TF-IDF 코사인 유사도 기반 (BidMatchService 위임) |
| 경쟁 강도 (competition) | 25% | 유사 공고 낙찰 이력 기반 역점수 |
| 역량 (capability) | 30% | 실적(40%) + 인증(30%) + 기업규모(30%) |
| 시장 환경 (market) | 15% | 예산적합성(50%) + 계약방식(30%) + 시기(20%) |

**총점 = suitability×0.30 + competition×0.25 + capability×0.30 + market×0.15**

### 3.2 추천 등급

| 등급 | 코드 | 점수 범위 |
|------|------|----------|
| 강력추천 | strongly_recommended | 80~100 |
| 추천 | recommended | 60~79 |
| 보류 | neutral | 40~59 |
| 비추천 | not_recommended | 0~39 |

---

## 4. 기존 API 변경

### GET /api/v1/bids/{id}/matches (F-01 하위 호환)

- `recommendation` 필드의 유효 값에 `strongly_recommended` 추가
- 기존 3단계 (`recommended`, `neutral`, `not_recommended`)는 하위 호환 유지

---

## 5. 인메모리 캐시 전략

- 캐시 키: `{user_id}:{bid_id}`
- TTL: 없음 (서비스 재시작 시 초기화)
- 재분석: 캐시된 결과를 무효화하려면 서비스 재시작 필요
