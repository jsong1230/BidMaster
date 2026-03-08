# F-01 공고 자동 수집 및 매칭 API 스펙 확정본

## 개요

나라장터 공공 API로부터 공고를 수집하고, TF-IDF 기반 매칭 분석을 수행하는 API입니다.

**Base URL**: `/api/v1/bids`

---

## 공통 응답 포맷

```json
{
  "success": true,
  "data": { ... },
  "meta": { ... }
}
```

에러 응답:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "에러 메시지"
  }
}
```

---

## 에러 코드

| 코드 | HTTP | 설명 |
|------|------|------|
| AUTH_002 | 401 | 인증 토큰이 필요합니다 |
| BID_001 | 404 | 공고를 찾을 수 없습니다 |
| BID_004 | 409 | 공고 수집이 이미 진행 중입니다 |
| BID_005 | 502 | 공공데이터포털 API 연동 실패 |
| BID_006 | 500 | 매칭 분석 중 오류 |
| COMPANY_001 | 404 | 회사를 찾을 수 없습니다 (미소속 사용자) |
| PERMISSION_001 | 403 | 접근 권한이 없습니다 |
| VALIDATION_001 | 400 | 입력값 유효성 실패 |

---

## 엔드포인트

### 1. 공고 목록 조회

```
GET /api/v1/bids
```

**인증**: Bearer Token 필수

**쿼리 파라미터**:

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| page | int | 1 | 페이지 번호 |
| pageSize | int | 20 | 페이지 크기 (최대 100) |
| status | string | - | 필터: open/closed/awarded/cancelled |
| keyword | string | - | 제목/기관명 검색 |
| region | string | - | 지역 필터 |
| category | string | - | 카테고리 필터 |
| bidType | string | - | 입찰 유형 필터 |
| minBudget | int | - | 최소 예산 (원) |
| maxBudget | int | - | 최대 예산 (원) |
| startDate | string | - | 공고일 시작 (YYYY-MM-DD) |
| endDate | string | - | 공고일 종료 (YYYY-MM-DD) |
| sortBy | string | deadline | 정렬 기준: deadline/announcementDate/budget/createdAt |
| sortOrder | string | asc | 정렬 방향: asc/desc |

**성공 응답** (200):
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "bidNumber": "20260308001-00",
        "title": "2026년 정보시스템 고도화 사업",
        "organization": "행정안전부",
        "region": "서울",
        "category": "정보화",
        "bidType": "일반경쟁",
        "contractMethod": "적격심사",
        "budget": 500000000,
        "announcementDate": "2026-03-08",
        "deadline": "2026-03-22T17:00:00+00:00",
        "status": "open",
        "attachmentCount": 2,
        "crawledAt": "2026-03-08T06:00:00+00:00"
      }
    ]
  },
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 150,
    "totalPages": 8
  }
}
```

**에러 응답**:
- `401 AUTH_002`: 인증 토큰 없음
- `400 VALIDATION_001`: 잘못된 status 값

---

### 2. 매칭 공고 목록 조회

```
GET /api/v1/bids/matched
```

**인증**: Bearer Token 필수 (회사 소속 사용자만)

**쿼리 파라미터**:

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| page | int | 1 | 페이지 번호 |
| pageSize | int | 20 | 페이지 크기 (최대 100) |
| minScore | float | 0 | 최소 총점 필터 |
| recommendation | string | - | 필터: recommended/neutral/not_recommended |
| sortBy | string | totalScore | 정렬 기준 |
| sortOrder | string | desc | 정렬 방향 |

**성공 응답** (200):
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "match-uuid",
        "bid": {
          "id": "bid-uuid",
          "bidNumber": "20260308001-00",
          "title": "2026년 정보시스템 고도화 사업",
          "organization": "행정안전부",
          "budget": 500000000,
          "deadline": "2026-03-22T17:00:00+00:00",
          "status": "open"
        },
        "totalScore": 78.5,
        "recommendation": "recommended",
        "recommendationReason": "높은 적합도를 보입니다.",
        "analyzedAt": "2026-03-08T06:05:00+00:00"
      }
    ]
  },
  "meta": {
    "page": 1,
    "pageSize": 20,
    "total": 5,
    "totalPages": 1
  }
}
```

**에러 응답**:
- `401 AUTH_002`: 인증 토큰 없음
- `404 COMPANY_001`: 회사 미소속 사용자

---

### 3. 공고 상세 조회

```
GET /api/v1/bids/{bid_id}
```

**인증**: Bearer Token 필수

**경로 파라미터**:
- `bid_id` (UUID): 공고 ID

**성공 응답** (200):
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "bidNumber": "20260308001-00",
    "title": "2026년 정보시스템 고도화 사업",
    "description": "행정안전부 내부 정보시스템 고도화 사업",
    "organization": "행정안전부",
    "region": "서울",
    "category": "정보화",
    "bidType": "일반경쟁",
    "contractMethod": "적격심사",
    "budget": 500000000,
    "estimatedPrice": 450000000,
    "announcementDate": "2026-03-08",
    "deadline": "2026-03-22T17:00:00+00:00",
    "openDate": "2026-03-23T10:00:00+00:00",
    "status": "open",
    "scoringCriteria": { "technical": 80, "price": 20 },
    "attachments": [
      {
        "id": "att-uuid",
        "filename": "제안요청서.pdf",
        "fileType": "PDF",
        "fileUrl": "https://nara.go.kr/files/rfp.pdf",
        "hasExtractedText": true
      }
    ],
    "crawledAt": "2026-03-08T06:00:00+00:00",
    "createdAt": "2026-03-08T06:00:05+00:00"
  }
}
```

