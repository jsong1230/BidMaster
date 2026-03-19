# F-06 입찰 현황 대시보드 — API 스펙 확정본

> 구현 완료일: 2026-03-19
> 구현 방식: 인메모리 (MVP), DB 서비스 레이어 완비

---

## 공통

### 인증
모든 엔드포인트는 `Authorization: Bearer {token}` 헤더 필요

### 응답 형식
```json
{ "success": true, "data": {...}, "meta": {...} }
```

### 에러 형식
```json
{ "success": false, "error": { "code": "CODE", "message": "메시지" } }
```

---

## 1. GET /api/v1/dashboard/summary

대시보드 KPI 요약 조회

### Query Parameters

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| period | string | current_month | current_month, last_month, last_3_months, last_6_months, last_year |

### 응답 200

```json
{
  "success": true,
  "data": {
    "period": "2026-03",
    "participationCount": 12,
    "submissionCount": 8,
    "wonCount": 3,
    "lostCount": 4,
    "pendingCount": 1,
    "totalWonAmount": 1500000000,
    "winRate": 42.86,
    "averageWonAmount": 500000000.0,
    "roi": 0.0,
    "upcomingDeadlines": [
      {
        "bidId": "uuid",
        "title": "2026년 정보시스템 고도화 사업",
        "deadline": "2026-03-22T17:00:00+00:00",
        "daysLeft": 3,
        "trackingStatus": "participating"
      }
    ]
  }
}
```

### 에러

| 코드 | HTTP | 상황 |
|------|------|------|
| AUTH_002 | 401 | 인증 토큰 없음 |
| DASHBOARD_002 | 400 | 유효하지 않은 period |

---

## 2. GET /api/v1/dashboard/pipeline

파이프라인 단계별 현황 조회

### 응답 200

```json
{
  "success": true,
  "data": {
    "stages": [
      {
        "status": "interested",
        "label": "관심",
        "count": 5,
        "items": [
          {
            "trackingId": "uuid",
            "bidId": "uuid",
            "title": "AI 기반 행정 서비스 구축",
            "organization": "과학기술부",
            "budget": 200000000,
            "deadline": "2026-03-25T17:00:00+00:00",
            "daysLeft": 6,
            "totalScore": 78.5,
            "updatedAt": "2026-03-08T10:00:00+00:00"
          }
        ]
      },
      { "status": "participating", "label": "참여", "count": 3, "items": [] },
      { "status": "submitted", "label": "제출", "count": 2, "items": [] },
      { "status": "won", "label": "낙찰", "count": 1, "items": [] },
      { "status": "lost", "label": "실패", "count": 1, "items": [] }
    ]
  }
}
```

### 에러

| 코드 | HTTP | 상황 |
|------|------|------|
| AUTH_002 | 401 | 인증 토큰 없음 |

---

## 3. GET /api/v1/dashboard/statistics

성과 통계 (월별 트렌드) 조회

### Query Parameters

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| months | int | 6 | 최근 N개월 (1~12) |

### 응답 200

```json
{
  "success": true,
  "data": {
    "monthly": [
      {
        "month": "2026-03",
        "participationCount": 8,
        "submissionCount": 5,
        "wonCount": 2,
        "lostCount": 3,
        "winRate": 40.0,
        "totalWonAmount": 800000000,
        "averageBidRate": 0.8745
      }
    ],
    "cumulative": {
      "totalParticipation": 52,
      "totalSubmission": 35,
      "totalWon": 14,
      "totalLost": 18,
      "overallWinRate": 43.75,
      "totalWonAmount": 7500000000,
      "averageWonAmount": 535714285.0,
      "overallRoi": 0.0
    }
  }
}
```

### 에러

| 코드 | HTTP | 상황 |
|------|------|------|
| AUTH_002 | 401 | 인증 토큰 없음 |
| VALIDATION_001 | 400 | months가 1~12 범위 초과 |

---

## 4. POST /api/v1/bids/{bid_id}/tracking

입찰 추적 생성/업데이트 (Upsert)

### Request Body

```json
{
  "status": "participating",
  "myBidPrice": 450000000,
  "notes": "투찰가 확정"
}
```

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| status | string | O | interested, participating, submitted, won, lost |
| myBidPrice | int | X | 나의 투찰 금액 (0 이상) |
| notes | string | X | 메모 (최대 10000자) |

### 비즈니스 규칙
- 최초 요청: 201 Created + 신규 생성
- 이후 요청: 200 OK + 업데이트
- status=submitted: submitted_at 자동 설정
- status=won: is_winner=true, result_at 자동 설정
- status=lost: is_winner=false, result_at 자동 설정

### 응답 201 / 200

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "bidId": "uuid",
    "userId": "uuid",
    "status": "participating",
    "myBidPrice": 450000000,
    "isWinner": null,
    "submittedAt": null,
    "resultAt": null,
    "notes": "투찰가 확정",
    "createdAt": "2026-03-08T10:00:00+00:00",
    "updatedAt": "2026-03-08T10:00:00+00:00"
  }
}
```

### 에러

| 코드 | HTTP | 상황 |
|------|------|------|
| AUTH_002 | 401 | 인증 토큰 없음 |
| BID_001 | 404 | 공고 없음 |
| DASHBOARD_003 | 400 | 유효하지 않은 status |

---

## 5. GET /api/v1/bids/{bid_id}/tracking

입찰 추적 상태 조회

### 응답 200

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "bidId": "uuid",
    "userId": "uuid",
    "status": "participating",
    "myBidPrice": 450000000,
    "isWinner": null,
    "submittedAt": null,
    "resultAt": null,
    "notes": "메모",
    "createdAt": "2026-03-08T10:00:00+00:00",
    "updatedAt": "2026-03-08T10:00:00+00:00"
  }
}
```

### 에러

| 코드 | HTTP | 상황 |
|------|------|------|
| AUTH_002 | 401 | 인증 토큰 없음 |
| BID_001 | 404 | 공고 없음 |
| DASHBOARD_001 | 404 | 추적 정보 없음 |

---

## 6. GET /api/v1/bids/wins

낙찰 이력 조회

### Query Parameters

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| page | int | 1 | 페이지 번호 |
| pageSize | int | 20 | 페이지당 항목 수 (최대 100) |
| startDate | date | - | 시작일 (ISO 8601) |
| endDate | date | - | 종료일 (ISO 8601) |
| sortBy | string | resultAt | 정렬 기준: resultAt, myBidPrice |
| sortOrder | string | desc | 정렬 방향: asc, desc |

### 응답 200

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "bidId": "uuid",
        "userId": "uuid",
        "status": "won",
        "myBidPrice": 450000000,
        "isWinner": true,
        "submittedAt": "2026-03-20T15:00:00+00:00",
        "resultAt": "2026-03-25T10:00:00+00:00"
      }
    ]
  },
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 14,
    "totalPages": 1
  }
}
```

### 에러

| 코드 | HTTP | 상황 |
|------|------|------|
| AUTH_002 | 401 | 인증 토큰 없음 |

---

## 에러 코드 (F-06 신규)

| 코드 | HTTP | 메시지 |
|------|------|--------|
| DASHBOARD_001 | 404 | 추적 정보를 찾을 수 없습니다. |
| DASHBOARD_002 | 400 | 유효하지 않은 기간 값입니다. |
| DASHBOARD_003 | 400 | 유효하지 않은 추적 상태 값입니다. |
