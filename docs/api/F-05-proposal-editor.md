# F-05 제안서 편집기 API 문서

## 개요

제안서 편집기 기능을 제공하는 API입니다. 섹션 자동 저장, 제안서 검증, 평가 체크리스트 관리 기능을 포함합니다.

## 기본 정보

- Base URL: `/api/v1/proposals`
- 인증: JWT 토큰 필수 (`Authorization: Bearer <token>`)
- 응답 포맷: `{"success": boolean, "data": object, "error": object}`

---

## API 목록

### 1. 섹션 자동 저장

제안서의 여러 섹션을 한 번에 자동 저장합니다.

**Endpoint:** `PATCH /{proposal_id}/auto-save`

**인증:** 필수

**요청:**

```json
{
  "sections": [
    {
      "sectionKey": "overview",
      "content": "<p>사업 개요 내용</p>"
    },
    {
      "sectionKey": "technical",
      "content": "<p>기술 제안 내용</p>"
    }
  ]
}
```

**요청 필드:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| sections | array | Y | 저장할 섹션 목록 |
| sections[].sectionKey | string | Y | 섹션 키 (`overview`, `technical`, `price`, `schedule`, `organization`, `past_performance`) |
| sections[].content | string | Y | HTML 콘텐츠 |
| sections[].wordCount | number | N | 단어 수 (API에서 자동 계산) |

**응답 (200 OK):**

```json
{
  "success": true,
  "data": {
    "savedAt": "2026-03-20T10:30:00Z",
    "wordCount": 1250
  }
}
```

**에러 응답:**

| 상태 코드 | 에러 코드 | 설명 |
|----------|-----------|------|
| 400 | PROPOSAL_004 | 섹션 배열이 비어 있습니다 |
| 400 | SECTION_002 | 유효하지 않은 섹션 키입니다 |
| 401 | AUTH_001 | 인증이 필요합니다 |
| 403 | PERMISSION_002 | 리소스 소유자가 아닙니다 |
| 404 | PROPOSAL_001 | 제안서를 찾을 수 없습니다 |

---

### 2. 제안서 검증

제안서를 제출하기 전에 필수 섹션, 페이지 제한, 평가 항목 달성률을 검증합니다.

**Endpoint:** `POST /{proposal_id}/validate`

**인증:** 필수

**요청:**

```json
{
  "pageLimit": 30
}
```

**요청 필드:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| pageLimit | number | N | 페이지 제한 (최대 페이지 수) |

**응답 (200 OK):**

```json
{
  "success": true,
  "data": {
    "isValid": true,
    "warnings": [],
    "stats": {
      "totalWordCount": 1250,
      "estimatedPages": 1,
      "sectionStats": [
        {
          "sectionKey": "overview",
          "wordCount": 500,
          "isEmpty": false
        },
        {
          "sectionKey": "technical",
          "wordCount": 750,
          "isEmpty": false
        }
      ]
    }
  }
}
```

**응답 필드:**

| 필드 | 타입 | 설명 |
|------|------|------|
| isValid | boolean | 검증 통과 여부 (필수 섹션, 페이지 제한 모두 통과 시 true) |
| warnings | array | 경고 목록 |
| warnings[].type | string | 경고 타입 (`required_field`, `page_limit`, `evaluation_incomplete`) |
| warnings[].section | string | 관련 섹션 키 |
| warnings[].message | string | 경고 메시지 |
| warnings[].current | number | 현재 값 |
| warnings[].limit | number | 제한 값 |
| stats | object | 통계 정보 |
| stats.totalWordCount | number | 총 단어 수 |
| stats.estimatedPages | number | 예상 페이지 수 (2000자당 1페이지) |
| stats.sectionStats | array | 섹션별 통계 |
| sectionStats[].sectionKey | string | 섹션 키 |
| sectionStats[].wordCount | number | 단어 수 |
| sectionStats[].isEmpty | boolean | 비어있는지 여부 |

**에러 응답:**

| 상태 코드 | 에러 코드 | 설명 |
|----------|-----------|------|
| 400 | PROPOSAL_005 | 페이지 제한은 0보다 커야 합니다 |
| 401 | AUTH_001 | 인증이 필요합니다 |
| 403 | PERMISSION_002 | 리소스 소유자가 아닙니다 |
| 404 | PROPOSAL_001 | 제안서를 찾을 수 없습니다 |

---

### 3. 평가 체크리스트 업데이트

평가 항목 체크리스트를 업데이트하고 달성률을 계산합니다.

**Endpoint:** `PATCH /{proposal_id}/evaluation-checklist`

**인증:** 필수

**요청:**