**에러 응답**:
- `401 AUTH_002`: 인증 토큰 없음
- `404 BID_001`: 공고 없음
- `422`: bid_id가 UUID 형식이 아님

---

### 4. 공고별 매칭 결과 조회 (Lazy Evaluation)

```
GET /api/v1/bids/{bid_id}/matches
```

**인증**: Bearer Token 필수 (회사 소속 사용자만)

매칭 결과가 없으면 즉시 분석하여 반환합니다 (Lazy Evaluation).

**경로 파라미터**:
- `bid_id` (UUID): 공고 ID

**성공 응답** (200):
```json
{
  "success": true,
  "data": {
    "id": "match-uuid",
    "bidId": "bid-uuid",
    "userId": "user-uuid",
    "suitabilityScore": 78.5,
    "competitionScore": 0,
    "capabilityScore": 0,
    "marketScore": 0,
    "totalScore": 78.5,
    "recommendation": "recommended",
    "recommendationReason": "높은 적합도를 보입니다.",
    "isNotified": true,
    "analyzedAt": "2026-03-08T06:05:00+00:00"
  }
}
```

**recommendation 값**:
- `recommended`: totalScore >= 70
- `neutral`: 40 <= totalScore < 70
- `not_recommended`: totalScore < 40

**에러 응답**:
- `401 AUTH_002`: 인증 토큰 없음
- `404 COMPANY_001`: 회사 미소속 사용자
- `404 BID_001`: 공고 없음

---

### 5. 수동 공고 수집 트리거

```
POST /api/v1/bids/collect
```

**인증**: Bearer Token 필수 (owner 역할만)

비동기로 공고 수집을 시작합니다. 응답은 즉시 반환됩니다.

**성공 응답** (202 Accepted):
```json
{
  "success": true,
  "data": {
    "message": "공고 수집이 시작되었습니다.",
    "triggeredAt": "2026-03-08T10:00:00+00:00"
  }
}
```

**에러 응답**:
- `401 AUTH_002`: 인증 토큰 없음
- `403 PERMISSION_001`: owner 역할 아님
- `409 BID_004`: 이미 수집 진행 중

---

## 자동 수집 스케줄

APScheduler를 사용하여 KST 기준으로 자동 수집이 실행됩니다.

| 설정 | 값 |
|------|-----|
| 스케줄 | 매일 06:00, 12:00, 18:00 KST |
| 타임아웃 | 10분 (Redis 잠금 TTL) |
| 동시 실행 방지 | Redis SETNX 잠금 |
| 수집 소스 | 나라장터 API (공공데이터포털) |

**수집 파이프라인**:
1. BidCollectorService: API 호출 → 중복 제거 → DB 저장
2. BidParserService: PDF/HWP 첨부파일 텍스트 추출
3. BidMatchService: TF-IDF 코사인 유사도 기반 매칭 분석

---

## 매칭 알고리즘

### TF-IDF 기반 유사도 계산

1. **회사 텍스트 구성**: 업종 + 설명 + 수행 실적 + 보유 인증
2. **공고 텍스트 구성**: 제목 + 설명 + 첨부파일 추출 텍스트
3. **코사인 유사도 계산**: scikit-learn TfidfVectorizer
4. **점수 보정**:
   - 발주기관이 수행 실적 발주처와 일치: +30점
   - TF-IDF 유사도 >= 0.20: +15점
5. **최종 점수**: 0~100점 범위로 정규화

### 추천 등급 기준

| 등급 | 점수 범위 |
|------|----------|
| recommended | 70점 이상 |
| neutral | 40점 이상 70점 미만 |
| not_recommended | 40점 미만 |