```json
{
  "checklist": {
    "technical_capability": {
      "checked": true,
      "weight": 30
    },
    "price_competitiveness": {
      "checked": true,
      "weight": 25
    },
    "past_performance": {
      "checked": false,
      "weight": 20
    },
    "project_schedule": {
      "checked": true,
      "weight": 15
    },
    "organization": {
      "checked": false,
      "weight": 10
    }
  }
}
```

**요청 필드:**

| 필드 | 타입 | 필수 | 설명 |
|------|------|------|------|
| checklist | object | Y | 체크리스트 (key-value 형태) |
| checklist.*.checked | boolean | Y | 체크 여부 |
| checklist.*.weight | number | Y | 가중치 (0-100) |

**응답 (200 OK):**

```json
{
  "success": true,
  "data": {
    "checklist": {
      "technical_capability": {
        "checked": true,
        "weight": 30
      },
      "price_competitiveness": {
        "checked": true,
        "weight": 25
      },
      "past_performance": {
        "checked": false,
        "weight": 20
      },
      "project_schedule": {
        "checked": true,
        "weight": 15
      },
      "organization": {
        "checked": false,
        "weight": 10
      }
    },
    "achievementRate": 70,
    "updatedAt": "2026-03-20T10:30:00Z"
  }
}
```

**응답 필드:**

| 필드 | 타입 | 설명 |
|------|------|------|
| checklist | object | 업데이트된 체크리스트 |
| achievementRate | number | 달성률 (0-100) |
| updatedAt | string | 업데이트 시각 (ISO 8601) |

**에러 응답:**

| 상태 코드 | 에러 코드 | 설명 |
|----------|-----------|------|
| 401 | AUTH_001 | 인증이 필요합니다 |
| 403 | PERMISSION_002 | 리소스 소유자가 아닙니다 |
| 404 | PROPOSAL_001 | 제안서를 찾을 수 없습니다 |

---

## 섹션 정의

| 섹션 키 | 섹션 명 | 필수 여부 | 설명 |
|---------|---------|-----------|------|
| overview | 사업 개요 | Y | 제안서 개요 |
| technical | 기술 제안 | Y | 기술적 제안 내용 |
| price | 가격 제안 | N | 가격 제안 내용 |
| schedule | 추진 일정 | N | 프로젝트 일정 |
| organization | 조직 구성 | N | 팀 조직 구성 |
| past_performance | 수행 실적 | N | 과거 수행 실적 |

---

## 워드 카운트 계산

- 한국어: 글자 수 기준 (공백 제외)
- 영어: 공백 기준 단어 수
- HTML 태그: 무시

예시:
- `"<p>안녕하세요 테스트입니다</p>"` → 11 (안녕하세요: 5 + 테스트입니다: 6)
- `"<p>Hello World</p>"` → 2 (Hello: 1 + World: 1)

---

## 페이지 수 계산

- 약 2000자당 1페이지로 계산
- 최소 1페이지

---

## 검증 규칙

### 필수 섹션 검증

- `overview`, `technical` 섹션이 비어있으면 검증 실패

### 페이지 제한 검증

- `pageLimit`이 제공되면 예상 페이지 수가 제한을 초과하는지 확인
- 예상 페이지 수 = `max(1, 총 단어 수 // 2000)`

### 평가 항목 달성률 검증

- 달성률이 50% 미만이면 경고 (검증 실패 아님)
- 달성률 = `(체크된 항목 가중치 합 / 전체 가중치) * 100`

---

## 메타데이터

섹션 저장 시 다음 메타데이터가 자동 업데이트됩니다:

```json
{
  "lastEditedBy": "user-uuid",
  "editCount": 5,
  "lastEditAt": "2026-03-20T10:30:00Z",
  "format": "html"
}
```

---

## 예시 시나리오

### 1. 섹션 자동 저장

```bash
curl -X PATCH \
  https://api.bidmaster.kr/api/v1/proposals/{proposal_id}/auto-save \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "sections": [
      {"sectionKey": "overview", "content": "<p>사업 개요</p>"}
    ]
  }'
```

### 2. 제안서 검증 (페이지 제한 30페이지)

```bash
curl -X POST \
  https://api.bidmaster.kr/api/v1/proposals/{proposal_id}/validate \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"pageLimit": 30}'
```

### 3. 평가 체크리스트 업데이트

```bash
curl -X PATCH \
  https://api.bidmaster.kr/api/v1/proposals/{proposal_id}/evaluation-checklist \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "checklist": {
      "technical_capability": {"checked": true, "weight": 30},
      "price_competitiveness": {"checked": true, "weight": 25}
    }
  }'
```
